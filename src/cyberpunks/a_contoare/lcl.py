"""Low Carbon London: consum real la 30 de minute, peste care injectăm defecte și furturi (etichete din construcție).

    uv run python -m cyberpunks.a_contoare.lcl          # citește CSV-urile și construiește eșantioanele

Pași:
1. `load_lcl()` citește fișierele descărcate, curăță (spații, "Null", rânduri duplicate, ore nepotrivite, ora de
   vară) și pune totul într-un tablou (gospodării × zile × 48), salvat în data/interim/A/.
2. `build_samples()` face eșantioane (gospodărie, zi de evaluare) cu o fereastră de 180 de zile:
   - gospodăriile se împart 60/20/20 în antrenare / calibrare / test (nicio gospodărie în două seturi);
   - antrenarea și calibrarea folosesc zile de evaluare din dec. 2012 - aug. 2013, testul din sept. 2013 -
     feb. 2014 (perioadă ulterioară);
   - pe fiecare eșantion injectăm (sau nu) un defect, un furt sau o schimbare normală (inject.py);
   - "vecinii" sunt gospodăriile din același post sintetic (grupuri de ~25 din același set).
Datele sunt SINTETICE ca etichete: consumul e real, problemele sunt injectate de noi.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
import pyarrow.csv as pacsv

from cyberpunks.a_contoare import inject as inj
from cyberpunks.a_contoare.download import LCL_DIR
from cyberpunks.a_contoare.features import daily_features, intraday_features
from cyberpunks.common.config import load as load_config
from cyberpunks.common.paths import DATA_INTERIM, DATA_PROCESSED

INTERIM_A = DATA_INTERIM / "A"
PROCESSED_A = DATA_PROCESSED / "A"
HH_NPY = INTERIM_A / "lcl_hh.npy"
HH_META = INTERIM_A / "lcl_households.parquet"
SAMPLES = PROCESSED_A / "lcl_samples.parquet"

CAL_START = pd.Timestamp("2011-11-01")  # prima zi din tabloul de zile
CAL_END = pd.Timestamp("2014-02-28")
WINDOW = 180  # zile în fereastra unui eșantion
RECENT = 28  # zile "recente" (problema trebuie să fie activă aici ca să conteze ca problemă)
INTRADAY_BASE = 56  # zile de istoric pentru profilul zilnic
SEED = 42
POST_SIZE = 25

# Cât de des apare fiecare familie. La antrenare mărim problemele ca modelul să aibă exemple; la calibrare,
# test și demo folosim o prevalență plauzibilă (IPOTEZĂ, vezi docs/data/A.md): 3% defecte, 2% furturi.
TRAIN_FAMILY_SHARE = {"none": 0.50, "faulty": 0.25, "tamper": 0.20, "benign": 0.05}
DEPLOY_FAMILY_SHARE = {"none": 0.91, "faulty": 0.03, "tamper": 0.02, "benign": 0.04}


def kind_probs(family_share: dict[str, float]) -> dict[str, float]:
    """Împarte cota fiecărei familii egal între tipurile ei."""
    probs = {"none": family_share["none"]}
    for fam, kinds in (("faulty", inj.FAULT_KINDS), ("tamper", inj.TAMPER_KINDS), ("benign", inj.BENIGN_KINDS)):
        for k in kinds:
            probs[k] = family_share[fam] / len(kinds)
    return probs


# --------------------------------------------------------------------------------------------
# 1. Citirea și curățarea
# --------------------------------------------------------------------------------------------


def _read_one(path) -> pd.DataFrame:
    tbl = pacsv.read_csv(path, convert_options=pacsv.ConvertOptions(column_types={"KWH/hh (per half hour) ": "string"}))
    df = tbl.to_pandas()
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"KWH/hh (per half hour)": "kwh"})
    df["kwh"] = pd.to_numeric(df["kwh"].str.strip(), errors="coerce")  # "Null" -> NaN
    return df[["LCLid", "DateTime", "kwh"]]


def expected_lcl_files() -> list[str]:
    """Fișierele LCL din manifestul de sume de control din git (data/samples/A/checksums_lcl.sha256)."""
    from cyberpunks.a_contoare.download import LCL_CHECKSUMS, LCL_DEFAULT_FILES

    if LCL_CHECKSUMS.exists():
        names = [ln.split()[1] for ln in LCL_CHECKSUMS.read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith("#")]
        if names:
            return names
    return [f"LCL-June2015v2_{k}.csv" for k in LCL_DEFAULT_FILES]


def load_lcl(force: bool = False) -> tuple[np.ndarray, pd.DataFrame]:
    """Tabloul (gospodării × zile × 48) în kWh pe 30 de minute și tabelul gospodăriilor."""
    if HH_NPY.exists() and HH_META.exists() and not force:
        return np.load(HH_NPY, mmap_mode="r"), pd.read_parquet(HH_META)
    files = sorted(LCL_DIR.glob("LCL-June2015v2_*.csv"), key=lambda p: int(p.stem.rsplit("_", 1)[1]))
    expected = expected_lcl_files()
    missing = sorted(set(expected) - {p.name for p in files})
    if not files or missing:
        # un set incomplet ar antrena pe alte gospodării și ar da alte cifre, fără niciun avertisment
        raise SystemExit(
            f"Lipsesc fișierele LCL ({len(missing) or 'toate'}: {', '.join(missing[:5])}...). "
            "Rulează: uv run python -m cyberpunks.a_contoare.download --only lcl"
        )
    files = [p for p in files if p.name in set(expected)]
    df = pd.concat([_read_one(p) for p in files], ignore_index=True)
    ts = pd.to_datetime(df["DateTime"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")
    ok = ts.notna() & df["kwh"].notna() & ts.dt.minute.isin([0, 30]) & (ts.dt.second == 0)
    df, ts = df[ok], ts[ok]
    start = ts - pd.Timedelta(minutes=30)  # ora din fișier marchează sfârșitul intervalului de 30 de minute
    day = (start.dt.normalize() - CAL_START).dt.days.to_numpy()
    slot = (start.dt.hour * 2 + start.dt.minute // 30).to_numpy()
    ids, hh_idx = np.unique(df["LCLid"].to_numpy(), return_inverse=True)
    keep = (day >= 0) & (day <= (CAL_END - CAL_START).days)
    n_days = (CAL_END - CAL_START).days + 1
    arr = np.full((len(ids), n_days, 48), np.nan, dtype=np.float32)
    # duplicatele (aceeași gospodărie și același interval, inclusiv ora dublată la trecerea la ora de iarnă)
    # se mediază; la trecerea la ora de vară lipsesc două intervale (rămân NaN)
    flat = (hh_idx[keep] * n_days + day[keep]) * 48 + slot[keep]
    vals = df["kwh"].to_numpy()[keep]
    sums = np.bincount(flat, weights=vals, minlength=arr.size)
    cnts = np.bincount(flat, minlength=arr.size)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(cnts > 0, sums / np.maximum(cnts, 1), np.nan)
    arr = mean.reshape(arr.shape).astype(np.float32)
    del sums, mean
    valid_days = (np.isfinite(arr).sum(axis=2) >= 40).sum(axis=1)
    dup = (cnts > 1).reshape(arr.shape).sum(axis=(1, 2))
    meta = pd.DataFrame({"household": ids, "valid_days": valid_days, "duplicates_merged": dup})
    INTERIM_A.mkdir(parents=True, exist_ok=True)
    np.save(HH_NPY, arr)
    meta.to_parquet(HH_META, index=False)
    return np.load(HH_NPY, mmap_mode="r"), meta


METER_RESOLUTION_KWH = 0.001  # contoarele din Londra raportează cu 3 zecimale (kWh)


def quantize(hh: np.ndarray, step: float = METER_RESOLUTION_KWH) -> np.ndarray:
    """Rotunjește la rezoluția contorului (NaN rămâne NaN).

    Fără pasul ăsta, injecțiile prin înmulțire (alpha·x, beta·x, deriva) produc valori cu multe zecimale pe care
    niciun contor real nu le trimite, iar modelul învață artefactul în loc de tiparul de consum.
    """
    return np.round(np.asarray(hh, dtype=np.float64) / step) * step


def daily_from_halfhours(hh: np.ndarray, min_slots: int = 40) -> np.ndarray:
    """Consumul zilnic din citirile la 30 de minute; zilele cu sub `min_slots` citiri devin NaN (gol)."""
    n_valid = np.isfinite(hh).sum(axis=-1)
    tot = np.nansum(hh, axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        daily = tot * 48.0 / np.maximum(n_valid, 1)
    return np.where(n_valid >= min_slots, daily, np.nan)


# --------------------------------------------------------------------------------------------
# 2. Eșantioanele cu probleme injectate
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SampleSpec:
    split: str
    dates: pd.DatetimeIndex
    family_share: dict[str, float]
    replicates: int = 1


def split_households(n: int, seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    split = np.empty(n, dtype=object)
    a, b = int(0.6 * n), int(0.8 * n)
    split[perm[:a]], split[perm[a:b]], split[perm[b:]] = "train", "cal", "test"
    return split


def assign_posts(split: np.ndarray, seed: int = SEED) -> np.ndarray:
    """Posturi sintetice: grupuri de ~25 de gospodării din același set (vecinii se compară între ei)."""
    rng = np.random.default_rng(seed + 1)
    post = np.empty(len(split), dtype=object)
    for s in np.unique(split):
        idx = rng.permutation(np.flatnonzero(split == s))
        for j, i in enumerate(idx):
            post[i] = f"LP-{s}-{j // POST_SIZE:03d}"
    return post


def economics() -> dict[str, float]:
    """Ipotezele economice din config/economics.yaml (cheia `meters` și costul energiei pierdute)."""
    econ = load_config("economics")
    m = econ.get("meters", {})
    visit = float(m.get("inspection_visit_cost_lei", 250))
    return {
        "horizon_days": float(m.get("detection_horizon_days", 90)),
        "loss_cost_lei_per_kwh": float(econ.get("energy", {}).get("loss_cost_lei_per_kwh", 0.70)),
        "visit_cost_lei": visit,
        "remote_cost_lei": float(m.get("remote_reading_cost_lei", 2)),
        "service_time_min": float(m.get("service_time_min", 40)),
        # CALCUL: un contor defect, nereparat, cere cel puțin o deplasare în orizont (citire manuală sau reclamație),
        # deci repararea lui evită costul unei vizite. Dacă planificatorul adaugă cheia, o folosim pe aceea.
        "faulty_fixed_lei": float(m.get("faulty_meter_fixed_value_lei", visit)),
    }


def value_lei(kwh_lost: float, n_days: int, family: str, kind: str = "") -> float:
    """Valoarea reală (în lei) dacă problema e găsită acum: pierderea zilnică × orizont × cost + componenta fixă."""
    e = economics()
    fixed = e["faulty_fixed_lei"] if family == "faulty" else 0.0
    daily_loss = max(0.0, kwh_lost) / max(n_days, 1)
    return round(daily_loss * e["horizon_days"] * e["loss_cost_lei_per_kwh"] + fixed, 2)


def _window(arr: np.ndarray, h: int, end_day: int) -> np.ndarray:
    return np.array(arr[h, end_day - WINDOW + 1 : end_day + 1], dtype=np.float64)


def build_samples(force: bool = False, seed: int = SEED) -> pd.DataFrame:
    """Eșantioanele LCL cu features, etichete și valoarea reală. Salvat ca parquet."""
    if SAMPLES.exists() and not force:
        return pd.read_parquet(SAMPLES)
    arr, meta = load_lcl()
    usable = np.flatnonzero(meta["valid_days"].to_numpy() >= 270)
    split = split_households(len(usable), seed)
    posts = assign_posts(split, seed)
    daily_all = daily_from_halfhours(np.asarray(arr[usable]))  # (n_hh, n_days)

    # mediana zilnică pe fiecare post (din datele originale, fără injecții: problemele reale sunt rare)
    post_median: dict[str, np.ndarray] = {}
    for p in np.unique(posts):
        with np.errstate(all="ignore"):
            post_median[p] = np.nanmedian(daily_all[posts == p], axis=0)

    specs = [
        SampleSpec("train", pd.date_range("2012-12-01", "2013-08-31", freq="14D"), TRAIN_FAMILY_SHARE),
        SampleSpec("cal", pd.date_range("2012-12-08", "2013-08-31", freq="14D"), DEPLOY_FAMILY_SHARE),
        SampleSpec("test", pd.date_range("2013-09-07", "2014-02-22", freq="7D"), DEPLOY_FAMILY_SHARE, replicates=2),
    ]
    rng = np.random.default_rng(seed)
    rows, x_daily, x_peer, hh_recent, hh_base = [], [], [], [], []
    for spec in specs:
        probs = kind_probs(spec.family_share)
        members = np.flatnonzero(split == spec.split)
        for d in spec.dates:
            end_day = (d - CAL_START).days
            for i in members:
                h = usable[i]
                window = _window(arr, h, end_day)
                daily_orig = daily_from_halfhours(window)
                if np.isfinite(daily_orig).sum() < 120 or np.isfinite(daily_orig[-RECENT:]).sum() < 14:
                    continue
                for rep in range(spec.replicates):
                    kind = inj.sample_kind(rng, probs)
                    if kind in inj.EPISODIC_KINDS:
                        start = int(rng.integers(WINDOW - 40, WINDOW - 7))
                    else:
                        start = int(rng.integers(WINDOW - 60, WINDOW - 3))
                    new, info = inj.inject(window, kind, rng, start)
                    new = quantize(new)  # rezoluția contorului: altfel modelul învață "valori nerotunjite = furt"
                    active = info.kind != "none" and info.end_day > WINDOW - RECENT
                    family = info.family if active else "normal"
                    n_aff = max(1, info.end_day - info.start_day) if info.kind != "none" else 1
                    lost = info.kwh_true - info.kwh_recorded
                    rows.append(
                        {
                            "sample_id": f"LCL-{meta['household'].iat[h]}-{d:%Y%m%d}-{rep}",
                            "household": meta["household"].iat[h],
                            "post": posts[i],
                            "split": spec.split,
                            "date": d,
                            "kind": info.kind if active else ("none" if info.kind == "none" else info.kind),
                            "family": family,
                            "problem": int(family in ("faulty", "tamper")),
                            "onset_days_ago": WINDOW - info.start_day if info.kind != "none" else -1,
                            "kwh_lost": round(float(lost), 3),
                            "value_true_lei": value_lei(lost, n_aff, family, info.kind)
                            if family in ("faulty", "tamper")
                            else 0.0,
                        }
                    )
                    x_daily.append(daily_from_halfhours(new))
                    x_peer.append(post_median[posts[i]][end_day - WINDOW + 1 : end_day + 1])
                    hh_recent.append(new[-RECENT:].astype(np.float32))
                    hh_base.append(new[-RECENT - INTRADAY_BASE : -RECENT].astype(np.float32))
    meta_df = pd.DataFrame(rows)
    daily_df = daily_features(np.vstack(x_daily), np.vstack(x_peer))
    intra_parts = []
    for b in range(0, len(hh_recent), 4000):
        intra_parts.append(intraday_features(np.stack(hh_recent[b : b + 4000]), np.stack(hh_base[b : b + 4000])))
    intra_df = pd.concat(intra_parts, ignore_index=True)
    out = pd.concat([meta_df, daily_df, intra_df], axis=1)
    PROCESSED_A.mkdir(parents=True, exist_ok=True)
    out.to_parquet(SAMPLES, index=False)
    return out


def main() -> int:
    force = "--force" in sys.argv
    arr, meta = load_lcl(force=force)
    print(f"LCL: {arr.shape[0]} gospodării, {arr.shape[1]} zile; cu cel puțin 270 de zile: {(meta.valid_days >= 270).sum()}")
    s = build_samples(force=force)
    print(f"eșantioane: {len(s)}")
    print(s.groupby(["split", "family"]).size().unstack(fill_value=0).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
