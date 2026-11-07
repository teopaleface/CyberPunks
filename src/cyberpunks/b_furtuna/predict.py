"""Aplică modelul B pe zonele Rețele Electrice și scrie lucrările pentru planificator.

    uv run python -m cyberpunks.b_furtuna.predict --scenario demo-vara
    uv run python -m cyberpunks.b_furtuna.predict --scenario maine
    uv run python -m cyberpunks.b_furtuna.predict --scenario demo-vara --date 2025-07-07

Scrie `outputs/work_items/<scenariu>/B.jsonl` (un WorkItem pe zonă) și `outputs/series/<scenariu>/<id>.json`
(rafalele pe ore). Funcția importabilă: `run(scenario, date) -> Path`.

Reguli (în cod, nu în LLM):
- `preposition_crew` dacă P(vârf ≥ 1% din clienți) ≥ pragul ales pe validare (cel mai bun F1 pe OOF);
- `human_review` (abstain) dacă lipsește vremea, dacă zona iese din ce a văzut modelul la antrenare sau dacă
  sursele meteo nu se pun de acord și decizia s-ar schimba;
- `no_action` altfel.
Modelul e validat pe date externe (SUA); trebuie calibrat pe istoricul de avarii Rețele Electrice.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import numpy as np
import pandas as pd

from cyberpunks.b_furtuna import explain, openmeteo, romania
from cyberpunks.b_furtuna.features import FEATURES, make_features
from cyberpunks.b_furtuna.model import CASE_FEATURES, MODEL_ID, MODEL_PATH, BModel
from cyberpunks.common import config
from cyberpunks.common.contracts import (
    DataQuality,
    Effort,
    Explanation,
    Impact,
    Location,
    Prediction,
    Series,
    SeriesAnnotation,
    SeriesPoint,
    TimeWindow,
    WorkItem,
)
from cyberpunks.common.paths import OUTPUTS, work_items_path

TZ = ZoneInfo("Europe/Bucharest")
DEMO_VARA_DATE = "2025-07-08"  # aleasă de firul B (vezi docs/research/B.md, secțiunea 3)
ONSET_GUST_KMH = 45.0  # pragul afișat pe grafic
ONSET_PRECIP_MM = 2.0  # de la câți mm pe oră marcăm ploaia pe grafic
STORM_GUST_KMH = 55.0
STORM_RAIN_MM = 1.0
SAFETY_GUST_KMH = 75.0  # peste această rafală, lucrul la înălțime e periculos: semnalăm planificatorului
DISAGREE_WIDTH = 0.35  # lățimea intervalului de probabilitate de la care spunem "nu sunt sigur"
ZONE_FEATURES = {"log_customers", "log_density"}
SCORE_MIN, SCORE_MAX = 0.005, 0.99
# Vreme periculoasă: o zonă în afara antrenării merge la om doar atunci (pe vreme liniștită riscul e oricum mic)
HAZARD = {"gust_max_2d": 50.0, "precip_48h": 15.0, "snow_3d": 3.0, "ice_proxy": 1.0}


def hazardous(row: pd.Series) -> bool:
    return any(pd.notna(row.get(f)) and float(row.get(f)) >= v for f, v in HAZARD.items())
DATA_SOURCES = [
    "Open-Meteo (archive ERA5/IFS pentru istoric; forecast și ensemble ICON-EPS pentru mâine)",
    "Model antrenat pe EAGLE-I (ORNL, SUA, 2023-2024), validat pe 2025 și pe state nevăzute",
    "Clienți pe județ: Planul de dezvoltare RER 2026-2035 (31.12.2024); pe zone: aproximare din recensământul 2021",
]
VALIDATION_NOTE = "validat pe date externe (SUA, EAGLE-I); de calibrat pe istoricul de avarii Rețele Electrice"


def resolve(scenario: str, day: str | None) -> tuple[date, str]:
    scen = config.load("scenarios")["scenarios"]
    if scenario not in scen:
        raise SystemExit(f"Scenariu necunoscut: {scenario}. Există: {', '.join(scen)}")
    cfg = scen[scenario]
    mode = "historical" if cfg.get("weather") == "historical" else "forecast"
    if day:
        target = date.fromisoformat(day)
    elif str(cfg.get("date")) == "auto_tomorrow":
        target = datetime.now(TZ).date() + timedelta(days=1)
    elif str(cfg.get("date", "")).startswith("TBD"):
        target = date.fromisoformat(DEMO_VARA_DATE)
    else:
        target = date.fromisoformat(str(cfg["date"]))
    if mode == "forecast" and target < datetime.now(TZ).date():
        mode = "historical"
    return target, mode


def decision_time(target: date, mode: str) -> datetime:
    """Când rulează agentul: seara de dinainte (18:00) pentru istoric, acum pentru prognoză."""
    if mode == "historical":
        return datetime.combine(target - timedelta(days=1), time(18, 0), tzinfo=TZ)
    return datetime.now(TZ).replace(microsecond=0)


def storm_onset(h: pd.DataFrame, target: date) -> tuple[datetime, int]:
    """Începutul estimat al furtunii în ziua țintă (ora României).

    Prima oră de la 06:00 cu ploaie ≥ 1 mm sau cu rafală ≥ max(55 km/h, 90% din maximul zilei). Pe căldură, rafalele
    trec de 45 km/h încă de la prânz din amestecul aerului, deci ploaia marchează mai bine sosirea furtunii.
    Fără astfel de ore: ora rafalei maxime. Fără date: 14:00 (furtunile de vară vin de obicei după-amiaza).
    """
    default = datetime.combine(target, time(14, 0), tzinfo=TZ), 14
    if h.empty or "time" not in h:
        return default
    day = h[(h["time"].dt.date == target) & (h["time"].dt.hour >= 6)].sort_values("time")
    if day.empty or day["wind_gusts_10m"].isna().all():
        return default
    gmax = float(day["wind_gusts_10m"].max())
    strong = day["wind_gusts_10m"] >= max(STORM_GUST_KMH, 0.9 * gmax)
    rain = day["precipitation"].fillna(0) >= STORM_RAIN_MM
    hit = day[strong | rain]
    t = hit["time"].iloc[0] if not hit.empty else day.loc[day["wind_gusts_10m"].idxmax(), "time"]
    t = pd.Timestamp(t).to_pydatetime().replace(tzinfo=TZ)
    return t, t.hour


HIST_MODELS = ["icon_seamless", "ecmwf_ifs025", "gfs_seamless"]


def hist_models_daily(zones: list[romania.Zone], start: date, end: date) -> pd.DataFrame:
    """Rafala maximă și ploaia zilnică din trei modele de prognoză (Historical Forecast API), format lung."""
    params = {"latitude": ",".join(str(z.lat) for z in zones), "longitude": ",".join(str(z.lon) for z in zones),
              "start_date": start.isoformat(), "end_date": end.isoformat(),
              "daily": "wind_gusts_10m_max,precipitation_sum", "models": ",".join(HIST_MODELS),
              "timezone": "Europe/Bucharest"}
    data, _ = openmeteo.get(openmeteo.HIST_FORECAST, params, n_locations=len(zones))
    data = data if isinstance(data, list) else [data]
    rows = []
    for z, p in zip(zones, data, strict=True):
        d = p["daily"]
        n = len(d["time"])
        for m in HIST_MODELS:
            g = d.get(f"wind_gusts_10m_max_{m}") or [None] * n
            pr = d.get(f"precipitation_sum_{m}") or [None] * n
            for t, gv, pv in zip(d["time"], g, pr, strict=True):
                rows.append({"zone_id": z.zone_id, "date": pd.Timestamp(t), "model": m, "gust": gv, "precip": pv})
    return pd.DataFrame(rows)


def alt_from_models(feats: pd.DataFrame, mdaily: pd.DataFrame, target: date) -> list[pd.DataFrame]:
    """Câte o variantă a features-urilor pentru fiecare model meteo (se schimbă doar rafala și ploaia)."""
    out = []
    t0, t1 = pd.Timestamp(target), pd.Timestamp(target - timedelta(days=1))
    for m in HIST_MODELS:
        alt = feats.copy()
        sub = mdaily[mdaily["model"] == m].set_index(["zone_id", "date"])
        for i, zid in enumerate(feats["zone_id"]):
            if (zid, t0) not in sub.index or pd.isna(sub.loc[(zid, t0), "gust"]):
                continue
            g = float(sub.loc[(zid, t0), "gust"])
            gp = sub.loc[(zid, t1), "gust"] if (zid, t1) in sub.index else np.nan
            gp = float(gp) if pd.notna(gp) else alt.loc[i, "gust_prev"]
            alt.loc[i, ["gust_max", "gust_prev"]] = [g, gp]
            alt.loc[i, "gust_max_2d"] = np.nanmax([g, gp])
            pr = sub.loc[(zid, t0), "precip"]
            prp = sub.loc[(zid, t1), "precip"] if (zid, t1) in sub.index else 0.0
            if pd.notna(pr):
                alt.loc[i, "precip"] = float(pr)
                alt.loc[i, "precip_48h"] = float(pr) + (float(prp) if pd.notna(prp) else 0.0)
        out.append(alt)
    return out


def uncertainty(model: BModel, zones: list[romania.Zone], feats: pd.DataFrame, target: date, mode: str,
                mdaily: pd.DataFrame | None = None) -> tuple[np.ndarray, np.ndarray, str]:
    """Intervalul probabilității din dezacordul surselor meteo.

    Istoric: trei modele de prognoză (ICON, ECMWF IFS, GFS) din Historical Forecast API, plus arhiva (min-max).
    Prognoză: membrii ICON-EPS (ensemble), P10-P90. Doar rafala și ploaia se schimbă; restul features rămân.
    """
    lats, lons = [z.lat for z in zones], [z.lon for z in zones]
    scenarios: list[pd.DataFrame] = []
    try:
        if mode == "historical":
            if mdaily is None:
                mdaily = hist_models_daily(zones, target - timedelta(days=1), target)
            scenarios = alt_from_models(feats, mdaily, target)
            source = "dezacordul a trei modele de prognoză (ICON, ECMWF IFS, GFS) față de arhivă"
        else:
            data = openmeteo.ensemble_gusts(lats, lons, forecast_days=max((target - date.today()).days + 2, 2))
            members = sorted({k.split("_member")[1] for k in data[0]["hourly"] if "_member" in k})
            for mem in members[:40]:
                alt = feats.copy()
                for i, p in enumerate(data):
                    h = pd.DataFrame(p["hourly"])
                    h["time"] = pd.to_datetime(h["time"])
                    day = h[h["time"].dt.date == target]
                    gcol = f"wind_gusts_10m_member{mem}"
                    pcol = f"precipitation_member{mem}"
                    if gcol in day and day[gcol].notna().any():
                        alt.loc[i, "gust_max"] = float(day[gcol].max())
                        alt.loc[i, "gust_max_2d"] = max(alt.loc[i, "gust_max"], alt.loc[i, "gust_prev"])
                    if pcol in day and day[pcol].notna().any():
                        alt.loc[i, "precip"] = float(day[pcol].sum())
                scenarios.append(alt)
            source = f"{len(scenarios)} membri ICON-EPS (ensemble Open-Meteo)"
    except (RuntimeError, openmeteo.RateLimited, KeyError, IndexError, ValueError) as exc:
        p = model.predict_proba(feats)
        return p, p, f"incertitudine indisponibilă ({type(exc).__name__}); folosim doar prognoza principală"
    probs = np.column_stack([model.predict_proba(feats)] + [model.predict_proba(s) for s in scenarios])
    if mode == "historical":
        return probs.min(axis=1), probs.max(axis=1), source
    return np.nanpercentile(probs, 10, axis=1), np.nanpercentile(probs, 90, axis=1), source


def target_features(zones: list[romania.Zone], wx: pd.DataFrame, target: date) -> pd.DataFrame:
    """Features pentru ziua țintă, câte un rând pe zonă, în ordinea zonelor. O zonă fără vreme rămâne cu NaN."""
    zf = romania.zones_frame(zones)[["zone_id", "customers", "area_km2"]]
    full = make_features(wx.merge(zf, on="zone_id"), group="zone_id") if not wx.empty else pd.DataFrame()
    day = full[full["date"] == pd.Timestamp(target)] if not full.empty else pd.DataFrame(columns=["zone_id"])
    base = zf.assign(date=pd.Timestamp(target))
    keep = [c for c in day.columns if c not in ("customers", "area_km2", "date")]
    feats = base.merge(day[keep], on="zone_id", how="left")
    for f in FEATURES:
        if f not in feats:
            feats[f] = np.nan
    feats["log_customers"] = np.log10(feats["customers"].clip(lower=1))
    feats["log_density"] = np.log10((feats["customers"] / feats["area_km2"]).clip(lower=0.01))
    doy = feats["date"].dt.dayofyear
    feats["doy_sin"], feats["doy_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    return feats


def build_items(model: BModel, zones: list[romania.Zone], feats: pd.DataFrame, hourly: pd.DataFrame, target: date,
                mode: str, created: datetime, econ: dict, scenario: str, lo: np.ndarray | None = None,
                hi: np.ndarray | None = None, unc_source: str = "", wx_issues: list[str] | None = None,
                ) -> tuple[list[WorkItem], list[Series]]:
    """Regulile de decizie ale lui B, fără rețea: din features și vreme orară -> WorkItem-uri și serii."""
    feats = feats.copy()
    for f in [*model.features, *CASE_FEATURES]:  # modelul salvat și explicațiile pot cere și alte coloane
        if f not in feats:
            feats[f] = np.nan
    cols = list(model.features)
    missing = feats[cols].isna()
    filled = feats.copy()
    fill_cols = list(dict.fromkeys([*cols, *CASE_FEATURES]))
    med = feats[fill_cols].median(numeric_only=True)
    filled[fill_cols] = filled[fill_cols].fillna(med).fillna(0.0)
    # Calibrarea izotonică poate da 0 sau 1 la capete; un model nu e niciodată sigur, deci în lucrări folosim [0,005; 0,99].
    p = np.clip(model.predict_proba(filled), SCORE_MIN, SCORE_MAX)
    q = model.predict_quantiles(filled)
    lo = p.copy() if lo is None else np.clip(np.minimum(lo, p), SCORE_MIN, SCORE_MAX)
    hi = p.copy() if hi is None else np.clip(np.maximum(hi, p), SCORE_MIN, SCORE_MAX)
    ood = model.out_of_range(feats)
    factors = explain.top_factors(model, filled)
    cases = explain.similar_cases(model, filled)
    thr = model.decision_threshold
    items: list[WorkItem] = []
    series: list[Series] = []
    for i, z in enumerate(zones):
        row = feats.iloc[i]
        h = hourly[hourly["zone_id"] == z.zone_id] if not hourly.empty else hourly
        onset, onset_h = storm_onset(h, target)
        issues = list(wx_issues or [])
        issues.append("clienții pe zonă sunt o aproximare (populația orașului + restul județului împărțit egal)")
        if not 0.3 <= z.customers_per_capita_county <= 0.9:
            issues.append(f"județul {z.county} are {z.customers_per_capita_county:.2f} clienți RER pe locuitor (neobișnuit):"
                          " zonele de rețea RER nu urmează exact granițele județului; folosit ca atare")
        miss_cols = [c for c in cols if missing.iloc[i][c]]
        abstain_reasons = []
        if miss_cols:
            issues.append(f"vreme lipsă pentru {', '.join(miss_cols)}: completată cu mediana zonelor")
            if {"gust_max", "precip"} & set(miss_cols):
                abstain_reasons.append("lipsesc rafala sau ploaia pentru ziua țintă")
        if ood.iloc[i]:
            zone_ood = [f for f in ood.iloc[i] if f in ZONE_FEATURES]
            wx_ood = [f for f in ood.iloc[i] if f not in ZONE_FEATURES]
            issues.append(f"în afara datelor de antrenare: {', '.join(ood.iloc[i])}")
            if wx_ood:
                abstain_reasons.append("vremea iese din ce a văzut modelul la antrenare (" + ", ".join(wx_ood) + ")")
            elif zone_ood and hazardous(row):
                abstain_reasons.append("zona e mai mare sau mai densă decât orice comitat din antrenare, iar vremea e "
                                       "periculoasă (" + ", ".join(zone_ood) + ")")
            else:
                issues.append("zona iese din datele de antrenare, dar vremea e liniștită: riscul rămâne mic, fără decizie la om")
        width = float(hi[i] - lo[i])
        if width >= DISAGREE_WIDTH and lo[i] < thr <= hi[i]:
            abstain_reasons.append(f"sursele meteo nu se pun de acord: riscul e între {lo[i]:.0%} și {hi[i]:.0%}")
        abstain = bool(abstain_reasons)
        confidence = "low" if abstain or width >= DISAGREE_WIDTH else ("medium" if width >= 0.15 or p[i] >= 0.5 else "high")
        if abstain:
            action = "human_review"
        elif p[i] >= thr:
            action = "preposition_crew"
        else:
            action = "no_action"

        cust = np.round(q[i] * z.customers).astype(int)
        # câți clienți poate ajuta o echipă într-o tură: dacă planificatorul pune cheia în economics.yaml, o folosim
        helped = min(int(cust[1]), int(econ.get("customers_helped_per_crew_shift") or cust[1]))
        value_if_true = round(float(helped * econ["restoration_speedup_hours"] * econ["cost_per_customer_hour_lei"]), 2)
        score = round(float(p[i]), 4)
        wid = f"B-{target:%Y%m%d}-{z.zone_id}"
        tw_start = onset  # planificatorul cere echipa pe poziție cu 60 de minute înainte de start
        tw_end = onset + timedelta(hours=6)
        gust = row.get("gust_max")
        item = WorkItem(
            work_item_id=wid,
            source="B",
            kind="storm_prepositioning",
            asset_id=z.zone_id,
            asset_type="zone",
            location=Location(lat=z.lat, lon=z.lon, zone_id=z.zone_id, county=z.county, label=f"{z.label_ro} ({z.county})"),
            target_date=target,
            time_window=TimeWindow(start=tw_start, end=tw_end),
            prediction=Prediction(
                model_id=MODEL_ID,
                model_version=model.version,
                prediction_id=str(uuid.uuid4()),
                label="outage_risk",
                score=score,
                interval_low=round(float(lo[i]), 4),
                interval_high=round(float(hi[i]), 4),
                point_estimate=float(cust[1]),
                point_unit="clienți fără curent la vârf, dacă se produce avaria (P50)",
                point_interval=(float(cust[0]), float(cust[2])),
                confidence=confidence,
                abstain=abstain,
                abstain_reason="; ".join(abstain_reasons) if abstain else None,
            ),
            impact=Impact(
                expected_value_lei=round(score * value_if_true, 2),  # exact scor × valoare (verificat de carantină)
                value_if_true_lei=value_if_true,
                customers_affected=int(cust[1]),
                urgency_hours=max(round((onset - created).total_seconds() / 3600, 1), 1.0),
                safety_flag=bool(pd.notna(gust) and gust >= SAFETY_GUST_KMH),
                assumptions_ref="storm",
            ),
            effort=Effort(duration_min=480, crew_skill="mv_grid" if cust[1] >= 2000 else "lv_grid", crew_size=3),
            explanation=Explanation(
                top_factors=factors[i],
                similar_cases=cases[i],
                summary_ro=explain.summary_ro(float(p[i]), row, onset_h, cases[i], abstain, int(cust[1]), factors[i]),
            ),
            data_quality=DataQuality(
                missing_ratio=round(float(missing.iloc[i].mean()), 3),
                input_issues=issues,
                synthetic=False,
                data_sources=DATA_SOURCES,
            ),
            recommended_action=action,
            created_at=created,
            extra={
                "series_ref": f"outputs/series/{scenario}/{wid}.json",
                "region": z.region,
                "zone_customers": z.customers,
                "storm_onset": onset.isoformat(),
                "gust_max_kmh": None if pd.isna(gust) else round(float(gust), 1),
                "precip_48h_mm": None if pd.isna(row.get("precip_48h")) else round(float(row["precip_48h"]), 1),
                "pct_out_p10_p50_p90": [round(float(x), 4) for x in q[i]],
                "decision_threshold": round(thr, 3),
                "weather_mode": mode,
                "uncertainty_source": unc_source,
                "validation_note": VALIDATION_NOTE,
            },
        )
        items.append(item)
        series.append(make_series(wid, z, h, target, onset, tw_start))
    return items, series


def run(scenario: str, date: str | None = None) -> Path:
    target, mode = resolve(scenario, date)
    if not MODEL_PATH.exists():
        raise SystemExit(f"Lipsește modelul {MODEL_PATH}. Rulează `uv run python -m cyberpunks.b_furtuna.evaluate`.")
    model = BModel.load()
    econ = config.load("economics")["storm"]
    zones = romania.load_zones()
    created = decision_time(target, mode)

    openmeteo.STALE_NOTES.clear()
    try:
        wx, wx_issues = romania.weather_daily(zones, target, mode)
        hourly = romania.weather_hourly(zones, target, mode)
    except (httpx.HTTPError, RuntimeError, OSError, ValueError, KeyError) as exc:  # rețea, cotă (429), format
        wx, hourly = pd.DataFrame(), pd.DataFrame()
        wx_issues = [f"vremea indisponibilă ({type(exc).__name__}) și nicio copie salvată: toate zonele merg la om"]
    feats = target_features(zones, wx, target)
    if wx.empty:
        lo = hi = None
        unc_source = "fără vreme: incertitudinea nu se poate estima"
    else:
        lo, hi, unc_source = uncertainty(model, zones, feats, target, mode)
    wx_issues = list(wx_issues) + sorted(set(openmeteo.STALE_NOTES))
    items, series = build_items(model, zones, feats, hourly, target, mode, created, econ, scenario, lo, hi,
                                unc_source, wx_issues)

    out_path = work_items_path(scenario, "B")
    series_dir = OUTPUTS / "series" / scenario
    out_path.parent.mkdir(parents=True, exist_ok=True)
    series_dir.mkdir(parents=True, exist_ok=True)
    for s in series:
        (series_dir / f"{s.work_item_id}.json").write_text(s.model_dump_json(indent=1) + "\n", encoding="utf-8")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.writelines(it.model_dump_json() + "\n" for it in items)
    n_pre = sum(it.recommended_action == "preposition_crew" for it in items)
    n_hr = sum(it.recommended_action == "human_review" for it in items)
    print(f"{scenario} {target} ({mode}): {len(items)} zone, {n_pre} echipe recomandate, {n_hr} la om -> {out_path}")
    return out_path


def make_series(wid: str, z: romania.Zone, h: pd.DataFrame, target: date, onset: datetime,
                tw_start: datetime) -> Series:
    window = h if h.empty else h[(h["time"] >= pd.Timestamp(target - timedelta(days=1)) + pd.Timedelta(hours=12))
                                 & (h["time"] < pd.Timestamp(target + timedelta(days=1)) + pd.Timedelta(hours=6))]
    points = []
    for _, r in window.iterrows():
        t = pd.Timestamp(r["time"]).to_pydatetime().replace(tzinfo=TZ)
        g = None if pd.isna(r["wind_gusts_10m"]) else float(r["wind_gusts_10m"])
        pr = 0.0 if pd.isna(r["precipitation"]) else float(r["precipitation"])
        flag = f"ploaie {pr:.0f} mm" if pr >= ONSET_PRECIP_MM else None
        points.append(SeriesPoint(t=t, value=g, flag=flag))
    if not points:
        points = [SeriesPoint(t=onset, value=None, flag="gol")]
    s = Series(
        work_item_id=wid,
        source="B",
        title_ro=f"Rafale de vânt pe ore, {z.label_ro} ({z.county})",
        unit="km/h",
        points=points,
        thresholds={"rafala_inceput_furtuna_kmh": ONSET_GUST_KMH, "rafala_periculoasa_kmh": SAFETY_GUST_KMH},
        annotations=[
            SeriesAnnotation(t=tw_start - timedelta(hours=1), label_ro="echipa pe poziție (cu o oră înainte)"),
            SeriesAnnotation(t=onset, label_ro="începutul furtunii (estimat)"),
        ],
        synthetic=False,
    )
    return s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenario", default="demo-vara")
    ap.add_argument("--date", default=None)
    args = ap.parse_args(argv)
    path = run(args.scenario, args.date)
    print(json.dumps({"written": str(path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
