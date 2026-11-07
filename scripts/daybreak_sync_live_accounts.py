"""Copy live account records to local KV, without sessions or remote writes."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "outputs/runtime"


def cli(*args: str, optional: bool = False) -> str | None:
    result = subprocess.run(
        ["bun", "x", "wrangler", "kv", *args, "--binding", "CONTURI"],
        cwd=ROOT / "web",
        capture_output=True,
        text=True,
        input="y\n",
        check=False,
    )
    if result.returncode:
        if optional and "not found" in (result.stderr + result.stdout).lower():
            return None
        raise SystemExit("Cloudflare KV command failed; private output was suppressed.")
    return result.stdout


def main() -> None:
    records = []
    keys = json.loads(cli("key", "list", "--remote", "--prefix", "u:") or "[]")
    for entry in keys:
        key = entry["name"]
        if not re.fullmatch(r"u:[0-9a-f-]{36}", key):
            continue
        raw = (cli("key", "get", key, "--remote", "--text") or "").rstrip("\r\n")
        user = json.loads(raw or "{}")
        if key != "u:" + user.get("id", "") or not all(user.get(k) for k in ("email", "salt", "hash", "iter")):
            raise SystemExit("Invalid live account record; local storage was not changed.")
        email_key = "u:email:" + user["email"].strip().lower()
        live_id = cli("key", "get", email_key, "--remote", "--text")
        if (live_id or "").strip() != user["id"]:
            raise SystemExit("Live account index mismatch; local storage was not changed.")
        records += [{"key": key, "value": raw}, {"key": email_key, "value": user["id"]}]
    if not records:
        raise SystemExit("No live accounts found; local accounts were preserved.")
    backup = []
    local_keys = {x["name"] for x in json.loads(cli("key", "list", "--local", "--prefix", "u:") or "[]")}
    for record in records:
        if record["key"] in local_keys:
            prior = cli("key", "get", record["key"], "--local", "--text")
            if record["key"].startswith("u:email:") and (prior or "").strip() != record["value"]:
                raise SystemExit("A different local account uses this email; preserved it without overwriting.")
            backup.append({"key": record["key"], "value": prior})
    PRIVATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    def private_file(path, data):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)

    private_file(PRIVATE / f"account-sync-backup-{stamp}.json", backup)
    payload = PRIVATE / f"account-sync-import-{stamp}.json"
    private_file(payload, records)
    try:
        cli("bulk", "put", str(payload), "--local")
        for record in records:
            actual = cli("key", "get", record["key"], "--local", "--text")
            if (actual or "").rstrip("\r\n") != record["value"]:
                raise SystemExit("Local verification failed; private backup preserved.")
    finally:
        payload.unlink(missing_ok=True)
    users = [json.loads(r["value"]) for r in records if not r["key"].startswith("u:email:")]
    print(
        json.dumps(
            {
                "accounts_copied_and_verified": len(users),
                "remote_writes": False,
                "sessions_copied": False,
                "memberships_preserved": True,
            }
        )
    )


if __name__ == "__main__":
    main()
