#!/usr/bin/env python3
"""Connect only the authorized Meta test app. Never print credentials or send test messages."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import signal
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "outputs/runtime"
CONFIG = RUNTIME / "meta-whatsapp.env"
RECORD = RUNTIME / "whatsapp-webhook.json"
APP_ID = "1126383816984070"
PHONE_ID = "1397343823467724"
WABA_ID = "1542900177687148"
WEBHOOK_PATH = "/api/conversation/whatsapp/webhook"


def private_env(path: Path) -> dict[str, str]:
    if not path.is_file() or path.stat().st_mode & 0o077:
        raise SystemExit(f"A private mode-0600 file is required: {path.name}")
    return dict(
        line.split("=", 1) for line in path.read_text().splitlines() if "=" in line and not line.startswith("#")
    )


def save(config: dict[str, str]) -> None:
    temporary = CONFIG.with_suffix(".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.writelines(f"{key}={value}\n" for key, value in sorted(config.items()))
    temporary.chmod(0o600)
    temporary.replace(CONFIG)


def ready(config: dict[str, str]) -> None:
    required = ("DAYBREAK_META_ACCESS_TOKEN", "DAYBREAK_META_APP_SECRET")
    if any(not config.get(key) for key in required):
        raise SystemExit("Meta setup is incomplete. Finish the private App Secret confirmation in Helium.")
    if (
        config.get("DAYBREAK_META_PHONE_NUMBER_ID") != PHONE_ID
        or config.get("DAYBREAK_META_MESSAGING_ACCOUNT_ID") != WABA_ID
    ):
        raise SystemExit("The configured number or account differs from the authorized Meta test app.")
    if not re.fullmatch(r"v\d+\.\d+", config.get("DAYBREAK_META_GRAPH_VERSION", "")):
        raise SystemExit("The configured Meta Graph version is invalid.")


def graph(client: httpx.Client, method: str, path: str, token: str, **kwargs) -> dict:
    response = client.request(method, path, headers={"Authorization": f"Bearer {token}"}, **kwargs)
    try:
        result = response.json()
    except ValueError:
        raise SystemExit(
            f"Meta returned an invalid response with HTTP {response.status_code}; no retry was made."
        ) from None
    if response.is_error or "error" in result:
        error = result.get("error", {})
        raise SystemExit(
            f"Meta rejected {method}: HTTP {response.status_code}, code {error.get('code')}, "
            f"subcode {error.get('error_subcode')}. No automatic retry was made."
        )
    return result


def connect(callback: str) -> None:
    url = urlparse(callback)
    if not (
        url.scheme == "https"
        and url.hostname
        and url.hostname.endswith(".trycloudflare.com")
        and url.path == WEBHOOK_PATH
        and url.port in (None, 443)
        and not any((url.username, url.password, url.query, url.fragment))
    ):
        raise SystemExit("Use the temporary HTTPS tunnel and the exact Meta webhook path.")
    config = private_env(CONFIG)
    ready(config)
    user_token = config["DAYBREAK_META_ACCESS_TOKEN"]
    app_token = APP_ID + "|" + config["DAYBREAK_META_APP_SECRET"]
    base = "https://graph.facebook.com/" + config["DAYBREAK_META_GRAPH_VERSION"] + "/"
    with httpx.Client(base_url=base, timeout=30, follow_redirects=False) as client:
        app = graph(client, "GET", APP_ID, user_token, params={"fields": "id,name"})
        if app.get("id") != APP_ID or app.get("name") != "Daybreak CyberPunks":
            raise SystemExit("Meta app identity did not match; stopped before configuration changes.")
        subscriptions = graph(client, "GET", APP_ID + "/subscriptions", app_token).get("data", [])
        current = next((s for s in subscriptions if s.get("object") == "whatsapp_business_account"), None)
        previous = json.loads(RECORD.read_text()) if RECORD.is_file() else {}
        if current and current.get("callback_url") not in (callback, previous.get("callback_url")):
            raise SystemExit("This app already has another callback. It was preserved; review it before changing it.")
        fields = {"messages"}
        if current:
            fields.update(f["name"] for f in current.get("fields", []) if isinstance(f, dict) and f.get("name"))
        config.setdefault("DAYBREAK_META_VERIFY_TOKEN", secrets.token_urlsafe(32))
        config["DAYBREAK_WHATSAPP_ENABLED"] = "1"
        config["DAYBREAK_WHATSAPP_SEND_ENABLED"] = "0"
        save(config)
        result = graph(
            client,
            "POST",
            APP_ID + "/subscriptions",
            app_token,
            data={
                "object": "whatsapp_business_account",
                "callback_url": callback,
                "verify_token": config["DAYBREAK_META_VERIFY_TOKEN"],
                "fields": ",".join(sorted(fields)),
            },
        )
        if result.get("success") is not True:
            raise SystemExit("Meta did not confirm the callback. Sending remains disabled; inspect before retrying.")
        graph(client, "POST", WABA_ID + "/subscribed_apps", user_token)
        persisted = graph(client, "GET", APP_ID + "/subscriptions", app_token).get("data", [])
        subscription = next((s for s in persisted if s.get("object") == "whatsapp_business_account"), {})
        accounts = graph(client, "GET", WABA_ID + "/subscribed_apps", user_token).get("data", [])
        ids = {a.get("whatsapp_business_api_data", {}).get("id", a.get("id")) for a in accounts}
        persisted_fields = {f.get("name") for f in subscription.get("fields", []) if isinstance(f, dict)}
        if (
            subscription.get("callback_url") != callback
            or not subscription.get("active")
            or not fields.issubset(persisted_fields)
            or APP_ID not in ids
        ):
            raise SystemExit("Persisted Meta verification is incomplete. Sending remains disabled.")
        config["DAYBREAK_WHATSAPP_SEND_ENABLED"] = "1"
        save(config)
        RECORD.write_text(
            json.dumps({"app_id": APP_ID, "callback_url": callback, "verified_at": time.time()}, indent=2) + "\n"
        )
        RECORD.chmod(0o600)
    print("Meta callback and account subscription verified. Replies are enabled only for verified inbound senders.")


def serve() -> None:
    # Start before connect so Meta can perform its challenge. Sending remains gated in the private configuration.
    from daybreak_runtime import check_ports

    check_ports((8721,))
    env = os.environ.copy()
    env["DAYBREAK_CHANNELS_RUNTIME"] = str(RUNTIME)
    paths = private_env(RUNTIME / "daybreak.env")
    for key in ("CYBERPUNKS_OUTPUT_ROOT", "DAYBREAK_OPERATIONS_OUTPUTS", "DAYBREAK_OPERATIONS_DB"):
        env[key] = paths[key]
    commands = [
        [
            "uv",
            "run",
            "uvicorn",
            "cyberpunks.webhook_runtime:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            "8721",
            "--no-access-log",
        ],
        ["uv", "run", "python", "scripts/daybreak_channels.py", "whatsapp-worker"],
    ]
    children = []

    def stop(*_args):
        for child in children:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        for command in commands:
            children.append(subprocess.Popen(command, cwd=ROOT, env=env, start_new_session=True))
        print("Meta-only ingress on 127.0.0.1:8721 and one durable reply worker started.", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
    finally:
        stop()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("serve")
    connect_parser = sub.add_parser("connect")
    connect_parser.add_argument("--callback", required=True)
    args = parser.parse_args()
    if args.command == "serve":
        serve()
    elif args.command == "connect":
        connect(args.callback)
    else:
        config = private_env(CONFIG)
        print(
            json.dumps(
                {
                    "access_token_present": bool(config.get("DAYBREAK_META_ACCESS_TOKEN")),
                    "app_secret_present": bool(config.get("DAYBREAK_META_APP_SECRET")),
                    "number_matches": config.get("DAYBREAK_META_PHONE_NUMBER_ID") == PHONE_ID,
                    "sending_enabled": config.get("DAYBREAK_WHATSAPP_SEND_ENABLED") == "1",
                    "callback_verified": RECORD.is_file(),
                }
            )
        )


if __name__ == "__main__":
    main()
