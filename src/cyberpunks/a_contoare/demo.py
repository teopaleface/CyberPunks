"""Populația demo: 10.000 de contoare SINTETICE în București-Ilfov, pentru o zi de evaluare dată.

Fiecare contor din `data/samples/A/meters.csv` (topologia sintetică) primește:
- profilul real al unei gospodării din Londra din setul de TEST (nevăzută de model la antrenare), la o scară
  aleatoare (contoarele care împart o gospodărie diferă prin scară, zgomot și decalaj de 0-3 săptămâni);
- calendarul mutat în 2026 cu un număr întreg de săptămâni (zilele săptămânii rămân la locul lor);
- cu prevalența din calibrare (3% defecte, 2% furturi, 4% schimbări normale), un defect sau un furt injectat;
- câteva probleme de intrare (unitate greșită, istoric scurt), ca agentul să arate cum le tratează.
Adevărul (ce am injectat) se scrie separat, doar pentru evaluarea agentului; modelul nu îl vede.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from cyberpunks.a_contoare import inject as inj
from cyberpunks.a_contoare.lcl import (
    CAL_START,
    DEPLOY_FAMILY_SHARE,
    HH_NPY,
    RECENT,
    SAMPLES,
    WINDOW,
    build_samples,
    kind_probs,
    load_lcl,
    quantize,
    value_lei,
)
from cyberpunks.common.paths import DATA_SAMPLES

SAMPLES_A = DATA_SAMPLES / "A"
PACK = SAMPLES_A / "demo_pack.npy.xz"  # profile reale (Low Carbon London, UK Power Networks, CC BY 4.0), perioada demo
PACK_META = SAMPLES_A / "demo_pack.json"
PACK_START = pd.Timestamp("2012-12-15")  # acoperă demo-vara (iulie) și "mâine" în noiembrie, cu 3 săptămâni de rezervă
PACK_END = pd.Timestamp("2013-11-30")
PACK_HOUSEHOLDS = 160  # primele 160 de gospodării de test (sortate după ID), nevăzute la antrenare
NAN_WH = 65535  # valoarea care înseamnă "lipsă" în pachet
WEEKS_SHIFT = 678  # 2026 - 678 săptămâni ≈ 2013, aceeași zi a săptămânii
UNIT_ERROR_SHARE = 0.002  # contoare raportate în Wh în loc de kWh (intrare greșită)
SHORT_HISTORY_SHARE = 0.003  # contoare noi, cu istoric prea scurt


@dataclass
class DemoPopulation:
    target_date: date
    source_date: pd.Timestamp
    meters: pd.DataFrame  # topologia + adevărul injectat
    hh: np.ndarray  # (n_contoare, WINDOW, 48), kWh pe 30 de minute, după injecții
    days: pd.DatetimeIndex  # zilele din fereastră, în calendarul 2026


def load_topology() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(contoare, posturi): contoarele A pe posturile din registrul comun al firului C."""
    from cyberpunks.a_contoare.topology import load_topology as _load

    posts, meters = _load()
    return meters, posts


def source_date_for(target: date) -> pd.Timestamp:
    """Ziua din datele Londra care joacă rolul zilei `target` (2026), cu aceeași zi a săptămânii."""
    d = pd.Timestamp(target) - pd.Timedelta(weeks=WEEKS_SHIFT)
    first_ok = CAL_START + pd.Timedelta(days=WINDOW + 28 + 60)
    last_ok = pd.Timestamp("2014-02-27")
    while d > last_ok:
        d -= pd.Timedelta(weeks=52)
    while d < first_ok:
        d += pd.Timedelta(weeks=52)
    return d


