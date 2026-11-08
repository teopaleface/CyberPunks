"""Exercise a prepared local runtime on a clean CI checkout, without external channels."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from cyberpunks.common.processes import session_options, stop_tree

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    # Never run against an active developer runtime or inherited external-service configuration.
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("This smoke check is for a clean GitHub Actions checkout only.")
    from daybreak_runtime import check_ports

    check_ports((8720, 3870))
    with tempfile.TemporaryFile(mode="w+b") as log:
        child = subprocess.Popen(
            [sys.executable, "scripts/daybreak_runtime.py", "start"],
            cwd=ROOT, stdout=log, stderr=log, **session_options(),
        )
        try:
            pending = {"http://127.0.0.1:8720/healthz", "http://127.0.0.1:3870/intra"}
            deadline = time.monotonic() + 180
            while pending and time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError("The local startup command exited before both services were ready.")
                for url in list(pending):
                    try:
                        with urlopen(url, timeout=10) as response:
                            body = response.read()
                            if response.status == 200 and body:
                                pending.remove(url)
                    except (URLError, TimeoutError):
                        pass
                time.sleep(1)
            if pending:
                raise RuntimeError("The local API or sign-in page did not become ready.")
            try:
                urlopen("http://127.0.0.1:8720/api/health", timeout=10)
            except HTTPError as exc:
                assert exc.code == 401, "The private API must reject unauthenticated requests."
            else:
                raise AssertionError("The private API accepted an unauthenticated request.")
            subprocess.run([sys.executable, "scripts/daybreak_runtime.py", "accounts"], cwd=ROOT, check=True)
            print("Local API, sign-in page, authentication boundary and synthetic account provisioning passed.")
        except Exception:
            # This job has only synthetic local credentials; never print private environment files.
            log.seek(0)
            print(log.read().decode("utf-8", errors="replace")[-12000:], file=sys.stderr)
            raise
        finally:
            if child.poll() is None:
                stop_tree(child.pid, force=True)
                child.wait(timeout=20)


if __name__ == "__main__":
    main()
