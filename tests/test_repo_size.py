"""Paza de mărime a repo-ului: niciun fișier urmărit de git peste 5 MB, cu excepțiile listate.

Cerința lui Teo (7 nov.): repo-ul nu primește fișiere grele. Modelele finale au voie (juriul trebuie
să poată rula demo-ul fără reantrenare), dar se salvează în git doar la versiunea finală.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 5 * 1024 * 1024
ALLOWED = {"models/release/C/bundle.joblib", "models/release/bilant/diagnose.txt.gz", "models/release/bilant-v2/diagnose.txt.gz"}  # modelele finale comprimate
ALLOWED_PREFIXES = ("presentation/exports/",)  # exportul final al filmului, sub 50 MB


def test_no_big_tracked_files() -> None:
    files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    big = []
    for name in filter(None, files.decode().split("\0")):
        p = ROOT / name
        if not p.is_file() or name in ALLOWED:
            continue
        size = p.stat().st_size
        limit = 50 * 1024 * 1024 if name.startswith(ALLOWED_PREFIXES) else LIMIT
        if size > limit:
            big.append(f"{name} ({size / 1048576:.1f} MB)")
    assert not big, "Fișiere prea mari în git: " + ", ".join(big)