def export_pack() -> Path:
    """Scrie pachetul demo din datele complete: gospodăriile de test, PACK_START..PACK_END, în Wh (uint16, lzma)."""
    import io
    import json
    import lzma

    arr, meta = load_lcl()
    samples = build_samples()
    households = sorted(samples.loc[samples.split == "test", "household"].unique())[:PACK_HOUSEHOLDS]
    index = {h: i for i, h in enumerate(meta["household"])}
    d0, d1 = (PACK_START - CAL_START).days, (PACK_END - CAL_START).days + 1
    sub = np.asarray(arr[[index[h] for h in households], d0:d1], dtype=np.float64)
    wh = np.where(np.isfinite(sub), np.round(sub * 1000.0), NAN_WH).clip(0, NAN_WH).astype(np.uint16)
    buf = io.BytesIO()
    np.save(buf, wh)
    PACK.write_bytes(lzma.compress(buf.getvalue(), preset=9))
    PACK_META.write_text(
        json.dumps(
            {
                "households": households,
                "start": str(PACK_START.date()),
                "end": str(PACK_END.date()),
                "unit": "Wh pe 30 de minute, 65535 = lipsă",
                "source": "Low Carbon London, UK Power Networks, via London Datastore, CC BY 4.0",
                "note": "Profile reale ale gospodăriilor din setul de test A (nevăzute la antrenare), doar perioada demo.",
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return PACK


def _load_pack() -> tuple[np.ndarray, list[str], pd.Timestamp]:
    import io
    import json
    import lzma

    meta = json.loads(PACK_META.read_text(encoding="utf-8"))
    wh = np.load(io.BytesIO(lzma.decompress(PACK.read_bytes())))
    arr = np.where(wh == NAN_WH, np.nan, wh.astype(np.float32) / 1000.0).astype(np.float32)
    return arr, list(meta["households"]), pd.Timestamp(meta["start"])


def profile_source(src: pd.Timestamp) -> tuple[np.ndarray, list[str], dict[str, int], pd.Timestamp]:
    """Profilele pentru populația demo: din pachetul din git (aceleași rezultate oriunde), altfel din datele complete."""
    need_from = src - pd.Timedelta(days=WINDOW + 7 * 3)
    if PACK.exists() and PACK_META.exists():
        arr, households, start = _load_pack()
        if need_from >= start and src <= start + pd.Timedelta(days=arr.shape[1] - 1):
            return arr, households, {h: i for i, h in enumerate(households)}, start
    if HH_NPY.exists() and SAMPLES.exists():
        arr, meta = load_lcl()
        samples = build_samples()
        households = sorted(samples.loc[samples.split == "test", "household"].unique())[:PACK_HOUSEHOLDS]
        return arr, households, {h: i for i, h in enumerate(meta["household"])}, CAL_START
    raise SystemExit(
        f"Pachetul demo nu acoperă data cerută (are nevoie de {need_from.date()} - {src.date()} în calendarul Londra), "
        "iar datele complete lipsesc. Rulează: make a-data"
    )


def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


def build_population(target: date, scenario: str = "demo", n_meters: int | None = None) -> DemoPopulation:
    meters, _posts = load_topology()
    if n_meters:
        meters = meters.head(n_meters).copy()
    src = source_date_for(target)
    arr, test_households, hh_index, day0 = profile_source(src)
    rng = np.random.default_rng(_seed(scenario, target.isoformat()))
    probs = kind_probs(DEPLOY_FAMILY_SHARE)

    n = len(meters)
    out = np.full((n, WINDOW, 48), np.nan, dtype=np.float32)
    rows = []
    order = rng.permutation(n)
    for j, i in enumerate(order):
        # caută o gospodărie de test cu destule date în fereastră
        for _attempt in range(20):
            h = test_households[(j + _attempt * 7919) % len(test_households)] if _attempt else rng.choice(test_households)
            offset_weeks = int(rng.integers(0, 4))
            end = (src - day0).days - 7 * offset_weeks
            win = np.array(arr[hh_index[h], end - WINDOW + 1 : end + 1], dtype=np.float64)
            if np.isfinite(win).any(axis=1).sum() >= 150 and np.isfinite(win[-RECENT:]).any(axis=1).sum() >= 21:
                break
        scale = float(np.exp(rng.normal(0.0, 0.25)))
        # variație pe zi (nu pe jumătate de oră): păstrează forma zilei și valorile repetate naturale (frigiderul
        # noaptea), care altfel ar dispărea și ar face orice contor să pară manipulat
        day_factor = rng.normal(1.0, 0.04, (win.shape[0], 1)).clip(0.85, 1.15)
        win = quantize(np.clip(win * scale * day_factor, 0.0, None))
        kind = inj.sample_kind(rng, probs)
        if kind in inj.EPISODIC_KINDS:
            start = int(rng.integers(WINDOW - 40, WINDOW - 7))
        else:
            start = int(rng.integers(WINDOW - 60, WINDOW - 3))
        new, info = inj.inject(win, kind, rng, start)
        new = quantize(new)
        # energia din ultimele 4 săptămâni, cum o vede bilanțul postului: consumul real trece prin post, contorul
        # raportează mai puțin (sau mai mult); zilele fără citiri le estimează VEE, deci nu apar ca pierdere
        tru_d, rec_d = np.nansum(win[-RECENT:], axis=1), np.nansum(new[-RECENT:], axis=1)
        day_ok = np.isfinite(new[-RECENT:]).sum(axis=1) >= 40
        true_recent = float(np.mean(tru_d))
        loss_recent = float(np.mean(np.where(day_ok, tru_d - rec_d, 0.0)))
        active = info.kind != "none" and info.end_day > WINDOW - RECENT
        family = info.family if active else "normal"
        lost = info.kwh_true - info.kwh_recorded
        n_aff = max(1, info.end_day - info.start_day) if info.kind != "none" else 1
        input_issue = ""
        u = rng.random()
        if u < UNIT_ERROR_SHARE:
            new = new * 1000.0  # sistemul sursă a trimis Wh în loc de kWh
            input_issue = "unit_wh"
        elif u < UNIT_ERROR_SHARE + SHORT_HISTORY_SHARE:
            new[: WINDOW - int(rng.integers(5, 25))] = np.nan  # contor montat recent
            input_issue = "short_history"
        out[i] = new.astype(np.float32)
        rows.append(
            {
                "idx": i,
                "source_household": h,
                "scale": round(scale, 3),
                "offset_weeks": offset_weeks,
                "true_kind": info.kind if (active or info.kind == "none") else f"{info.kind}_terminat",
                "true_family": family,
                "true_problem": int(family in ("faulty", "tamper")),
                "true_onset_days_ago": WINDOW - info.start_day if info.kind != "none" else -1,
                "true_kwh_lost": round(float(lost), 3),
                "true_value_lei": value_lei(lost, n_aff, family, info.kind) if family in ("faulty", "tamper") else 0.0,
                "input_issue": input_issue,
                "true_recent_kwh_day": round(true_recent, 3),
                "true_recent_loss_kwh_day": round(loss_recent, 3),
            }
        )
    truth = pd.DataFrame(rows).sort_values("idx").reset_index(drop=True)
    meters = pd.concat([meters.reset_index(drop=True), truth.drop(columns="idx")], axis=1)
    days = pd.date_range(end=pd.Timestamp(target), periods=WINDOW, freq="D")
    return DemoPopulation(target, src, meters, out, days)


def target_date_from_scenario(scenario: str, override: str | None = None) -> date:
    """Data scenariului: --date, apoi config/scenarios.yaml; 'auto_tomorrow' = mâine; 'TBD-B' = 15 iulie 2026."""
    from zoneinfo import ZoneInfo

    from cyberpunks.common.config import load as load_config

    if override:
        return date.fromisoformat(override)
    sc = load_config("scenarios").get("scenarios", {}).get(scenario, {})
    raw = str(sc.get("date", "")).strip()
    if raw == "auto_tomorrow":
        from datetime import datetime

        return (datetime.now(ZoneInfo("Europe/Bucharest")) + timedelta(days=1)).date()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return date(2026, 7, 15)  # până anunță firul B data reală a scenariului de vară
