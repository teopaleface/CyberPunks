"""Fresh-laptop setup uses complete model outputs and keeps private credentials local."""
import importlib.util
import os
from pathlib import Path

import pytest


@pytest.fixture
def setup_module(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[2] / "scripts/daybreak_runtime.py"
    spec = importlib.util.spec_from_file_location("local_runtime_setup", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "RUNTIME", tmp_path / "outputs/runtime")
    monkeypatch.setattr(module, "ENV_FILE", tmp_path / "outputs/runtime/daybreak.env")
    for name in ("work_items", "series", "plans"):
        folder = tmp_path / "outputs" / name
        folder.mkdir(parents=True)
        (folder / "synthetic-test-input.json").write_text('{"synthetic": true}')
    return module


def test_clean_clone_copies_each_output_directory_and_reuses_runtime(setup_module):
    m = setup_module
    m.prepare()
    initial = m.read_private_env()
    data = Path(initial["DAYBREAK_OPERATIONS_OUTPUTS"])
    for name in ("work_items", "series", "plans"):
        assert (data / name / "synthetic-test-input.json").read_text() == '{"synthetic": true}'
    if os.name != "nt":
        assert m.ENV_FILE.stat().st_mode & 0o777 == 0o600
    m.prepare()
    assert m.read_private_env() == initial


def test_named_local_accounts_prompt_privately_without_printing_password(setup_module, monkeypatch, capsys):
    m = setup_module
    password = "synthetic-test-password"
    monkeypatch.setattr(m.getpass, "getpass", lambda _: password)
    m.prepare(named_accounts=True)
    values = m.read_private_env()
    assert values["DAYBREAK_DEMO_CUSTOMER_EMAIL"] == "client@daybreak.ro"
    assert values["DAYBREAK_DEMO_TECHNICIAN_EMAIL"] == "tehnician@daybreak.ro"
    assert values["DAYBREAK_DEMO_DISPATCHER_EMAIL"] == "dispecer@daybreak.ro"
    assert all(values[f"DAYBREAK_DEMO_{r}_PASSWORD"] == password for r in ("CUSTOMER", "TECHNICIAN", "DISPATCHER"))
    assert password not in capsys.readouterr().out
    monkeypatch.setattr(m.getpass, "getpass", lambda _: pytest.fail("Existing passwords must not be prompted again"))
    m.prepare(named_accounts=True)
    assert m.read_private_env() == values


def test_missing_output_is_rejected_before_private_config_is_written(setup_module):
    m = setup_module
    import shutil
    shutil.rmtree(m.ROOT / "outputs/series")
    with pytest.raises(SystemExit, match="Missing complete local source"):
        m.prepare()
    assert not m.ENV_FILE.exists()
