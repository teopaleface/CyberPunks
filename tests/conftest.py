import os
import shutil
from pathlib import Path

import pytest

from cyberpunks.common.paths import ROOT


@pytest.fixture(scope="session")
def full_run(tmp_path_factory):
    """Rebuild the plan from the complete demo predictions in a temporary directory."""
    from cyberpunks.planner.agent import run

    source = Path(os.environ.get("DAYBREAK_OPERATIONS_TEST_DATA", ROOT / "data/local-runtime"))
    original = source / "plans/demo-vara/inputs"
    assert original.is_dir(), f"Complete demo predictions are missing: {original}"

    root = tmp_path_factory.mktemp("demo-plan")
    target = root / "work_items/demo-vara"
    target.mkdir(parents=True)
    for path in original.glob("*.jsonl"):
        shutil.copy2(path, target / path.name)
    result = run("demo-vara", mode="existing", out_root=root, solver="greedy")
    assert result.plan.summary.items_valid >= 600
    return root
