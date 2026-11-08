"""Process groups owned by Daybreak, on Windows and POSIX."""

import os
import signal
import subprocess


def session_options() -> dict:
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def stop_tree(pid: int, *, force: bool = False) -> None:
    if os.name == "nt":
        # Limit termination to this child's tree; never kill by executable name.
        subprocess.run(["taskkill", "/PID", str(pid), "/T", *(["/F"] if force else [])],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(pid, signal.SIGKILL if force else signal.SIGTERM)
        except ProcessLookupError:
            pass
