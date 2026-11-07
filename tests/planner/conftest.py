"""Ajutoare pentru testele planificatorului: lucrări valide construite din fixture-uri, scrise într-un outputs/ temporar."""

from __future__ import annotations

import copy
import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from cyberpunks.common.paths import CONTRACTS

FIX = CONTRACTS / "fixtures"
SCENARIO = "test"
DATE = "2026-11-09"


def fixture_items(source: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (FIX / f"work_items_{source}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def variant(base: dict[str, Any], asset_id: str, **changes: Any) -> dict[str, Any]:
    """O copie a unei lucrări, cu alt activ (ID nou) și câmpuri schimbate prin chei cu puncte: 'prediction.score'."""
    it = copy.deepcopy(base)
    it["asset_id"] = asset_id
    it["work_item_id"] = f"{it['source']}-{it['target_date'].replace('-', '')}-{asset_id}"
    it["prediction"]["prediction_id"] = str(uuid.uuid4())
    for key, value in changes.items():
        node = it
        parts = key.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value
    pr = it["prediction"]
    if "prediction.score" in changes and pr.get("interval_low") is not None and "prediction.interval_low" not in changes:
        pr["interval_low"] = round(max(0.0, pr["score"] - 0.1), 3)  # scorul trebuie să rămână în interval (contract)
        pr["interval_high"] = round(min(1.0, pr["score"] + 0.05), 3)
    if any(k.startswith(("prediction.score", "impact.value_if_true_lei")) for k in changes):
        it["impact"]["expected_value_lei"] = round(pr["score"] * it["impact"]["value_if_true_lei"], 2)
    return it


def write_items(out_root: Path, source: str, rows: list[Any], scenario: str = SCENARIO) -> Path:
    path = out_root / "work_items" / scenario / f"{source}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [r if isinstance(r, str) else json.dumps(r, ensure_ascii=False) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def out_root(tmp_path: Path) -> Path:
    return tmp_path / "outputs"
