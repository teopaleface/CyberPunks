"""The smoke check lets the launcher clean up its separate service sessions."""

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from cyberpunks.common.processes import session_options, stop_tree


@pytest.mark.skipif(os.name == "nt", reason="POSIX service sessions and SIGTERM handler")
def test_smoke_cleanup_stops_detached_service(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/check_local_start.py"
    spec = importlib.util.spec_from_file_location("local_start_check", script)
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    ready = tmp_path / "ready"
    stopped = tmp_path / "stopped"
    code = '''
import os, signal, subprocess, sys, time
from pathlib import Path
service = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'], start_new_session=True)
def stop(*_):
    os.killpg(service.pid, signal.SIGTERM)
    service.wait(timeout=5)
    Path(sys.argv[2]).write_text('stopped')
    sys.exit(0)
signal.signal(signal.SIGTERM, stop)
Path(sys.argv[1]).write_text(str(service.pid))
while True:
    time.sleep(0.1)
'''
    launcher = subprocess.Popen([sys.executable, "-c", code, str(ready), str(stopped)], **session_options())
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            assert launcher.poll() is None
            time.sleep(0.05)
        assert ready.exists()
        check.stop_runtime(launcher)
        assert launcher.returncode == 0
        assert stopped.read_text() == "stopped"
        with pytest.raises(ProcessLookupError):
            os.kill(int(ready.read_text()), 0)
    finally:
        if launcher.poll() is None:
            stop_tree(launcher.pid, force=True)
            launcher.wait(timeout=5)
        if ready.exists():
            stop_tree(int(ready.read_text()), force=True)
