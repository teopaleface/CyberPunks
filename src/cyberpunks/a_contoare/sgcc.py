"""SGCC: consum zilnic real și etichete reale de furt (State Grid Corporation of China, Zheng et al. 2018).

    uv run python -m cyberpunks.a_contoare.sgcc      # construiește tabelul de features (în data/processed/A/)

Ce face:
- citește `data/raw/A/sgcc/data.csv` (vezi download.py), sortează coloanele de zile (în fișier sunt în ordine
  alfabetică) și pune NaN pentru ziua care lipsește (2016-09-18), ca grila să fie regulată;
- calculează features zilnice pe toată perioada (ca în literatură), cu "vecinii" = mediana zilnică a clienților
  DE ANTRENARE (scoate sezonul și sărbătorile, de exemplu Anul Nou chinezesc), aceeași referință pentru toate
  seturile, ca testul să nu influențeze features-urile de antrenare;
- împarte pe clienți, stratificat după etichetă: 60% antrenare, 20% calibrare, 20% test (seed fix).
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from cyberpunks.a_contoare.download import SGCC_DIR, download_sgcc
from cyberpunks.a_contoare.features import DAILY_FEATURES, daily_features
from cyberpunks.common.paths import DATA_PROCESSED

PROCESSED_A = DATA_PROCESSED / "A"
SGCC_FEATURES = PROCESSED_A / "sgcc_features.parquet"
SEED = 42


def load_sgcc() -> tuple[pd.Series, np.ndarray, pd.DatetimeIndex, np.ndarray]:
    """Întoarce (CONS_NO, FLAG, zile, X) cu X de forma (clienți, zile), kWh/zi, NaN = lipsă."""
    csv = SGCC_DIR / "data.csv"
    if not csv.exists():
        download_sgcc()
    df = pd.read_csv(csv)
    date_cols = [c for c in df.columns if c not in ("CONS_NO", "FLAG")]
    dates = pd.to_datetime(pd.Series(date_cols), format="%Y/%m/%d")
    order = np.argsort(dates.to_numpy())
    sorted_cols = [date_cols[i] for i in order]
    x = df[sorted_cols].to_numpy(dtype=np.float64)
    days = pd.DatetimeIndex(dates.iloc[order])
    full = pd.date_range(days.min(), days.max(), freq="D")
    if len(full) != len(days):  # ziua lipsă devine o coloană NaN
        pos = full.get_indexer(days)
        grid = np.full((x.shape[0], len(full)), np.nan)
        grid[:, pos] = x
        x, days = grid, full
    return df["CONS_NO"], df["FLAG"].to_numpy(dtype=np.int8), days, x


def split_customers(flag: np.ndarray, seed: int = SEED) -> np.ndarray:
    """Împărțirea pe clienți, stratificată: 'train' 60%, 'cal' 20%, 'test' 20%."""
    idx = np.arange(len(flag))
    rest, test = train_test_split(idx, test_size=0.20, stratify=flag, random_state=seed)
    train, cal = train_test_split(rest, test_size=0.25, stratify=flag[rest], random_state=seed)
    split = np.empty(len(flag), dtype=object)
    split[train], split[cal], split[test] = "train", "cal", "test"
    return split


def build_features(force: bool = False) -> pd.DataFrame:
    """Tabelul de features SGCC (un rând pe client), cu eticheta și împărțirea. Salvat ca parquet."""
    if SGCC_FEATURES.exists() and not force:
        return pd.read_parquet(SGCC_FEATURES)
    cons, flag, _days, x = load_sgcc()
    split = split_customers(flag)
    with np.errstate(all="ignore"):
        peer = np.nanmedian(x[split == "train"], axis=0)  # referința vecinilor: DOAR clienții de antrenare
    feats = daily_features(x, peer)
    feats.insert(0, "customer_id", cons.to_numpy())
    feats["label"] = flag
    feats["split"] = split
    feats["sgcc_row"] = np.arange(len(flag))
    PROCESSED_A.mkdir(parents=True, exist_ok=True)
    feats.to_parquet(SGCC_FEATURES, index=False)
    return feats


def main() -> int:
    feats = build_features(force="--force" in sys.argv)
    print(f"SGCC: {len(feats)} clienți, {len(DAILY_FEATURES)} features, salvat în {SGCC_FEATURES}")
    print(feats.groupby("split")["label"].agg(["count", "sum", "mean"]).round(4).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
