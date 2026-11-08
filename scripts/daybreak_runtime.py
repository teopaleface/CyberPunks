#!/usr/bin/env python3
"""Prepare and run the private local workspace without touching existing servers."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from cyberpunks.common.processes import session_options, stop_tree

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "outputs" / "runtime"
ENV_FILE = RUNTIME / "daybreak.env"


def read_private_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    return dict(
        line.split("=", 1) for line in ENV_FILE.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.startswith("#")
    )


def environment() -> dict[str, str]:
    values = os.environ.copy()
    values.update(read_private_env())
    for name in ("channels.env", "meta-whatsapp.env"):
        path = RUNTIME / name
        if path.is_file():
            if path.stat().st_mode & 0o077:
                raise SystemExit(f"Private credentials must have mode 0600: {path.name}")
            for line in path.read_text(encoding="utf-8").splitlines():
                key, sep, value = line.partition("=")
                if sep and key.startswith(("ELEVENLABS_", "DAYBREAK_META_", "DAYBREAK_WHATSAPP_")):
                    values[key] = value.strip().strip("\"'")
    return values


def prepare(*, new_run: bool = False, named_accounts: bool = False) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)
    RUNTIME.chmod(0o700)
    values = read_private_env()
    if new_run and values:
        old_run = Path(values["DAYBREAK_OPERATIONS_OUTPUTS"]).parent
        old_run.mkdir(parents=True, exist_ok=True)
        backup = old_run / "private-runtime.env"
        if not backup.exists():
            shutil.copyfile(ENV_FILE, backup)
            backup.chmod(0o600)
        for role in ("CUSTOMER", "TECHNICIAN", "DISPATCHER"):
            for field in ("EMAIL", "PASSWORD"):
                values.pop(f"DAYBREAK_DEMO_{role}_{field}", None)
        values.pop("DAYBREAK_INTERNAL_TOKEN", None)
    if "DAYBREAK_OPERATIONS_OUTPUTS" not in values or new_run:
        stamp = datetime.now(ZoneInfo("Europe/Bucharest")).strftime("%Y%m%d-%H%M%S-%f")
        run_root = ROOT / "outputs" / "operations-runtime" / "runs" / stamp
        target = run_root / "data"
        target.mkdir(parents=True, mode=0o700)
        source_root = ROOT / "outputs"
        if not all((source_root / name).is_dir() for name in ("work_items", "series", "plans")):
            source_root = ROOT / "outputs/demo"
        manifest: dict[str, int] = {}
        for name in ("work_items", "series", "plans"):
            source = source_root / name
            if name == "work_items" and source_root.name == "demo":
                inputs = ROOT / "data/local-runtime/plans/demo-vara/inputs"
                if not inputs.is_dir():
                    raise SystemExit("Missing complete local runtime prediction bundle.")
                shutil.copytree(inputs, target / name / "demo-vara")
                manifest[name] = sum(p.is_file() for p in (target / name).rglob("*"))
                continue
            if not source.is_dir():
                raise SystemExit(f"Missing complete local source: {source}. Run `uv run cyberpunks run --scenario demo-vara` first.")
            shutil.copytree(source, target / name)
            manifest[name] = sum(p.is_file() for p in (target / name).rglob("*"))
        (run_root / "source.json").write_text(json.dumps({
            "copied_at": datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(),
            "source": "complete local outputs or bundled demo snapshot; public and synthetic technical data",
            "synthetic_accounts": True,
            "files": manifest,
            "inference": "not yet recomputed in isolated runtime",
        }, indent=2) + "\n")
        if source_root.name == "demo":
            from cyberpunks.planner.agent import run

            # The saved UI snapshot has no raw inputs. Replan from the complete
            # public/synthetic bundle, without model downloads or external writes.
            run("demo-vara", mode="existing", out_root=target, solver="greedy")
        values["DAYBREAK_OPERATIONS_OUTPUTS"] = str(target)
        values["DAYBREAK_OPERATIONS_DB"] = str(run_root / "operations.sqlite3")
    if named_accounts:
        emails = {"CUSTOMER": "client@daybreak.ro", "TECHNICIAN": "tehnician@daybreak.ro", "DISPATCHER": "dispecer@daybreak.ro"}
        if any(values.get(f"DAYBREAK_DEMO_{role}_EMAIL", email) != email for role, email in emails.items()):
            raise SystemExit("Existing account identities are preserved. Use the existing private credentials for this runtime.")
        if any(not values.get(f"DAYBREAK_DEMO_{role}_PASSWORD") for role in emails):
            password = getpass.getpass("Local synthetic demo password (at least 4 characters; never sent to GitHub): ")
            if len(password) < 4 or any(c in password for c in "\r\n"):
                raise SystemExit("Use at least four characters without line breaks.")
            for role in emails:
                values.setdefault(f"DAYBREAK_DEMO_{role}_PASSWORD", password)
        for role, email in emails.items():
            values.setdefault(f"DAYBREAK_DEMO_{role}_EMAIL", email)
    values.setdefault("DAYBREAK_INTERNAL_TOKEN", secrets.token_urlsafe(48))
    for role in ("CUSTOMER", "TECHNICIAN", "DISPATCHER"):
        values.setdefault(f"DAYBREAK_DEMO_{role}_PASSWORD", secrets.token_urlsafe(24))
        run_label = Path(values["DAYBREAK_OPERATIONS_OUTPUTS"]).parent.name
        values.setdefault(f"DAYBREAK_DEMO_{role}_EMAIL", f"demo-{role.lower()}+{run_label}@daybreak.local")
    values.update({
        "CYBERPUNKS_OUTPUT_ROOT": values["DAYBREAK_OPERATIONS_OUTPUTS"],
        "API_BASE": "http://127.0.0.1:8720/api",
        "DATA_SOURCE": "api",
        "DAYBREAK_DEMO_SETUP": "1",
        "DAYBREAK_ENABLE_DEMO_PROVISIONING": "1",
        "DAYBREAK_COOKIE_NAME": "daybreak_operations_session",
        "DAYBREAK_NEXT_DIST": ".next-operations",
        "DAYBREAK_API_PORT": "8720",
        "DAYBREAK_WEB_PORT": "3870",
        "PYTHONUNBUFFERED": "1",
        "PYTHONUTF8": "1",
    })
    for key, value in values.items():
        if "\n" in value or "\r" in value or not key.replace("_", "").isalnum():
            raise SystemExit("Invalid private runtime setting.")
    fd = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        out.write("# Private local runtime. Never commit or paste these values.\n")
        out.writelines(f"{key}={value}\n" for key, value in sorted(values.items()))
    ENV_FILE.chmod(0o600)
    print(f"Private runtime prepared. Data: {values['DAYBREAK_OPERATIONS_OUTPUTS']}")
    print("Credentials are stored privately in outputs/runtime/daybreak.env; values are not displayed.")


def infer(scenario: str) -> None:
    if not ENV_FILE.exists():
        prepare()
    code = (
        "import json; from cyberpunks.planner.agent import run; "
        "from cyberpunks.common.paths import OUTPUTS; "
        f"r=run({scenario!r},mode='auto',out_root=OUTPUTS); "
        "print(json.dumps({'plan_id':r.plan.plan_id,'summary':r.plan.summary.model_dump(),"
        "'sources':r.plan.sources_status,'timings':r.timings},default=str))"
    )
    subprocess.run(["uv", "run", "python", "-c", code], cwd=ROOT, env=environment(), check=True)


def check_ports(ports: tuple[int, ...]) -> None:
    for port in ports:
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(f"Port {port} is already in use. Existing processes have been left running.") from None


def start() -> None:
    if not ENV_FILE.exists():
        prepare()
    check_ports((8720, 3870))
    env = environment()
    # A clean clone has no generated public/landing directory. Build it before serving auth pages.
    subprocess.run(["bun", "run", "worker"], cwd=ROOT / "web", env=env, check=True)
    subprocess.run(["bun", "run", "landing"], cwd=ROOT / "web", env=env, check=True)
    specs = [
        (["uv", "run", "uvicorn", "cyberpunks.runtime:create_app", "--factory", "--host", "127.0.0.1", "--port", "8720"], ROOT),
        (["bun", "x", "next", "dev", "--hostname", "127.0.0.1", "--port", "3870"], ROOT / "web"),
    ]
    children: list[subprocess.Popen] = []

    def stop(_signum=None, _frame=None):
        for child in children:
            if child.poll() is None:
                try:
                    stop_tree(child.pid)
                except ProcessLookupError:
                    pass

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for command, cwd in specs:
            children.append(subprocess.Popen(command, cwd=cwd, env=env, **session_options()))
        print("Daybreak app with local accounts: http://127.0.0.1:3870/app", flush=True)
        print("Existing servers on 3710 and 8710 are unchanged.", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        failed = next((child.returncode for child in children if child.returncode not in (None, 0, -signal.SIGTERM)), None)
        if failed is not None:
            raise SystemExit(failed)
    finally:
        stop()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    stop_tree(child.pid, force=True)
                except ProcessLookupError:
                    pass
                child.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Create an isolated full-data runtime and private credentials")
    prep.add_argument("--new-run", action="store_true", help="Create another run without removing previous data")
    prep.add_argument("--named-accounts", action="store_true", help="Prepare the three named synthetic accounts; prompt privately for their local password")
    prediction = sub.add_parser("infer", help="Run the actual local ML models in the isolated data directory")
    prediction.add_argument("--scenario", default="demo-vara", choices=["demo-vara", "maine"])
    sub.add_parser("start", help="Start private API 8720 and web 3870; Ctrl-C stops only these children")
    sub.add_parser("accounts", help="Provision the three synthetic accounts on the running local workspace")
    sub.add_parser("check", help="Check configuration and output presence without printing credentials")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(new_run=args.new_run, named_accounts=args.named_accounts)
    elif args.command == "infer":
        infer(args.scenario)
    elif args.command == "start":
        start()
    elif args.command == "accounts":
        subprocess.run(["bun", "run", "scripts/provision-demo.ts"], cwd=ROOT / "web", env=environment(), check=True)
    else:
        env = read_private_env()
        root = Path(env.get("DAYBREAK_OPERATIONS_OUTPUTS", "__not_prepared__"))
        print(json.dumps({"prepared": bool(env), "private_credentials_mode": oct(ENV_FILE.stat().st_mode & 0o777) if env else None,
                          "data_exists": root.is_dir(), "plan_exists": (root / "plans/demo-vara/plan.json").is_file(),
                          "internal_auth_configured": bool(env.get("DAYBREAK_INTERNAL_TOKEN"))}))


if __name__ == "__main__":
    main()
