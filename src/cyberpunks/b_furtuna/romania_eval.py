"""Testul modelului B pe avarii reale din România: arhiva Powercut (feed Rețele Electrice), 30 de zile.

    DYLD_LIBRARY_PATH=.venv/lib/python3.12/site-packages/sklearn/.dylibs \\
        uv run python -m cyberpunks.b_furtuna.romania_eval

Intrări (locale, ignorate de git, vezi `memory/14-date-furtuni-eden.md`):
- `data/raw/B/romania/surse/powercut_archive.json`: rânduri `[lat, lon, planificat, clienți, țară, start, sfârșit]`,
  minute față de `from` (Unix UTC); `sfârșit = -1` înseamnă încă deschis.
- vremea zilnică Open-Meteo, aceeași sursă ca la antrenare (archive) și, separat, Historical Forecast.

Eticheta, ca în SUA: într-o zi locală, vârful clienților fără curent în același timp ≥ 1% din clienții zonei.
Vârful se calculează pe o grilă de 10 minute din intervalele incidentelor neplanificate cu clienți > 0.
Fiecare incident intră în zona cu centrul cel mai apropiat (APROXIMARE: nu avem granițele zonelor).

Scrie `reports/B/romania_eval.json` și `reports/B/romania_eval.md`. Date reale, nu sintetice.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from cyberpunks.b_furtuna import openmeteo, romania
from cyberpunks.b_furtuna.features import FEATURES, clean_weather
from cyberpunks.b_furtuna.model import BModel, best_f1_threshold
from cyberpunks.b_furtuna.predict import target_features
from cyberpunks.common.paths import DATA_PROCESSED, DATA_RAW, REPORTS

POWERCUT = DATA_RAW / "B" / "romania" / "surse" / "powercut_archive.json"
OUT_JSON = REPORTS / "B" / "romania_eval.json"
OUT_MD = REPORTS / "B" / "romania_eval.md"
ROWS_CSV = DATA_PROCESSED / "B" / "romania_eval_rows.csv"  # local: derivat din Powercut, licență nespecificată
TZ = "Europe/Bucharest"
STEP_MIN = 10
GUST_RULE_KMH = 70.0
N_BOOT = 2000


# ---------------------------------------------------------------------------------------------
# Etichetele din Powercut
# ---------------------------------------------------------------------------------------------


def load_outages() -> tuple[pd.DataFrame, dict]:
    raw = json.loads(POWERCUT.read_text(encoding="utf-8"))
    ro = raw["countries"].index("RO")
    df = pd.DataFrame(raw["outages"], columns=["lat", "lon", "planned", "customers", "country", "start", "end"])
    df = df[df["country"] == ro]
    info = {"rows_ro": len(df), "planned": int((df["planned"] == 1).sum())}
    df = df[df["planned"] == 0]
    info["unplanned"] = len(df)
    info["unplanned_customers_pos"] = int((df["customers"] > 0).sum())
    df = df[df["customers"] > 0].copy()
    total_min = (raw["to"] - raw["from"]) // 60
    info["open_at_snapshot"] = int((df["end"] == -1).sum())
    df.loc[df["end"] == -1, "end"] = total_min
    df["dur_h"] = (df["end"] - df["start"]) / 60
    info["window_utc"] = [datetime.fromtimestamp(raw["from"], UTC).isoformat(),
                          datetime.fromtimestamp(raw["to"], UTC).isoformat()]
    info["collection_since_utc"] = datetime.fromtimestamp(raw["since"], UTC).isoformat()
    return df.reset_index(drop=True), {**info, "_from": raw["from"], "_to": raw["to"], "_since": raw["since"]}


def assign_zones(df: pd.DataFrame, zones: list[romania.Zone]) -> pd.DataFrame:
    zlat = np.array([z.lat for z in zones])
    zlon = np.array([z.lon for z in zones])
    dlat = np.radians(df["lat"].to_numpy()[:, None] - zlat[None, :])
    dlon = np.radians(df["lon"].to_numpy()[:, None] - zlon[None, :])
    a = (np.sin(dlat / 2) ** 2 + np.cos(np.radians(df["lat"].to_numpy()))[:, None] * np.cos(np.radians(zlat))[None, :]
         * np.sin(dlon / 2) ** 2)
    km = 2 * 6371 * np.arcsin(np.sqrt(a))
    i = km.argmin(axis=1)
    return df.assign(zone_id=[zones[k].zone_id for k in i], county_code=[zones[k].county_code for k in i],
                     dist_km=km[np.arange(len(df)), i])


def daily_peaks(df: pd.DataFrame, t0_unix: int, total_min: int, key: str, max_dur_h: float | None = None) -> pd.DataFrame:
    """Vârful clienților simultan fără curent pe (cheie, zi locală), din intervalele incidentelor."""
    n = total_min // STEP_MIN + 2
    grid_t = pd.to_datetime(t0_unix + np.arange(n) * STEP_MIN * 60, unit="s", utc=True).tz_convert(TZ)
    day = grid_t.tz_localize(None).normalize()
    out = []
    for k, g in df.groupby(key):
        end = g["end"].to_numpy()
        if max_dur_h is not None:
            end = np.minimum(end, g["start"].to_numpy() + max_dur_h * 60)
        acc = np.zeros(n + 1)
        np.add.at(acc, (g["start"].to_numpy() // STEP_MIN).astype(int), g["customers"].to_numpy())
        np.add.at(acc, (np.ceil(end / STEP_MIN)).astype(int), -g["customers"].to_numpy())
        conc = np.cumsum(acc)[:n]
        s = pd.Series(conc).groupby(day).max()
        out.append(pd.DataFrame({key: k, "date": s.index, "out_max": s.to_numpy()}))
    return pd.concat(out, ignore_index=True)


def daily_new(df: pd.DataFrame, t0_unix: int, key: str) -> pd.DataFrame:
    """Clienții din incidentele care ÎNCEP în ziua locală (nu depinde de sfârșiturile întârziate din feed)."""
    day = pd.to_datetime(t0_unix + df["start"].to_numpy() * 60, unit="s", utc=True).tz_convert(TZ).tz_localize(None)
    g = df.assign(date=day.normalize()).groupby([key, "date"])["customers"].sum()
    return g.rename("out_max").reset_index()


# ---------------------------------------------------------------------------------------------
# Metrici
# ---------------------------------------------------------------------------------------------


def ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    return float(sum(abs(p[idx == b].mean() - y[idx == b].mean()) * (idx == b).mean() for b in range(bins)
                     if (idx == b).any()))


def at_threshold(y: np.ndarray, p: np.ndarray, thr: float, severe: np.ndarray) -> dict:
    pred = p >= thr
    tp = int(np.sum(pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1)))
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    return {"threshold": round(float(thr), 4), "alerts": int(pred.sum()), "tp": tp, "fp": fp, "fn": fn,
            "tn": int(np.sum(~pred & (y == 0))), "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(2 * prec * rec / max(prec + rec, 1e-9), 4),
            "recall_severe": round(float(np.sum(pred & (severe == 1)) / max(severe.sum(), 1)), 4),
            "false_alarm_rate": round(fp / max(fp + int(np.sum(~pred & (y == 0))), 1), 4)}


def ranking(y: np.ndarray, s: np.ndarray) -> dict:
    if y.min() == y.max():
        return {"pr_auc": None, "roc_auc": None}
    return {"pr_auc": round(float(average_precision_score(y, s)), 4), "roc_auc": round(float(roc_auc_score(y, s)), 4)}


def boot_ci(df: pd.DataFrame, cols: list[str], seed: int = 42) -> dict:
    """IC 95% pentru PR-AUC și ROC-AUC, cu bootstrap pe zile (zonele din aceeași zi au aceeași vreme)."""
    rng = np.random.default_rng(seed)
    days = df["date"].unique()
    idx = df.groupby("date").indices
    res = {c: {"pr_auc": [], "roc_auc": [], "pr_auc_minus_base": []} for c in cols}
    for _ in range(N_BOOT):
        rows = np.concatenate([idx[d] for d in rng.choice(days, len(days))])
        y = df["event"].to_numpy()[rows]
        if y.min() == y.max():
            continue
        for c in cols:
            s = df[c].to_numpy()[rows]
            ap = average_precision_score(y, s)
            res[c]["pr_auc"].append(ap)
            res[c]["roc_auc"].append(roc_auc_score(y, s))
            res[c]["pr_auc_minus_base"].append(ap - y.mean())
    return {c: {k: [round(float(np.quantile(v, 0.025)), 4), round(float(np.quantile(v, 0.975)), 4)]
                for k, v in d.items()} for c, d in res.items()}


def paired_diff(df: pd.DataFrame, a: str, b: str, seed: int = 7) -> dict:
    """PR-AUC(a) − PR-AUC(b) cu bootstrap pe zile: IC 95% și ce parte din eșantioane are a > b."""
    rng = np.random.default_rng(seed)
    days = df["date"].unique()
    idx = df.groupby("date").indices
    d = []
    for _ in range(N_BOOT):
        rows = np.concatenate([idx[x] for x in rng.choice(days, len(days))])
        y = df["event"].to_numpy()[rows]
        if y.min() == y.max():
            continue
        d.append(average_precision_score(y, df[a].to_numpy()[rows]) - average_precision_score(y, df[b].to_numpy()[rows]))
    d = np.array(d)
    return {"diff": round(float(np.median(d)), 4), "ci95": [round(float(np.quantile(d, 0.025)), 4),
            round(float(np.quantile(d, 0.975)), 4)], "share_a_better": round(float((d > 0).mean()), 3)}


def capacity(df: pd.DataFrame, scores: list[str], k: int) -> dict:
    """În fiecare zi, K echipe în cele K zone cu scorul cel mai mare: ce parte din clienții afectați prind."""
    affected = np.where(df["event"] == 1, df["out_max"], 0.0)
    ev = df["event"].to_numpy() == 1
    out = {}
    for c in [*scores, "oracol"]:
        sc = affected if c == "oracol" else df[c].to_numpy()
        chosen = np.zeros(len(df), bool)
        for idx in df.groupby("date").indices.values():
            chosen[idx[np.argsort(-sc[idx], kind="stable")[:k]]] = True
        out[c] = {"customers_covered_share": round(float(affected[chosen].sum() / max(affected.sum(), 1)), 4),
                  "events_caught_share": round(float((chosen & ev).sum() / max(ev.sum(), 1)), 4),
                  "alert_precision": round(float((chosen & ev).sum() / max(chosen.sum(), 1)), 4)}
    return out


def pinball(y: np.ndarray, q: np.ndarray, a: float) -> float:
    d = y - q
    return float(np.mean(np.maximum(a * d, (a - 1) * d)))


# ---------------------------------------------------------------------------------------------
# Rularea
# ---------------------------------------------------------------------------------------------


def weather(zones: list[romania.Zone], start: date, end: date, source: str) -> pd.DataFrame:
    lats, lons = [z.lat for z in zones], [z.lon for z in zones]
    if source == "archive":
        payloads = openmeteo.archive_daily(lats, lons, start.isoformat(), end.isoformat(), timezone=TZ)
    else:
        payloads = openmeteo.historical_forecast(lats, lons, start.isoformat(), end.isoformat(), timezone=TZ)
    frames = []
    for z, p in zip(zones, payloads, strict=True):
        d = openmeteo.daily_frame(p)
        d["zone_id"] = z.zone_id
        frames.append(d)
    wx, _ = clean_weather(pd.concat(frames, ignore_index=True))
    return wx


def score_table(model: BModel, zones: list[romania.Zone], wx: pd.DataFrame, days: list[date]) -> pd.DataFrame:
    rows = []
    for d in days:
        f = target_features(zones, wx, d)
        f = f[f[FEATURES].drop(columns=["log_customers", "log_density", "doy_sin", "doy_cos"]).notna().all(axis=1)]
        if f.empty:
            continue
        f["p_model"] = model.predict_proba(f)
        q = model.predict_quantiles(f)
        f["q10"], f["q50"], f["q90"] = q[:, 0], q[:, 1], q[:, 2]
        rows.append(f)
    return pd.concat(rows, ignore_index=True)


def evaluate(tab: pd.DataFrame, model: BModel) -> dict:
    y = tab["event"].to_numpy()
    sev = tab["severe"].to_numpy()
    p = tab["p_model"].to_numpy()
    res: dict = {"rows": len(tab), "days": int(tab["date"].nunique()), "zones": int(tab["zone_id"].nunique()),
                 "events": int(y.sum()), "severe_events": int(sev.sum()), "prevalence": round(float(y.mean()), 4)}
    if y.sum() == 0:
        return res
    cols = ["p_model", "gust_max", "zone_rate_loo", "small_zone", "random"]
    res["ranking"] = {c: ranking(y, tab[c].to_numpy()) for c in cols}
    res["ranking_ci95"] = boot_ci(tab, ["p_model", "gust_max", "small_zone"])
    res["pr_auc_model_vs"] = {b: paired_diff(tab, "p_model", b) for b in ["gust_max", "small_zone", "zone_rate_loo"]}
    res["probabilistic"] = {
        "brier_model": round(float(brier_score_loss(y, p)), 4),
        "brier_constant_prevalence": round(float(brier_score_loss(y, np.full_like(p, y.mean()))), 4),
        "brier_us_train_rate": round(float(brier_score_loss(y, np.full_like(p, model.train_info["events"]
                                                                            / model.train_info["rows"]))), 4),
        "log_loss_model": round(float(log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1])), 4),
        "ece_10bins": round(ece(y, p), 4),
        "mean_predicted": round(float(p.mean()), 4),
        "observed_rate": round(float(y.mean()), 4),
    }
    bins = pd.cut(tab["p_model"], [0, 0.05, 0.1, 0.16, 0.3, 0.5, 1.0], include_lowest=True)
    rel = tab.groupby(bins, observed=True).agg(n=("event", "size"), observed=("event", "mean"), predicted=("p_model", "mean"))
    res["reliability"] = [{"bin": str(i), "n": int(r.n), "observed": round(float(r.observed), 4),
                           "predicted": round(float(r.predicted), 4)} for i, r in rel.iterrows()]
    res["at_model_threshold"] = at_threshold(y, p, model.decision_threshold, sev)
    best = best_f1_threshold(y, p)
    res["at_best_f1_threshold_in_sample"] = at_threshold(y, p, best, sev)
    res["gust_rule_70kmh"] = at_threshold(y, tab["gust_max"].to_numpy(), GUST_RULE_KMH, sev)
    res["capacity_k3"] = capacity(tab, ["p_model", "gust_max", "small_zone", "random"], 3)
    res["capacity_k5"] = capacity(tab, ["p_model", "gust_max", "small_zone", "random"], 5)
    ev = tab[tab["event"] == 1]
    ylog = np.log1p(100 * ev["pct_out_max"].to_numpy())
    qlog = np.log1p(100 * ev[["q10", "q50", "q90"]].to_numpy())
    res["quantiles_on_events"] = {
        "n": len(ev),
        "coverage_p10_p90": round(float(np.mean((ev["pct_out_max"] >= ev["q10"]) & (ev["pct_out_max"] <= ev["q90"]))), 4),
        "share_above_p90": round(float(np.mean(ev["pct_out_max"] > ev["q90"])), 4),
        "share_below_p10": round(float(np.mean(ev["pct_out_max"] < ev["q10"])), 4),
        "pinball_log_q10": round(pinball(ylog, qlog[:, 0], 0.1), 4),
        "pinball_log_q50": round(pinball(ylog, qlog[:, 1], 0.5), 4),
        "pinball_log_q90": round(pinball(ylog, qlog[:, 2], 0.9), 4),
        "median_observed_pct": round(float(100 * ev["pct_out_max"].median()), 3),
        "median_p50_pct": round(float(100 * ev["q50"].median()), 3),
        "mae_p50_pct_points": round(float(100 * np.mean(np.abs(ev["pct_out_max"] - ev["q50"]))), 3),
    }
    oor = model.out_of_range(tab)
    res["rows_out_of_training_range"] = int(oor.map(bool).sum())
    res["out_of_range_features"] = pd.Series([f for fs in oor for f in fs]).value_counts().to_dict()
    return res


def build_table(model: BModel, zones, wx, peaks: pd.DataFrame, days: list[date], event_thr: float = 0.01) -> pd.DataFrame:
    tab = score_table(model, zones, wx, days)
    tab = tab.merge(peaks, on=["zone_id", "date"], how="left")
    tab["out_max"] = tab["out_max"].fillna(0.0)
    tab["pct_out_max"] = tab["out_max"] / tab["customers"]
    tab["event"] = (tab["pct_out_max"] >= event_thr).astype(int)
    tab["severe"] = (tab["pct_out_max"] >= 0.05).astype(int)
    # Repere: zona mică (prag de 1% ușor de atins), rata zonei din celelalte săptămâni, scor aleator
    tab["small_zone"] = -tab["log_customers"]
    week = tab["date"].dt.isocalendar().week.to_numpy()
    rate = []
    for z, w in zip(tab["zone_id"], week, strict=True):
        o = tab[(tab["zone_id"] == z) & (week != w)]["event"]
        rate.append(o.mean() if len(o) else tab["event"].mean())
    tab["zone_rate_loo"] = rate
    tab["random"] = np.random.default_rng(0).uniform(size=len(tab))
    return tab


def run() -> dict:
    model = BModel.load()
    zones = romania.load_zones()
    out, info = load_outages()
    out = assign_zones(out, zones)
    total_min = (info["_to"] - info["_from"]) // 60
    peaks = daily_peaks(out, info["_from"], total_min, "zone_id")

    # zile locale complete după începutul colectării și înainte de instantaneu
    since = pd.Timestamp(info["_since"], unit="s", tz="UTC").tz_convert(TZ)
    to = pd.Timestamp(info["_to"], unit="s", tz="UTC").tz_convert(TZ)
    first = (since.normalize() + pd.Timedelta(days=1)).date()
    last = (to.normalize() - pd.Timedelta(days=1)).date()
    days = [first + timedelta(days=i) for i in range((last - first).days + 1)]

    report: dict = {
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "model_version": model.version,
        "model_threshold": model.decision_threshold,
        "model_train_info": model.train_info,
        "synthetic_data": False,
        "labels": {k: v for k, v in info.items() if not k.startswith("_")},
        "days_evaluated": [days[0].isoformat(), days[-1].isoformat()],
        "assignment": {"median_km_to_zone": round(float(out["dist_km"].median()), 1),
                       "p95_km_to_zone": round(float(out["dist_km"].quantile(0.95)), 1),
                       "rows_over_60km": int((out["dist_km"] > 60).sum()),
                       "rows_per_zone": out["zone_id"].value_counts().to_dict()},
        "duration_hours": {"median": round(float(out["dur_h"].median()), 2),
                           "p95": round(float(out["dur_h"].quantile(0.95)), 1),
                           "over_72h": int((out["dur_h"] > 72).sum())},
    }

    wx_start = days[0] - timedelta(days=romania.LAG_DAYS)
    for source in ["archive", "historical_forecast"]:
        try:
            wx = weather(zones, wx_start, days[-1], source)
        except Exception as exc:  # noqa: BLE001
            report[source] = {"error": f"{type(exc).__name__}: {exc}"[:300]}
            continue
        tab = build_table(model, zones, wx, peaks, days)
        report[source] = evaluate(tab, model)
        if source == "archive":
            main_tab = tab
            peaks72 = daily_peaks(out, info["_from"], total_min, "zone_id", max_dur_h=72)
            peaks24 = daily_peaks(out, info["_from"], total_min, "zone_id", max_dur_h=24)
            new = daily_new(out, info["_from"], "zone_id")
            report["sensitivity"] = {
                "duration_capped_72h": evaluate(build_table(model, zones, wx, peaks72, days), model),
                "duration_capped_24h": evaluate(build_table(model, zones, wx, peaks24, days), model),
                "new_incidents_ge_1pct": evaluate(build_table(model, zones, wx, new, days), model),
                "new_incidents_ge_2pct": evaluate(build_table(model, zones, wx, new, days, 0.02), model),
                "event_threshold_0_5pct": evaluate(build_table(model, zones, wx, peaks, days, 0.005), model),
                "event_threshold_2pct": evaluate(build_table(model, zones, wx, peaks, days, 0.02), model),
            }
            top = main_tab.sort_values("pct_out_max", ascending=False).head(15)
            report["top_zone_days"] = [
                {"zone": r.zone_id, "date": r.date.date().isoformat(), "pct_out": round(100 * r.pct_out_max, 2),
                 "out_max": int(r.out_max), "p_model": round(float(r.p_model), 3), "gust_kmh": round(float(r.gust_max), 1),
                 "precip_mm": round(float(r.precip), 1)} for r in top.itertuples()]
            report["max_gust_kmh_in_window"] = round(float(main_tab["gust_max"].max()), 1)
            report["max_p_model_in_window"] = round(float(main_tab["p_model"].max()), 3)
            OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
            ROWS_CSV.parent.mkdir(parents=True, exist_ok=True)
            main_tab[["zone_id", "date", "customers", "out_max", "pct_out_max", "event", "p_model", "q10", "q50", "q90",
                      "gust_max", "precip", "precip_7d", "tmin"]].to_csv(ROWS_CSV, index=False)

    report["cases"] = case_checks(model, zones)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return report


def case_checks(model: BModel, zones: list[romania.Zone]) -> list[dict]:
    """Cazuri confirmate din presă și comunicate: ce probabilitate dădea modelul (vremea din arhivă)."""
    cases = [("2026-01-05", "HD", "RER: circa 5.500 clienți afectați la ora 15:00 în Hunedoara (≈2,5% din județ)"),
             ("2025-07-08", "TM", "Furtuna din Banat: cod roșu, circa 40.000 consumatori afectați cumulat în Timiș"),
             ("2025-07-08", "CS", "Furtuna din Banat: rafale 90-120 km/h, stâlpi avariați Reșița-Timișoara"),
             ("2025-07-07", "CS", "Furtună la Reșița și Caransebeș, rafale peste 80 km/h")]
    out = []
    for d, county, note in cases:
        day = date.fromisoformat(d)
        zs = [z for z in zones if z.county_code == county]
        try:
            wx = weather(zs, day - timedelta(days=romania.LAG_DAYS), day, "archive")
        except Exception as exc:  # noqa: BLE001
            out.append({"date": d, "county": county, "error": str(exc)[:200]})
            continue
        f = target_features(zs, wx, day)
        p = model.predict_proba(f)
        out.append({"date": d, "county": county, "note": note,
                    "zones": {z: round(float(v), 3) for z, v in zip(f["zone_id"], p, strict=True)},
                    "gust_kmh": {z: round(float(v), 1) for z, v in zip(f["zone_id"], f["gust_max"], strict=True)},
                    "above_threshold": bool((p >= model.decision_threshold).any())})
    return out


def main() -> int:
    r = run()
    a = r.get("archive", {})
    print(json.dumps({k: a.get(k) for k in ["rows", "days", "events", "prevalence", "ranking", "probabilistic",
                                             "at_model_threshold"]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
