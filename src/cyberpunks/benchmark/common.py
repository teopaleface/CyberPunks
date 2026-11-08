"""Piese comune benchmarkului: bootstrap pe grupuri (90%), cronometre, scrierea rezultatelor și a predicțiilor.

Regula pentru diferențe: se reeșantionează GRUPURI întregi (plecări, cartiere, gospodării, săptămâni), nu rânduri,
pentru că rândurile aceluiași grup sunt corelate. Diferența raportată e mereu `candidat - LightGBM`.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.common.paths import DATA_PROCESSED, REPORTS, ROOT

OUT = REPORTS / "benchmark"
PRED = OUT / "predictions"  # predicții pe test, în git (date publice sau sintetice)
PRED_LOCAL = DATA_PROCESSED / "benchmark"  # predicții care nu se pot publica (SGCC: fără licență explicită)
TZ = ZoneInfo("Europe/Bucharest")
N_BOOT = 1000
SEED = 20261108


def ci90(fn: Callable[[np.ndarray], float], groups: np.ndarray, n: int = N_BOOT, seed: int = SEED) -> dict:
    """Interval bootstrap 90% pentru `fn(indici)`, reeșantionând grupuri întregi cu întoarcere.

    `fn` primește indicii rândurilor alese și întoarce statistica (de exemplu diferența de F1 dintre modele);
    întoarce NaN dacă eșantionul nu permite calculul (se sare).
    """
    groups = np.asarray(groups)
    if groups.ndim != 1 or len(groups) == 0 or n < 1:
        raise ValueError("Bootstrap cere grupuri nenule și cel puțin o reeșantionare")
    uniq, inv = np.unique(groups, return_inverse=True)
    members = [np.flatnonzero(inv == g) for g in range(len(uniq))]
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        pick = rng.integers(0, len(uniq), len(uniq))
        v = fn(np.concatenate([members[g] for g in pick]))
        if np.isfinite(v):
            vals.append(v)
    if not vals:
        raise ValueError("Nicio statistică finită în bootstrap; date insuficiente pentru interval")
    lo, hi = np.percentile(vals, [5, 95])
    point = fn(np.arange(len(groups)))
    return {"delta": r(point), "ci90": [r(lo), r(hi)], "includes_zero": bool(lo <= 0 <= hi),
            "share_positive": r(float(np.mean(np.asarray(vals) > 0))), "groups": len(uniq), "n_boot": len(vals)}


def r(x: float, nd: int = 5) -> float:
    return float(round(float(x), nd)) if np.isfinite(x) else float("nan")


@contextmanager
def timer(store: dict, key: str):
    t0 = time.perf_counter()
    yield
    store[key] = round(time.perf_counter() - t0, 3)


def environment() -> dict:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "nogit"
    return {"git": sha, "python": platform.python_version(), "machine": platform.machine(), "system": platform.system(),
            "cpu_count": os.cpu_count(), "lightgbm": version("lightgbm"),
            "catboost": version("catboost"), "xgboost": version("xgboost"), "scikit_learn": version("scikit-learn"),
            "created_at": datetime.now(TZ).replace(microsecond=0).isoformat()}


def write_json(name: str, data: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=_default) + "\n", encoding="utf-8")
    print(f"scris: {path}", flush=True)
    return path


def write_predictions(name: str, frame: pd.DataFrame, local: bool = False) -> Path:
    base = PRED_LOCAL if local else PRED
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{name}.parquet"
    frame.reset_index(drop=True).to_parquet(path, index=False)
    print(f"scris: {path} ({len(frame)} rânduri)", flush=True)
    return path


def _default(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))
