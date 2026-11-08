"""Native process cleanup and complete-snapshot preparation, without external services."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import portalocker

from cyberpunks.common.paths import ROOT
from cyberpunks.common.processes import session_options, stop_tree


def test_lock_excludes_another_process_and_releases(tmp_path):
    path = tmp_path / "planner.lock"
    code = """
import sys, portalocker
with open(sys.argv[1], 'a') as handle:
    try:
        portalocker.lock(handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
    except portalocker.exceptions.LockException:
        sys.exit(7)
    portalocker.unlock(handle)
"""
    with path.open("a") as handle:
        portalocker.lock(handle, portalocker.LOCK_EX)
        result = subprocess.run([sys.executable, "-c", code, str(path)], timeout=20, check=False)
        assert result.returncode == 7
        portalocker.unlock(handle)
    assert subprocess.run([sys.executable, "-c", code, str(path)], timeout=20, check=False).returncode == 0


def test_owned_process_can_be_stopped():
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], **session_options())
    try:
        stop_tree(proc.pid, force=True)
        proc.wait(timeout=15)
        assert proc.returncode is not None
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_clean_checkout_prepares_complete_bundled_snapshot(tmp_path, monkeypatch):
    import shutil

    spec = importlib.util.spec_from_file_location("daybreak_runtime", ROOT / "scripts/daybreak_runtime.py")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    # Use the complete tracked snapshot, with no private config or source runtime copied.
    shutil.copytree(ROOT / "outputs/demo", tmp_path / "outputs/demo")
    shutil.copytree(ROOT / "data/local-runtime", tmp_path / "data/local-runtime")
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    monkeypatch.setattr(runtime, "RUNTIME", tmp_path / "outputs/runtime")
    monkeypatch.setattr(runtime, "ENV_FILE", tmp_path / "outputs/runtime/daybreak.env")
    runtime.prepare()
    env = runtime.read_private_env()
    data = Path(env["DAYBREAK_OPERATIONS_OUTPUTS"])
    for inputs in (tmp_path / "data/local-runtime/plans").glob("*/inputs/*.jsonl"):
        assert (data / "work_items" / inputs.parent.parent.name / inputs.name).read_bytes() == inputs.read_bytes()
    assert (data / "plans/demo-vara/plan.json").is_file()
    assert env["PYTHONUTF8"] == "1"
    assert ZoneInfo("Europe/Bucharest")
