"""Ferestrele diagnosticului: pe post, la fiecare 7 zile, ultimele 14 zile comparate cu pierderea normală.

Trăsăturile spun cât de mare e lipsa peste normal și ce formă are:
- nivelul: lipsa peste P50 (kWh/zi, procent, în unități de interval), câte zile peste P90;
- saltul: ultimele 7 zile față de primele 7 și față de fereastra dinainte (furtul apare brusc și rămâne);
- legătura cu încărcarea: corelația lipsei cu Σ P² (pierderea tehnică crește cu pătratul încărcării);
- noaptea: ce parte din lipsă apare noaptea (un furt constant se vede și noaptea);
- raportul contor de post / suma clienților (exact 2 = contorul de post setat greșit);
- vecinii: surplusul celui mai apropiat post și cât de bine se potrivește cu lipsa (client trecut la postul greșit);
- contoarele: semnale noi de zero, blocat, negativ noaptea; cel mai mare consum dispărut la un client și cât de bine
  explică lipsa; tensiunea contorului care seamănă cel mai puțin cu postul.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant.dataset import WINDOW, eval_days
from cyberpunks.common.paths import DATA_PROCESSED

WIN_FEATURES = [
    "r_mean_kwh",
    "r_pct",
    "z_mean",
    "days_over_p90",
    "days_under_p10",
    "jump_in_window",
    "jump_vs_prev",
    "corr_r_load2",
    "night_excess_share",
    "bal_db_ratio",
    "neigh_min_r_kwh",
    "neigh_match",
    "new_zero",
    "new_stuck",
    "new_neg",
    "max_drop_kwh",
    "drop_match",
    "drop_share",
    "vcorr_min",
    "vcorr_gap",
    "miss_share_w",
    "p50_mean_kwh",
    "width_kwh",
    "hist_days",
    "delta_kwh",
    "delta_long_kwh",
    "neigh_mirror_corr",
    "neigh_mirror_match",
    "corr_r_p50",
    "loss_ratio",
    "loss_ratio_cv",
    "quad_ratio",
    "intercept_jump_kwh_h",
    "linear_jump",
    "volt_elsewhere",
    "volt_claimed",
]
# calculate și salvate, dar scoase din model: au ridicat pierderea tehnică (F1 0,46 → 0,47) și au coborât F1 macro
# (0,668 → 0,658), diferențe în zgomot (7 nov., 15:15)
EXTRA_COLUMNS = ["ratio_vs_gis", "r_vs_gis_kwh"]
MIRROR_DAYS = 28  # fereastra pentru oglinda lipsă/surplus cu vecinii
LONG_REF = (90, 62)  # referința lungă: zilele e-90..e-62 (înaintea problemelor apărute în ultimele două luni)
METER_MATERIAL_KWH = 1.0  # sub 1 kWh/zi lipsă, un contor de client nu se vede în bilanț: eticheta rămâne „normal”


def oof_normal(df: pd.DataFrame, folds: int = 3, seed: int = 0) -> pd.DataFrame:
    """Predicțiile pierderii normale pe lotul de antrenare, fără ca postul să fi fost văzut (pe grupe de posturi)."""
    posts = df["post_id"].unique()
    rng = np.random.default_rng(seed)
    grp = dict(zip(posts, rng.integers(0, folds, len(posts)), strict=True))
    g = df["post_id"].map(grp).to_numpy()
    out = pd.DataFrame(index=df.index, columns=["p10", "p50", "p90", "p50_cold"], dtype=float)
    for k in range(folds):
        tr = df[(g != k) & df["clean"] & (df["hist_days"] > 0)]
        models = N.fit_pair(tr, seed)
        out.loc[g == k, ["p10", "p50", "p90"]] = N.predict_any(models, df.loc[g == k]).to_numpy()
        out.loc[g == k, "p50_cold"] = models["cold"].predict(N.drop_history(df.loc[g == k]))["p50"].to_numpy()
    return out


def predict_normal(models: dict, df: pd.DataFrame) -> pd.DataFrame:
    """Pierderea normală (cu istoric unde se poate) plus normalul fără istoric, doar din GIS și încărcare."""
    out = N.predict_any(models, df)
    out["p50_cold"] = models["cold"].predict(N.drop_history(df))["p50"].to_numpy()
    return out


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.std(a) < 1e-9 or np.std(b) < 1e-9:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _hourly_fit(bal: np.ndarray, db: np.ndarray) -> np.ndarray:
    """Lipsa orară = a + b·sarcină + c·sarcină² (cele mai mici pătrate); întoarce (a, b, c)."""
    y = bal - db
    ok = np.isfinite(y) & np.isfinite(db)
    if ok.sum() < 48:
        return np.array([np.nan, np.nan, np.nan])
    X = np.stack([np.ones(ok.sum()), db[ok], db[ok] ** 2], 1)
    coef, *_ = np.linalg.lstsq(X, y[ok], rcond=None)
    return coef


def build_windows(d: pd.DataFrame, pred: pd.DataFrame, pool: str, days: list[int] | None = None) -> pd.DataFrame:
    """O linie pe (post, zi de evaluare). `d` are trăsăturile zilnice și etichetele; `pred` pierderea normală."""
    o = DATA_PROCESSED / "bilant" / pool
    nb = json.loads((o / "neighbors.json").read_text())
    cust = np.load(o / "cust_daily.npz")
    vc = pd.read_parquet(o / "vcorr.parquet").set_index(["post_id", "day"])
    d = d.copy()
    d[["p10", "p50", "p90"]] = pred[["p10", "p50", "p90"]].to_numpy()
    d["p50_cold"] = pred["p50_cold"].to_numpy() if "p50_cold" in pred else d["p50"]
    d["r"] = d["short_kwh"] - d["p50"]
    d["half_w"] = ((d["p90"] - d["p10"]) / 2.56).clip(lower=0.5)
    D = int(d["day"].max()) + 1
    days = days or eval_days(D)
    by_post = {p: g.set_index("day") for p, g in d.groupby("post_id")}
    hourly = np.load(o / "hourly.npz")
    from cyberpunks.a_bilant import world

    hour_day = world.load_weather().local_day
    # nivelul fiecărui post pe fiecare fereastră (pentru vecini)
    rmean = {(p, e): float(g.loc[e - WINDOW + 1 : e, "r"].mean()) for p, g in by_post.items() for e in days}
    rows = []
    for p, g in by_post.items():
        cd = cust[p] if p in cust.files else None
        hb = hourly[f"bal__{p}"].astype(float) if f"bal__{p}" in hourly.files else None
        hd = hourly[f"db__{p}"].astype(float) if f"db__{p}" in hourly.files else None
        for e in days:
            w = g.loc[e - WINDOW + 1 : e]
            prev = g.loc[e - 2 * WINDOW + 1 : e - WINDOW]
            if len(w) < WINDOW // 2:
                continue
            r = w["r"].to_numpy()
            r_mean = float(r.mean())
            p50m = float(w["p50"].mean())
            half = float(w["half_w"].mean())
            z = r / w["half_w"].to_numpy()
            first, last = r[: len(r) // 2], r[len(r) // 2 :]
            exp_night = (w["p50"] * w["night_sq_kwh2"] / w["sq_kwh2"].clip(lower=1e-6)).sum()
            night_ex = float(w["night_short_kwh"].sum() - exp_night)
            nbs = nb.get(p, [])
            nr = [rmean.get((q, e), 0.0) for q in nbs]
            # oglinda: clientul mutat apare ca lipsă la un post și ca surplus la vecin, zi de zi (corelație negativă)
            rp = g.loc[e - MIRROR_DAYS + 1 : e, "r"]
            mir_c, mir_m, mir_q = 0.0, 0.0, ""
            for q in nbs:
                rq = by_post[q].loc[e - MIRROR_DAYS + 1 : e, "r"] if q in by_post else None
                if rq is None or len(rq) != len(rp) or len(rp) < 10:
                    continue
                c = _corr(rp.to_numpy(), rq.to_numpy())
                if c < mir_c:
                    mir_c, mir_q = c, q
                    a_, b_ = float(rp.tail(WINDOW).mean()), float(rq.tail(WINDOW).mean())
                    mir_m = float(max(0.0, 1 - abs(a_ + b_) / max(abs(a_), abs(b_), 1.0))) if a_ * b_ < 0 else 0.0
            # forma orară a lipsei, acum față de luna dinainte (aceleași zile ca la contoare)
            q_ratio, a_jump, b_jump = 1.0, 0.0, 0.0
            if hb is not None and e - 34 >= 0:
                now = (hour_day > e - WINDOW) & (hour_day <= e)
                ref = (hour_day >= e - 34) & (hour_day <= e - 14)
                cn, cr = _hourly_fit(hb[now], hd[now]), _hourly_fit(hb[ref], hd[ref])
                if np.isfinite(cn).all() and np.isfinite(cr).all():
                    q_ratio = float(np.clip(cn[2] / cr[2], -5, 20)) if abs(cr[2]) > 1e-7 else 1.0
                    a_jump, b_jump = float(cn[0] - cr[0]), float(cn[1] - cr[1])
            # pierderea tehnică: lipsa în plus e proporțională cu pierderea normală (raport constant)
            w28 = g.loc[e - MIRROR_DAYS + 1 : e]
            ratio_d = (w28["short_kwh"] / w28["p50"].clip(lower=0.5)).to_numpy()
            corr_rp50 = _corr(w28["r"].to_numpy(), w28["p50"].to_numpy())
            # față de normalul fără istoric (doar GIS și încărcare): prinde și problemele vechi, învățate de istoric
            ratio_gis = float(w["short_kwh"].mean() / max(float(w["p50_cold"].mean()), 0.5))
            r_gis = float((w["short_kwh"] - w["p50_cold"]).mean())
            nmin = float(min(nr)) if nr else 0.0
            match = float(1 - abs(r_mean + nmin) / max(abs(r_mean), abs(nmin), 1.0)) if nr else 0.0
            # contoarele de client: consumul dispărut (înainte: zilele e-34..e-14; după: ultimele 7 zile)
            max_drop, drop_match, drop_share = 0.0, 0.0, 0.0
            if cd is not None and e - 34 >= 0:
                before = cd[:, e - 34 : e - 13].mean(1)
                after = cd[:, e - 6 : e + 1].mean(1)
                drop = before - after
                j = int(np.argmax(drop))
                max_drop = float(drop[j])
                if max_drop > 0:
                    drop_match = float(max(0.0, 1 - abs(max_drop - r_mean) / max(abs(r_mean), max_drop, 1.0)))
                    drop_share = float(max_drop / max(abs(before[j]), 0.1))
            # creșterea lipsei peste normal: ultimele 7 zile față de zilele e-34..e-14 (aceleași ca la contoare);
            # abaterea fixă a postului față de model se anulează
            ref = g.loc[e - 34 : e - 14, "r"]
            delta = float(g.loc[e - 6 : e, "r"].mean() - ref.mean()) if len(ref) >= 7 else 0.0
            ref_l = g.loc[e - LONG_REF[0] : e - LONG_REF[1], "r"]
            delta_long = float(g.loc[e - 6 : e, "r"].mean() - ref_l.mean()) if len(ref_l) >= 14 else delta
            try:
                v = vc.loc[(p, e)]
                vmin, vgap = float(v["vcorr_min"]), float(v["vcorr_med"] - v["vcorr_min"])
                v_else = float(v.get("volt_elsewhere", 0.0) or 0.0)
                v_claim = float(v.get("volt_claimed", 0.0) or 0.0)
            except KeyError:
                vmin, vgap, v_else, v_claim = 1.0, 0.0, 0.0, 0.0
            lab = w.iloc[-1]
            cls = lab["true_class"]
            ex = float(w["true_excess_kwh"].mean())
            if cls == "contor_client" and abs(float(w["true_meter_deficit_kwh"].mean())) < METER_MATERIAL_KWH:
                cls = "normal"
            rows.append(
                {
                    "post_id": p,
                    "day": e,
                    "date": lab["date"],
                    "r_mean_kwh": r_mean,
                    "r_pct": r_mean / max(float(w["abs_kwh"].mean()), 1.0) * 100,
                    "z_mean": float(z.mean()),
                    "days_over_p90": float((w["short_kwh"] > w["p90"]).sum()),
                    "days_under_p10": float((w["short_kwh"] < w["p10"]).sum()),
                    "jump_in_window": float(last.mean() - first.mean()) / max(half, 0.5),
                    "jump_vs_prev": float(r_mean - prev["r"].mean()) / max(half, 0.5) if len(prev) else 0.0,
                    "corr_r_load2": _corr(r, w["sq_kwh2"].to_numpy()),
                    "night_excess_share": night_ex / r.sum() if abs(r.sum()) > 1 else 0.0,
                    "bal_db_ratio": float(np.median(w["bal_kwh"] / w["db_kwh"].where(w["db_kwh"].abs() > 1))) if (w["db_kwh"].abs() > 1).any() else 1.0,
                    "neigh_min_r_kwh": nmin,
                    "neigh_match": match,
                    "new_zero": float(w["cnt_zero"].sum() - prev["cnt_zero"].sum()) if len(prev) else 0.0,
                    "new_stuck": float(w["cnt_stuck"].sum() - prev["cnt_stuck"].sum()) if len(prev) else 0.0,
                    "new_neg": float(w["cnt_neg_night"].sum() - prev["cnt_neg_night"].sum()) if len(prev) else 0.0,
                    "max_drop_kwh": max_drop,
                    "drop_match": drop_match,
                    "drop_share": drop_share,
                    "vcorr_min": vmin,
                    "vcorr_gap": vgap,
                    "miss_share_w": float(w["miss_share"].mean()),
                    "p50_mean_kwh": p50m,
                    "width_kwh": float((w["p90"] - w["p10"]).mean()),
                    "hist_days": float(lab["hist_days"]),
                    "delta_kwh": delta,
                    "delta_long_kwh": delta_long,
                    "neigh_mirror_corr": mir_c,
                    "neigh_mirror_match": mir_m,
                    "mirror_post": mir_q,
                    "corr_r_p50": corr_rp50,
                    "loss_ratio": float(np.median(ratio_d)),
                    "loss_ratio_cv": float(np.std(ratio_d) / max(abs(np.mean(ratio_d)), 0.1)),
                    "ratio_vs_gis": ratio_gis,
                    "r_vs_gis_kwh": r_gis,
                    "volt_elsewhere": v_else,
                    "volt_claimed": v_claim,
                    "quad_ratio": q_ratio,
                    "intercept_jump_kwh_h": a_jump,
                    "linear_jump": b_jump,
                    "true_class": cls,
                    "true_excess_kwh": ex,
                }
            )
    return pd.DataFrame(rows)
