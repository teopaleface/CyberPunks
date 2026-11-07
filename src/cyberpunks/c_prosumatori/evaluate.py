"""Evaluarea modelului C pe REȚELE NEVĂZUTE și LUNI NEVĂZUTE, față de baseline.

Schema: pentru fiecare dintre cele 6 topologii SimBench, modelul se antrenează pe celelalte 5, doar pe zilele
dinainte de 2025-01-01, și prezice topologia lăsată deoparte pe zilele din 2025-01-01 → 2026-11-06. Calibrarea
(izotonică pentru probabilitate, conformal pentru interval) folosește tot predicții pe topologii nevăzute,
făcute numai pe topologiile de antrenare ale fold-ului. Toate predicțiile de test se adună și se măsoară o dată.

    uv run python -m cyberpunks.c_prosumatori.evaluate      # reports/C/metrics.json, metrics_detail.json, figuri
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import features as F
from cyberpunks.c_prosumatori import train as T
from cyberpunks.common.contracts import ModelReport
from cyberpunks.common.paths import REPORTS

OUT = REPORTS / "C"
REPRODUCE = "uv run python -m cyberpunks.c_prosumatori.evaluate"


def pinball(y: np.ndarray, q: np.ndarray, a: float) -> float:
    d = y - q
    return float(np.mean(np.maximum(a * d, (a - 1) * d)))


def ece(ex: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """Eroarea de calibrare așteptată: media ponderată a |probabilitate prezisă − frecvență reală| pe 10 coșuri."""
    idx = np.clip((np.asarray(p) * bins).astype(int), 0, bins - 1)
    tot = 0.0
    for k in range(bins):
        sel = idx == k
        if sel.any():
            tot += sel.mean() * abs(float(np.mean(p[sel])) - float(np.mean(ex[sel])))
    return float(tot)


def hourly_eval(n_estimators: int = 300) -> dict:
    """Modelul orar (seria din grafic) pe rețele nevăzute și luni nevăzute, pe eșantionul orar."""
    hs = T.load_hourly_sample("train")
    feats = F.HOURLY_FEATURES
    tr_p, te_p = hs[hs["date"] < T.SPLIT_DATE], hs[hs["date"] >= T.SPLIT_DATE]
    parts = []
    for t in sorted(hs["topology"].unique()):
        tr, te = tr_p[tr_p.topology != t], te_p[te_p.topology == t]
        q = {a: T.fit_quantile(tr[feats], tr["vmax"].to_numpy(), a, n_estimators=n_estimators).predict(te[feats]) for a in T.QUANTILES}
        parts.append(pd.DataFrame({"y": te["vmax"].to_numpy(), "q10": np.minimum(q[0.1], q[0.5]), "q50": q[0.5],
                                   "q90": np.maximum(q[0.9], q[0.5]), "pvk": te["pvk"].to_numpy(), "topology": t}))
        print(f"  orar {t}: {len(te)} ore de test", flush=True)
    r = pd.concat(parts, ignore_index=True)
    # lărgirea conformală pentru fiecare topologie, din reziduurile celorlalte topologii (fără etichetele ei)
    e = np.maximum(r.q10 - r.y, r.y - r.q90).to_numpy()
    margin = np.zeros(len(r))
    for t in r.topology.unique():
        other = e[(r.topology != t).to_numpy()]
        margin[(r.topology == t).to_numpy()] = np.quantile(other, min(1.0, np.ceil((len(other) + 1) * 0.8) / len(other)))
    lo, hi = r.q10 - margin, r.q90 + margin
    day = r["pvk"] > 0.05
    out = {"test_hours": len(r), "mae_vmax_pu": float(np.mean(np.abs(r.y - r.q50))),
           "mae_vmax_daylight_pu": float(np.mean(np.abs(r.y[day] - r.q50[day]))),
           "coverage_p10_p90_raw": float(np.mean((r.y >= r.q10) & (r.y <= r.q90))),
           "coverage_p10_p90": float(np.mean((r.y >= lo) & (r.y <= hi))),
           "coverage_p10_p90_daylight": float(np.mean((r.y[day] >= lo[day]) & (r.y[day] <= hi[day]))),
           "cqr_margin_mean_pu": float(margin.mean())}
    return out


def scores(y: np.ndarray, ex: np.ndarray, pred: dict, thr: float = 0.5) -> dict[str, float]:
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

    p = pred["p_exceed"]
    yhat = p >= thr
    tp = float(np.sum(yhat & (ex == 1)))
    out = {
        "mae_vmax_pu": float(np.mean(np.abs(y - pred["q50"]))),
        "rmse_vmax_pu": float(np.sqrt(np.mean((y - pred["q50"]) ** 2))),
        "pinball_mean": float(np.mean([pinball(y, pred[f"q{int(a * 100)}"], a) for a in T.QUANTILES])),
        "coverage_p10_p90": float(np.mean((y >= pred["q10"]) & (y <= pred["q90"]))),
        "interval_width_pu": float(np.mean(pred["q90"] - pred["q10"])),
        "brier": float(brier_score_loss(ex, p)),
        "recall_exceed": tp / max(float(ex.sum()), 1.0),
        "precision_exceed": tp / max(float(yhat.sum()), 1.0),
        "exceed_rate": float(ex.mean()),
    }
    if 0 < ex.sum() < len(ex):
        out["pr_auc_exceed"] = float(average_precision_score(ex, p))
        out["roc_auc_exceed"] = float(roc_auc_score(ex, p))
    out["ece_exceed"] = ece(ex, p)
    # zilele care contează pentru decizie: soare la prânz (producție de peste 0,5 kW/kWp)
    return out


def evaluate(oof_frac: float = 0.35, monotone: bool = True, drop: tuple[str, ...] = (), save: bool = True) -> dict:
    t0 = time.perf_counter()
    df = T.load_daily("train")
    feats = [f for f in F.DAILY_FEATURES if f not in drop]
    train_period = df[df["date"] < T.SPLIT_DATE]
    test_period = df[df["date"] >= T.SPLIT_DATE]
    topologies = sorted(df["topology"].unique())
    parts = []
    for t in topologies:
        tr = train_period[train_period.topology != t]
        te = test_period[test_period.topology == t].copy()
        oof = T.logo_oof(T.sample_for_oof(tr, oof_frac), feats, monotone=monotone)
        model = T.DailyModel(features=list(feats), monotone=monotone).fit(tr, calib=oof)
        base = T.Baseline().fit(tr)
        pm, pr, pb = model.predict(te), model.predict(te, calibrated=False), base.predict(te)
        for k, v in pm.items():
            te[f"m_{k}"] = v
        for k in ("q10", "q90", "p_exceed"):
            te[f"r_{k}"] = pr[k]
        for k, v in pb.items():
            te[f"b_{k}"] = v
        te["cqr_margin"] = model.cqr_margin
        parts.append(te)
        print(f"  {t}: test {len(te)} zile-post, MAE model {np.mean(np.abs(te.vmax_day - te.m_q50)):.4f}, "
              f"baseline {np.mean(np.abs(te.vmax_day - te.b_q50)):.4f}, {time.perf_counter() - t0:.0f} s", flush=True)
    res = pd.concat(parts, ignore_index=True)
    if save:
        res.to_parquet(T.DATA_PROCESSED / "C" / "eval_predictions.parquet")
    return summarize(res, time.perf_counter() - t0)


ABLATIONS = {
    # fără trăsăturile fizice din topologie (sensibilitățile, estimarea liniară a tensiunii, rezistența)
    "fara_fizica": ("sens_pv_pu", "sens_load_pu", "dv_lin_max", "v_lin_max", "net_kw_per_kva_max", "r_max_ohm"),
    # fără tensiunea de pornire și priză (ce s-ar întâmpla dacă distribuitorul nu le știe)
    "fara_tensiune_pornire": ("v0_est", "tap_pos", "v_lin_max"),
}


def ablation(tag: str) -> dict:
    """Aceeași evaluare, fără un grup de trăsături (sau fără constrângeri monotone); nu atinge metrics.json."""
    if tag == "fara_monotone":
        det = evaluate(monotone=False, save=False)
    else:
        det = evaluate(drop=ABLATIONS[tag], save=False)
    keys = ("mae_vmax_pu", "rmse_vmax_pu", "coverage_p10_p90", "pr_auc_exceed", "recall_exceed", "precision_exceed", "brier", "ece_exceed")
    out = {"tag": tag, "dropped": list(ABLATIONS.get(tag, ())), "model": {k: det["model"].get(k) for k in keys},
           "by_topology_mae": {t: v["model"]["mae_vmax_pu"] for t, v in det["by_topology"].items()}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"ablation_{tag}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _pred(res: pd.DataFrame, prefix: str) -> dict:
    return {k: res[f"{prefix}_{k}"].to_numpy() for k in ("q10", "q50", "q90", "p_exceed")}


def summarize(res: pd.DataFrame, seconds: float) -> dict:
    y, ex = res["vmax_day"].to_numpy(), res["exceed"].to_numpy()
    m, b = scores(y, ex, _pred(res, "m")), scores(y, ex, _pred(res, "b"))
    raw = _pred(res, "m") | {"q10": res["r_q10"].to_numpy(), "q90": res["r_q90"].to_numpy(), "p_exceed": res["r_p_exceed"].to_numpy()}
    m_raw = scores(y, ex, raw)
    sunny = res["pvk_max"].to_numpy() > 0.5
    m_sunny = scores(y[sunny], ex[sunny], {k: v[sunny] for k, v in _pred(res, "m").items()})
    b_sunny = scores(y[sunny], ex[sunny], {k: v[sunny] for k, v in _pred(res, "b").items()})
    by_topo = {}
    for t, g in res.groupby("topology"):
        yy, ee = g["vmax_day"].to_numpy(), g["exceed"].to_numpy()
        by_topo[t] = {"model": scores(yy, ee, _pred(g, "m")), "baseline": scores(yy, ee, _pred(g, "b")), "rows": len(g)}
    detail = {
        "split": "leave-one-topology-out (6 topologii SimBench) × luni nevăzute (antrenare < 2025-01-01, test ≥ 2025-01-01)",
        "test_rows": len(res),
        "model": m,
        "model_uncalibrated": m_raw,
        "baseline": b,
        "model_sunny_days": m_sunny,
        "baseline_sunny_days": b_sunny,
        "by_topology": by_topo,
        "seconds": round(seconds, 1),
    }
    return detail


def write_report(detail: dict, speed: dict | None = None) -> ModelReport:
    m, b = detail["model"], detail["baseline"]
    keys = ["mae_vmax_pu", "rmse_vmax_pu", "pinball_mean", "coverage_p10_p90", "interval_width_pu", "pr_auc_exceed",
            "roc_auc_exceed", "brier", "ece_exceed", "recall_exceed", "precision_exceed", "exceed_rate"]
    metrics = {k: round(m[k], 5) for k in keys if k in m}
    metrics.update({f"sunny_{k}": round(detail["model_sunny_days"][k], 5) for k in ("mae_vmax_pu", "pr_auc_exceed", "recall_exceed") if k in detail["model_sunny_days"]})
    base = {k: round(b[k], 5) for k in keys if k in b}
    base.update({f"sunny_{k}": round(detail["baseline_sunny_days"][k], 5) for k in ("mae_vmax_pu", "pr_auc_exceed", "recall_exceed") if k in detail["baseline_sunny_days"]})
    if speed:  # viteza: modelul față de calculul de rețea pandapower (referința fizică, nu baseline-ul)
        metrics.update({k: round(v, 4) for k, v in speed.items()})
    rep = ModelReport(
        source="C",
        model_id="c-surrogate",
        model_version=f"c-lgbm@{T.git_sha()}",
        task="regresie cuantilă a tensiunii maxime zilnice pe post (P10, P50, P90) + clasificare calibrată P(tensiune > 1,10 pu)",
        dataset=[
            "SimBench 1.6.3, 6 rețele JT (ODbL), variante SINTETICE de posturi",
            "Open-Meteo Historical Weather (ERA5), 44,45 N 26,05 E, 2023-01-01 → 2026-11-06 (CC BY 4.0)",
            "Etichete din fizică: circulație de puteri orară (pandapower 3.5.6 + calcul vectorizat verificat față de runpp)",
            "Profile de consum SimBench H0/G pe calendarul românesc; kWp și baterii calibrate pe ANRE (iun. 2026)",
        ],
        split=detail["split"],
        test_size=int(detail["test_rows"]),
        primary_metric="mae_vmax_pu",
        metrics=metrics,
        baseline_id="linreg-gti-x-kw-per-kva",
        baseline_metrics=base,
        synthetic_share=1.0,
        created_at=datetime.now(ZoneInfo("Europe/Bucharest")).replace(microsecond=0),
        reproduce_cmd=REPRODUCE,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(rep.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (OUT / "metrics_detail.json").write_text(json.dumps(detail, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rep


def speed_test(n_posts: int = 300, pp_snapshots: int = 48) -> dict:
    """Timpul pentru o zi pe toată populația: modelul față de calculul de rețea (măsurat)."""
    import copy

    import pandapower as pp

    from cyberpunks.c_prosumatori import grids, weather

    b = T.load_bundle()
    from cyberpunks.c_prosumatori.posts import load_posts

    reg = load_posts().head(n_posts)
    hw = F.hourly_weather(weather.archive("2023-01-01", "2026-11-06"))
    day = hw[hw["date"] == pd.Timestamp("2025-07-15").date()]
    t0 = time.perf_counter()
    X = F.daily_features(reg, day)
    b.daily.predict(X)
    t_daily = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _, st in reg.iterrows():
        b.hourly.predict(F.hourly_features(st, day))
    t_hourly = time.perf_counter() - t0
    # pandapower: instantanee pe câteva posturi, extrapolat la 300 de posturi × 24 de ore
    times = []
    for _, st in reg.head(4).iterrows():
        spec = grids.spec_from_row(st)
        net = copy.deepcopy(grids.build_post(spec).net)
        for _ in range(pp_snapshots // 4):
            t1 = time.perf_counter()
            pp.runpp(net, numba=False)
            times.append(time.perf_counter() - t1)
    pp_day = float(np.median(times)) * 24 * n_posts
    return {
        "surrogate_seconds_300_posts_day": t_daily,
        "surrogate_seconds_300_posts_hourly_series": t_hourly,
        "powerflow_seconds_300_posts_day_pandapower": pp_day,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--no-monotone", action="store_true")
    ap.add_argument("--oof-frac", type=float, default=0.35)
    ap.add_argument("--no-speed", action="store_true")
    ap.add_argument("--speed-only", action="store_true", help="refolosește metrics_detail.json, măsoară doar viteza")
    ap.add_argument("--rescore", action="store_true", help="recalculează metricile din predicțiile salvate (fără reantrenare)")
    ap.add_argument("--hourly", action="store_true", help="evaluează și modelul orar (circa 10 minute)")
    ap.add_argument("--ablation", choices=["fara_fizica", "fara_tensiune_pornire", "fara_monotone"], default=None)
    a = ap.parse_args()
    if a.ablation:
        print(json.dumps(ablation(a.ablation), indent=1, ensure_ascii=False))
        raise SystemExit(0)
    if a.speed_only:
        det = json.loads((OUT / "metrics_detail.json").read_text())
    elif a.rescore:
        old_det = json.loads((OUT / "metrics_detail.json").read_text())
        det = summarize(pd.read_parquet(T.DATA_PROCESSED / "C" / "eval_predictions.parquet"), old_det.get("seconds", 0.0))
        det.update({k: old_det[k] for k in ("hourly", "speed") if k in old_det})
    else:
        det = evaluate(oof_frac=a.oof_frac, monotone=not a.no_monotone)
    if a.hourly:
        det["hourly"] = hourly_eval()
    spd = det.get("speed")
    if not a.no_speed and not a.rescore and (T.MODEL_DIR / "bundle.joblib").exists():
        spd = speed_test()
        det["speed"] = spd
    rep = write_report(det, spd)
    print(json.dumps({"model": rep.metrics, "baseline": rep.baseline_metrics}, indent=1, ensure_ascii=False))
