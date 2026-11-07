"""Lucrările C pentru o zi: ce posturi pot trece de 1,10 pu, cât de sigur, ce recomandăm și de ce.

    uv run python -m cyberpunks.c_prosumatori.predict --scenario demo-vara
    uv run python -m cyberpunks.c_prosumatori.predict --scenario maine --date 2026-11-09

Scrie `outputs/work_items/<scenariu>/C.jsonl` (contractul WorkItem), `outputs/series/<scenariu>/<id>.json`
(contractul Series) și `outputs/work_items/<scenariu>/C_summary.json` (rezumatul zilei: câte posturi, de ce).
Funcția importabilă: `run(scenario, date) -> Path`.
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import actions, explain, profiles, remedies, weather
from cyberpunks.c_prosumatori import features as F
from cyberpunks.c_prosumatori import train as T
from cyberpunks.c_prosumatori.population import BBOX
from cyberpunks.common.config import load
from cyberpunks.common.contracts import RemedyOption, Series, WorkItem
from cyberpunks.common.paths import DATA_PROCESSED, OUTPUTS, work_items_path

TZ = ZoneInfo(profiles.TZ)
DEMO_VARA_FALLBACK = "2025-07-08"  # data aleasă de firul B (status B, 12:58): caniculă și cer senin în București-Ilfov
LIMIT = actions.LIMIT_PU
ARCHIVE_END = date(2026, 11, 6)
CONTEXT_RO = {  # ANRE, aug. 2026 (documentul de research din 7 nov., memory/12-probleme-reale-ppc-2026.md)
    "Ilfov": "Ilfov e primul județ din țară la prosumatori: 21.647, cu 303,81 MW (ANRE, aug. 2026).",
    "București": "București are 8.307 prosumatori, cu 134,94 MW (ANRE, aug. 2026); cei mai mulți sunt la case, puțini la blocuri.",
}
SOURCES_ARCHIVE = "Open-Meteo Historical Weather (ERA5), CC BY 4.0"
SOURCES_FORECAST = "Open-Meteo Forecast, CC BY 4.0"
BASE_SOURCES = [
    "SimBench 1.6.3 (ODbL): topologii JT, posturi SINTETICE",
    "OpenStreetMap (ODbL, © OpenStreetMap contributors): poziții de posturi",
    "pandapower 3.5.6: etichetele de antrenare (circulație de puteri)",
]
OOD_KEYS = ["pv_kw_per_kva", "sens_pv_pu", "r_max_ohm", "max_path_km", "v0_est", "kva", "pv_kw", "battery_pv_share"]


# ------------------------------------------------------------------------------------------------
# intrări: data, vremea, registrul posturilor
# ------------------------------------------------------------------------------------------------


def resolve_date(scenario: str, d: str | None) -> date:
    if d:
        return date.fromisoformat(d)
    sc = load("scenarios")["scenarios"].get(scenario, {})
    v = str(sc.get("date", ""))
    if v == "auto_tomorrow" or scenario == "maine":
        return datetime.now(TZ).date() + timedelta(days=1)
    if v and not v.startswith("TBD"):
        return date.fromisoformat(v)
    return date.fromisoformat(DEMO_VARA_FALLBACK)


def weather_for_day(d: date) -> tuple[pd.DataFrame, str, list[str]]:
    """Vremea orară pentru ziua locală d (UTC, ora care se încheie), sursa și problemele găsite."""
    start = pd.Timestamp(d, tz=profiles.TZ).tz_convert("UTC") + pd.Timedelta(hours=1)
    idx = pd.date_range(start, periods=24, freq="h")
    if d <= ARCHIVE_END:
        wx, src = weather.archive(), SOURCES_ARCHIVE
    else:
        p = weather.download_forecast((d - timedelta(days=1)).isoformat(), (d + timedelta(days=1)).isoformat(), refresh=True)
        wx, src = weather.read_openmeteo(p), SOURCES_FORECAST
    wx = wx.reindex(idx)
    issues = []
    for c in ("gti", "ghi", "dif", "temp", "cloud"):
        bad = wx[c].isna() | (wx[c] < (-50 if c == "temp" else 0)) | (wx[c] > (60 if c == "temp" else 1500))
        if bad.any():
            issues.append(f"meteo: {int(bad.sum())} ore lipsă sau imposibile la {c}, completate prin interpolare")
            wx.loc[bad, c] = np.nan
            wx[c] = wx[c].interpolate(limit_direction="both").fillna(0.0)
    return wx, src, issues


def registry() -> pd.DataFrame:
    from cyberpunks.c_prosumatori.posts import load_posts

    return load_posts()


def check_post(r: pd.Series) -> tuple[list[str], list[str]]:
    """(probleme care blochează predicția, probleme reparate). Intrări greșite: puteri negative, kVA zero etc."""
    block, fixed = [], []
    for k in F.STATIC:
        v = r.get(k)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            if k in ("battery_kwh", "battery_pv_share"):
                fixed.append(f"{k} lipsă, considerat 0")
            else:
                block.append(f"{k} lipsă")
    if not (r.get("kva", 0) and r["kva"] > 0):
        block.append(f"puterea transformatorului e {r.get('kva')} kVA")
    if r.get("pv_kw", 0) < 0:
        block.append(f"puterea instalată negativă ({r['pv_kw']} kW)")
    if r.get("n_prosumers", 0) > r.get("n_customers", 0):
        block.append("mai mulți prosumatori decât clienți")
    if r.get("tap_pos", 0) not in (-2, -1, 0, 1, 2):
        block.append(f"priză imposibilă ({r.get('tap_pos')})")
    if not (0.9 <= r.get("v0_est", 1.0) <= 1.15):
        block.append(f"tensiune estimată imposibilă ({r.get('v0_est')} pu)")
    if not (BBOX[0] <= r.get("lat", 0) <= BBOX[2] and BBOX[1] <= r.get("lon", 0) <= BBOX[3]):
        block.append("coordonate în afara zonei București-Ilfov")
    return block, fixed


def ood_reasons(r: pd.Series, ranges: dict) -> list[str]:
    out = []
    for k in OOD_KEYS:
        lo, hi = ranges[k]
        span = hi - lo
        v = r[k]
        if v > hi + 0.1 * span or v < lo - 0.1 * span:
            out.append(f"{F.FEATURE_LABELS_RO.get(k, k)} = {v:.3g}, antrenat pe {lo:.3g}-{hi:.3g}")
    return out


# ------------------------------------------------------------------------------------------------
# predicția
# ------------------------------------------------------------------------------------------------


def _weather_scenarios(wx: pd.DataFrame, forecast: bool) -> list[tuple[float, pd.DataFrame]]:
    """Pentru prognoză: trei variante de radiație (jos, mijloc, sus), ponderate 1/4, 1/2, 1/4.
    Lățimea crește cu norii (IPOTEZĂ calibrată pe MAE-ul prognozelor arhivate Open-Meteo: 38 W/m² în iulie)."""
    if not forecast:
        return [(1.0, wx)]
    noon = wx.tz_convert(profiles.TZ).between_time("10:00", "16:00")
    u = 0.10 + 0.30 * float(noon["cloud"].mean()) / 100.0
    out = []
    for w, f in ((0.25, 1 - u), (0.5, 1.0), (0.25, 1 + u)):
        v = wx.copy()
        v[["gti", "ghi", "dif"]] = v[["gti", "ghi", "dif"]] * f
        out.append((w, v))
    return out


def predict_day(bundle, reg: pd.DataFrame, wx: pd.DataFrame, forecast: bool) -> tuple[pd.DataFrame, dict]:
    variants = []
    for w, v in _weather_scenarios(wx, forecast):
        hw = F.hourly_weather(v)
        X = F.daily_features(reg, hw)
        variants.append((w, X, bundle.daily.predict(X)))
    X = variants[len(variants) // 2][1].copy()
    pm = variants[len(variants) // 2][2]
    p = sum(w * pr["p_exceed"] for w, _, pr in variants)
    X["p_exceed"] = p
    X["p_low"] = np.min([pr["p_exceed"] for _, _, pr in variants], axis=0)
    X["p_high"] = np.max([pr["p_exceed"] for _, _, pr in variants], axis=0)
    X["q10"] = variants[0][2]["q10"]
    X["q50"] = pm["q50"]
    X["q90"] = variants[-1][2]["q90"]
    X["lost_kwh"] = pm["lost_kwh"]
    X["raw_p"] = pm["raw_p"]
    hw_mid = F.hourly_weather(wx)
    noon = hw_mid[(hw_mid.hour >= 10) & (hw_mid.hour < 16)]
    info = {
        "gti_max": float(hw_mid["gti"].max()),
        "temp_noon": float(noon["temp"].mean()),
        "cloud_noon": float(noon["cloud"].mean()),
        "cloud_std_noon": float(noon["cloud"].std()),
        "free_day": bool(hw_mid["free_day"].iloc[12]),
    }
    return X, info


def tap_counterfactual(bundle, reg: pd.DataFrame, wx: pd.DataFrame) -> np.ndarray:
    """Tensiunea P50 estimată dacă priza urcă o treaptă (tensiunea pe JT coboară cu 2,5%)."""
    r2 = reg.copy()
    r2["tap_pos"] = np.clip(r2["tap_pos"] + 1, -2, 3)
    r2["v0_est"] = r2["vm_mv_est"] / (1 + 0.025 * r2["tap_pos"])
    X = F.daily_features(r2, F.hourly_weather(wx))
    return bundle.daily.predict(X)["q50"]


def hourly_series(bundle, st: pd.Series, wx: pd.DataFrame) -> pd.DataFrame:
    hw = F.hourly_weather(wx)
    X = F.hourly_features(st, hw)
    pr = bundle.hourly.predict(X)
    out = pd.DataFrame({"q10": pr["q10"], "q50": pr["q50"], "q90": pr["q90"], "hour": hw["hour"].to_numpy()}, index=wx.index)
    return out


def simulated_truth(post_id: str, idx: pd.DatetimeIndex) -> np.ndarray | None:
    p = DATA_PROCESSED / "C" / "population" / "hourly" / f"{post_id}.parquet"
    if not p.exists():
        return None
    h = pd.read_parquet(p, columns=["vmax"])
    v = h["vmax"].reindex(idx)
    return None if v.isna().all() else v.to_numpy()


def _window(series: pd.DataFrame) -> tuple[int, int]:
    risky = series[(series["q90"] > LIMIT) | (series["q50"] > LIMIT - 0.01)]
    if risky.empty:
        return 11, 15
    h0, h1 = int(risky["hour"].min()), int(risky["hour"].max()) + 1
    return h0, max(h1, h0 + 1)


def _window_end(d: date, h1: int) -> datetime:
    """Sfârșitul ferestrei; ora 24 înseamnă miezul nopții de după (nu 23:59)."""
    if h1 >= 24:
        n = d + timedelta(days=1)
        return datetime(n.year, n.month, n.day, 0, 0, tzinfo=TZ)
    return datetime(d.year, d.month, d.day, h1, 0, tzinfo=TZ)


def _confidence(p: float, width: float, abstain: bool) -> str:
    if abstain:
        return "low"
    if (p >= 0.8 or p <= 0.2) and width <= 0.04:
        return "high"
    if width <= 0.07:
        return "medium"
    return "low"


def ladder_extra(L) -> dict:
    """Scara de soluții în `extra`: opțiunile (contractul RemedyOption), P90 de pornire, alegerea și motivul."""
    return {
        "remedy_options": L.options,
        "ladder_base_p90_pu": round(L.p90_start, 4),
        "ladder_model_p90_pu": round(L.p90_model, 4),
        "phase_unbalance_pu": {"inainte": round(L.unbalance["before"], 4), "dupa": round(L.unbalance["after"], 4)},
        "ladder_choice": L.choice,
        "ladder_reason_ro": L.reason_ro,
        "ladder_reaches_target": L.reaches_target,
        "risk_hours": [remedies.fmt_window(L.hours)],
        "inverter_trips_base": round(L.base_trips, 1),
    }


def tap_extra(st: pd.Series, d: date, created: datetime) -> dict:
    """Preavizul întreruperii (Ord. ANRE 46/2021, art. 12): cea mai devreme zi pentru priză și anunțul către clienți."""
    eco = actions.economics()
    earliest = actions.add_working_days(created.date(), eco["planned_notice_working_days_lv"])
    when = max(earliest, d)
    return {
        "planned_outage_notified": False,
        "earliest_tap_date": when.isoformat(),
        "tap_cost_lei": round(actions.tap_cost_lei(int(st["n_customers"]), eco), 2),
        "outage_notice_ro": actions.outage_notice(st["post_id"], when),
    }


def _summary(dec: actions.Decision, r: pd.Series, d: date, h0: int, h1: int, factors: list[dict]) -> str:
    when = f"Pe {d.day} {explain.MONTHS_RO[d.month - 1]}, între {h0}:00 și {h1}:00,"
    core = (f"{when} tensiunea maximă estimată e {explain.fmt(r['q50'], 3)} pu (între {explain.fmt(r['q10'], 3)} și "
            f"{explain.fmt(r['q90'], 3)}), față de limita de 1,10; probabilitatea depășirii {r['p_exceed'] * 100:.0f}%.")
    why = " Motive: " + "; ".join(f["label_ro"] for f in factors[:2]) + "." if factors else ""
    return core + why + " " + dec.reason_ro


def run(scenario: str, date_str: str | None = None) -> Path:
    """Scrie lucrările C pentru scenariu și dată. Întoarce calea către C.jsonl."""
    d = resolve_date(scenario, date_str)
    bundle = T.load_bundle()
    reg = registry().reset_index(drop=True)
    wx, wx_src, wx_issues = weather_for_day(d)
    forecast = wx_src == SOURCES_FORECAST
    X, info = predict_day(bundle, reg, wx, forecast)
    X = X.set_index("post_id").loc[reg["post_id"]].reset_index()
    after_tap = tap_counterfactual(bundle, reg, wx)
    contrib = explain.shap_groups(bundle.daily.quantile_models[0.5], X[bundle.daily.features])
    sim = None
    now = datetime.now(TZ).replace(microsecond=0)
    created = now if d > now.date() else datetime(d.year, d.month, d.day, 6, 0, tzinfo=TZ) - timedelta(days=1)
    weather_uncertain = forecast and (20 <= info["cloud_noon"] <= 80 or info["cloud_std_noon"] > 25)
    out_items, counts, offers, day = [], {}, [], None
    series_dir = OUTPUTS / "series" / scenario
    series_dir.mkdir(parents=True, exist_ok=True)
    for i, r in X.iterrows():
        st = reg.iloc[i]
        block, fixed = check_post(st)
        ood = [] if block else ood_reasons(st, bundle.ood_ranges)
        dec = actions.decide(
            p=float(r["p_exceed"]), q10=float(r["q10"]), q50=float(r["q50"]), q90=float(r["q90"]), lost_kwh=float(r["lost_kwh"]),
            n_prosumers=int(st["n_prosumers"]), n_customers=int(st["n_customers"]), tap_pos=int(st["tap_pos"]), q50_after_tap=float(after_tap[i]), target=d,
            issues_block=block, ood_reasons=ood, weather_uncertain=weather_uncertain,
        )
        if dec is None:
            continue
        ladder = None
        if actions.needs_ladder(dec, float(r["q90"])):
            if day is None:
                day = remedies.day_inputs(d, wx)
            ladder = remedies.build_ladder(st["post_id"], day, float(r["q90"]), int(st["n_customers"]), actions.season_horizon_days(d))
            dec = actions.from_ladder(dec, ladder)
            for o in ladder.options:
                RemedyOption.model_validate(o)
            if not ladder.battery_offers.empty:
                offers.append(ladder.battery_offers.assign(target_date=d.isoformat()))
        counts[dec.action] = counts.get(dec.action, 0) + 1
        ser = hourly_series(bundle, st, wx)
        h0, h1 = _window(ser)
        wid = f"C-{d:%Y%m%d}-{st['post_id']}"
        if sim is None:
            sim = explain.SimilarCases(explain.similar_reference())
        factors = explain.top_factors(contrib.iloc[i], r, d)
        p = float(np.clip(r["p_exceed"], 0.0, 1.0))
        p_lo, p_hi = (float(r["p_low"]), float(r["p_high"])) if forecast else (None, None)
        if p_lo is not None:
            p_lo, p_hi = min(p_lo, p), max(p_hi, p)
        win_start = datetime(d.year, d.month, d.day, h0, 0, tzinfo=TZ)
        urgency = max((win_start - created).total_seconds() / 3600.0, 1.0)
        item = {
            "work_item_id": wid,
            "source": "C",
            "kind": "voltage_mitigation",
            "asset_id": st["post_id"],
            "asset_type": "transformer_post",
            "location": {"lat": float(st["lat"]), "lon": float(st["lon"]), "zone_id": st["zone_id"], "county": st["county"], "label": st["label"]},
            "target_date": d.isoformat(),
            "time_window": {"start": win_start.isoformat(), "end": _window_end(d, h1).isoformat()},
            "prediction": {
                "model_id": "c-surrogate",
                "model_version": bundle.version,
                "prediction_id": str(uuid.uuid4()),
                "label": "overvoltage",
                "score": round(p, 4),
                "interval_low": None if p_lo is None else round(p_lo, 4),
                "interval_high": None if p_hi is None else round(p_hi, 4),
                "point_estimate": round(float(r["q50"]), 4),
                "point_unit": "tensiune maximă pe post (pu)",
                "point_interval": [round(float(r["q10"]), 4), round(float(r["q90"]), 4)],
                "confidence": _confidence(p, float(r["q90"] - r["q10"]), dec.abstain),
                "abstain": dec.abstain,
                "abstain_reason": dec.abstain_reason,
            },
            "impact": {
                # exact scor × valoare, cu valorile scrise (carantina planificatorului verifică abaterea de 2%)
                "expected_value_lei": round(round(p, 4) * round(dec.value_if_true_lei, 2), 4),
                "value_if_true_lei": round(dec.value_if_true_lei, 2),
                "customers_affected": int(st["n_customers"]),
                "urgency_hours": round(urgency, 1),
                "safety_flag": bool(r["q50"] > 1.15),
                "assumptions_ref": "voltage",
            },
            "effort": {"duration_min": dec.duration_min, "crew_skill": "lv_grid", "crew_size": dec.crew_size, "requires_planned_outage": dec.requires_outage},
            "explanation": {"top_factors": factors, "similar_cases": sim.query(r), "summary_ro": ""},
            "data_quality": {
                "missing_ratio": 0.0,
                "input_issues": [*wx_issues, *fixed, *block],
                "synthetic": True,
                "data_sources": [*BASE_SOURCES, wx_src],
            },
            "recommended_action": dec.action,
            "created_at": created.isoformat(),
            "extra": {
                "rule_id": dec.rule_id,
                "series_ref": f"outputs/series/{scenario}/{wid}.json",
                "lost_pv_kwh_pred": round(float(r["lost_kwh"]), 1),
                "vmax_after_tap_pu": round(float(after_tap[i]), 4),
                "investment_flag": dec.investment_flag,
                "kva": float(st["kva"]),
                "pv_kw": float(st["pv_kw"]),
                "n_prosumers": int(st["n_prosumers"]),
                "tap_pos": int(st["tap_pos"]),
                "position_source": st.get("position_source"),
                "customer_message_ro": actions.customer_message(d, int(st["n_prosumers"]), (h0, h1))
                if dec.action in ("notify_customers", "adjust_tap") and int(st["n_prosumers"]) > 0 else None,
                "season_horizon_days": actions.season_horizon_days(d),
                "context_ro": CONTEXT_RO.get(st["county"]),
                **(tap_extra(st, d, created) if dec.action == "adjust_tap" or (ladder and "adjust_tap" in ladder.choice) else {}),
                **(ladder_extra(ladder) if ladder else {}),
            },
        }
        item["explanation"]["summary_ro"] = _summary(dec, r, d, h0, h1, factors)
        WorkItem.model_validate(item)
        out_items.append(item)
        truth = simulated_truth(st["post_id"], wx.index)
        loc_idx = wx.index.tz_convert(profiles.TZ) - pd.Timedelta(hours=1)
        pts = []
        for k, (t, s) in enumerate(zip(loc_idx, ser.itertuples(), strict=True)):
            pts.append({
                "t": t.isoformat(),
                "value": None if truth is None or np.isnan(truth[k]) else round(float(truth[k]), 4),
                "expected": round(float(s.q50), 4),
                "low": round(float(s.q10), 4),
                "high": round(float(s.q90), 4),
                "flag": "peste_limita" if s.q50 > LIMIT else ("risc" if s.q90 > LIMIT else None),
            })
        peak = ser["q50"].idxmax()
        series = {
            "work_item_id": wid,
            "source": "C",
            "title_ro": f"Tensiunea maximă pe {st['post_id']}, oră cu oră (P10-P90)" + (" și simularea fizică" if truth is not None else ""),
            "unit": "pu",
            "points": pts,
            "thresholds": {"limita_tensiune_pu": LIMIT, "limita_calitate_95_pu": 1.05},
            "annotations": [{"t": (peak.tz_convert(profiles.TZ) - pd.Timedelta(hours=1)).isoformat(),
                             "label_ro": f"vârful estimat: {explain.fmt(float(ser.loc[peak, 'q50']), 3)} pu"}],
            "synthetic": True,
        }
        Series.model_validate(series)
        (series_dir / f"{wid}.json").write_text(json.dumps(series, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    path = work_items_path(scenario, "C")
    path.parent.mkdir(parents=True, exist_ok=True)
    out_items.sort(key=lambda it: -it["impact"]["expected_value_lei"] - 1000 * it["prediction"]["score"])
    path.write_text("".join(json.dumps(it, ensure_ascii=False) + "\n" for it in out_items), encoding="utf-8")
    month = explain.MONTHS_RO[d.month - 1]
    reason = (f"{len(out_items)} posturi din {len(reg)} au lucrări. Radiația maximă pe panou: {info['gti_max']:.0f} W/m², "
              f"{info['temp_noon']:.0f} °C la prânz, nori {info['cloud_noon']:.0f}%.")
    reason += " " + CONTEXT_RO["Ilfov"]
    risky = int((X["p_exceed"] >= 0.5).sum())
    reason += f" {risky} posturi au probabilitate de depășire peste 50%."
    if len(out_items) <= 3:
        reason += (f" Puține lucrări: în {month} soarele urcă puțin pe cer și producția de la prânz rămâne sub pragul la care "
                   "tensiunea trece de 1,10 pu.") if info["gti_max"] < 650 else " Puține lucrări: consumul acoperă producția."
    elif d.month in (11, 12, 1, 2) and info["gti_max"] >= 600:
        reason += (f" Deși e {month}, cerul e senin și panourile reci produc aproape cât vara, iar "
                   + ("în zi liberă consumul de la prânz e mic." if info["free_day"] else "consumul de la prânz nu acoperă producția.")
                   + " În afara sezonului, o vizită pentru priză nu se justifică: agentul trimite mesaje și urmărește.")
    summary = {
        "scenario": scenario, "date": d.isoformat(), "posts": len(reg), "work_items": len(out_items), "by_action": counts,
        "weather_source": wx_src, "weather": info, "weather_issues": wx_issues, "model_version": bundle.version,
        "reason_ro": reason, "synthetic": True, "created_at": created.isoformat(),
    }
    (path.parent / "C_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if offers:
        allo = pd.concat(offers, ignore_index=True)
        allo.to_csv(path.parent / "C_battery_offers.csv", index=False)
        summary["battery_offers"] = len(allo)
        (path.parent / "C_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="demo-vara")
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    p = run(a.scenario, a.date)
    s = json.loads((p.parent / "C_summary.json").read_text())
    print(p, "\n", s["reason_ro"], s["by_action"])
