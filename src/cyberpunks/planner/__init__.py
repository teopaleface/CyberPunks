"""Agentul: stratul de decizie, planificarea echipelor, acțiunile, jurnalul. Proprietar: firul Teo-planificator."""

from __future__ import annotations

import subprocess
from functools import cache

from cyberpunks.common.paths import ROOT

__version__ = "0.1.0"


@cache
def planner_version() -> str:
    """De exemplu 'planner@0.1.0+3f2c1ab' (commit-ul codului care a făcut planul)."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=2, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        sha = ""
    return f"planner@{__version__}" + (f"+{sha}" if sha else "")
