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


def confirmed_by_bilant(it: dict[str, Any], confirmed: bool = True) -> dict[str, Any]:
    """Un contor cu semnal de siguranță, comparat cu bilanțul postului (extra.fusion, contractul BilantFusion).
    Confirmat = bilanțul arată energie lipsă și a urcat scorul; altfel scorul rămâne al modelului A."""
    score = it["prediction"]["score"]
    a_score = round(max(0.0, score - 0.05), 4) if confirmed else score
    it.setdefault("extra", {})
    it["extra"] = {**(it["extra"] or {}), "fusion": {
        "post_id": "PT-TEST", "bilant_prediction_id": "bilant-test", "post_excess_loss_kwh_day": 12.0 if confirmed else 0.2,
        "post_excess_loss_lei_month": 250.0 if confirmed else 4.0, "a_score": a_score, "combined_score": score,
        "note_ro": "Confirmat de bilanțul postului PT-TEST (test)." if confirmed else "Bilanțul postului PT-TEST nu confirmă (test).",
    }}
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


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "weekly_batching: rulează cu amânarea până la tura de zonă de la sfârșitul săptămânii")


@pytest.fixture(autouse=True)
def _daily_dispatch_by_default(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Testele mai vechi verifică traseele în ziua planului (reguli, solver, aprobări). Amânarea până la tura de zonă
    (planner/dispatch.py) are testele ei, marcate cu `weekly_batching`; în rest e oprită, ca lucrările să ajungă în trasee."""
    if request.node.get_closest_marker("weekly_batching"):
        return
    from cyberpunks.planner.settings import Settings

    original = Settings.load.__func__

    def load(cls: type[Settings], config_dir: Path | None = None) -> Settings:
        s = original(cls, config_dir)
        s.planner.setdefault("dispatch", {})["weekly_batching"] = False
        return s

    monkeypatch.setattr(Settings, "load", classmethod(load))
