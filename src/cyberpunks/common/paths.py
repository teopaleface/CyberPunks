"""Căile standard din repo. Toate firele le folosesc, ca să nu existe căi scrise de mână."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "config"
CONTRACTS = ROOT / "contracts"
DATA_RAW = ROOT / "data" / "raw"  # descărcări, în afara git
DATA_INTERIM = ROOT / "data" / "interim"  # în afara git
DATA_PROCESSED = ROOT / "data" / "processed"  # în afara git
DATA_SAMPLES = ROOT / "data" / "samples"  # mostre mici, în git
MODELS = ROOT / "models"  # artefacte; doar models/release/ intră în git
REPORTS = ROOT / "reports"  # metrici, grafice, analize de erori (în git)
# A runtime may isolate predictions and operations without changing release data.
# Existing commands keep the original output directory unless explicitly configured.
OUTPUTS = Path(os.environ.get("CYBERPUNKS_OUTPUT_ROOT", str(ROOT / "outputs"))).expanduser().resolve()


def work_items_path(scenario: str, source: str) -> Path:
    """outputs/work_items/<scenariu>/<A|B|C>.jsonl"""
    return OUTPUTS / "work_items" / scenario / f"{source}.jsonl"


def plan_dir(scenario: str) -> Path:
    """outputs/plans/<scenariu>/ cu plan.json, audit.jsonl, work_orders/, report.md"""
    return OUTPUTS / "plans" / scenario
