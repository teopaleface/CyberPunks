"""Analiza erorilor modelului C, din predicțiile de test (rețele nevăzute × luni nevăzute).

    uv run python -m cyberpunks.c_prosumatori.error_analysis      # reports/C/error_analysis.md (cifrele) + error_tables.json

Tabelele se calculează aici; textul din reports/C/error_analysis.md le citează. Tot ce scrie acolo se reface cu
comanda de mai sus după `make c-eval`.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from cyberpunks.common.paths import DATA_PROCESSED, REPORTS

OUT = REPORTS / "C"


def _load() -> pd.DataFrame:
    res = pd.read_parquet(DATA_PROCESSED / "C" / "eval_predictions.parquet")
    posts = pd.read_parquet(DATA_PROCESSED / "C" / "train" / "posts.parquet")[["post_id", "line_type", "line_scale"]]
    res = res.merge(posts, on="post_id", how="left")
    res["err"] = res["m_q50"] - res["vmax_day"]
    res["abs_err"] = res["err"].abs()
    res["b_abs_err"] = (res["b_q50"] - res["vmax_day"]).abs()
    res["month"] = pd.to_datetime(res["date"]).dt.month
    res["pred_ex"] = res["m_p_exceed"] >= 0.5
    return res


def _group(res: pd.DataFrame, by: str | pd.Series, name: str) -> list[dict]:
    from sklearn.metrics import average_precision_score

    out = []
    for k, g in res.groupby(by, observed=True):
        row = {name: str(k), "zile_post": len(g), "mae_model": round(float(g.abs_err.mean()), 4), "mae_baseline": round(float(g.b_abs_err.mean()), 4),
               "eroare_medie_semn": round(float(g.err.mean()), 4), "rata_depasiri": round(float(g.exceed.mean()), 3),
               "acoperire_p10_p90": round(float(((g.vmax_day >= g.m_q10) & (g.vmax_day <= g.m_q90)).mean()), 3)}
        if 0 < g.exceed.sum() < len(g):
            row["pr_auc"] = round(float(average_precision_score(g.exceed, g.m_p_exceed)), 3)
            tp = int((g.pred_ex & (g.exceed == 1)).sum())
            row["recall"] = round(tp / max(int(g.exceed.sum()), 1), 3)
        out.append(row)
    return out


def tables() -> dict:
    res = _load()
    sunny = res[res.pvk_max > 0.5]
    t = {
        "pe_topologie": _group(res, "topology", "topologie"),
        "pe_conductor": _group(res, "line_type", "conductor"),
        "pe_lungime": _group(res, pd.qcut(res.max_path_km, 4, labels=["scurt", "mediu", "lung", "foarte lung"]), "drum_maxim"),
        "pe_nori_zile_cu_soare": _group(sunny, pd.cut(sunny.cloud_mean, [-1, 20, 50, 80, 101], labels=["senin", "puțini nori", "parțial noros", "noros"]), "nori_la_pranz"),
        "pe_partea_difuza": _group(sunny, pd.cut(sunny.dif_frac_noon, [0, 0.2, 0.35, 0.5, 1.0], labels=["sub 20%", "20-35%", "35-50%", "peste 50%"]), "radiatie_difuza"),
        "pe_baterii": _group(res, pd.cut(res.battery_pv_share, [-0.01, 0.0, 0.25, 0.5, 1.0], labels=["fără", "sub 25%", "25-50%", "peste 50%"]), "panouri_cu_baterie"),
        "pe_luna": _group(res, "month", "luna"),
        "pe_zi": _group(res, res.free_day.map({0.0: "lucrătoare", 1.0: "liberă"}), "zi"),
    }
    near = res[(res.vmax_day > 1.09) & (res.vmax_day < 1.11)]
    fn = res[(res.exceed == 1) & ~res.pred_ex]
    fp = res[(res.exceed == 0) & res.pred_ex]
    t["langa_prag"] = {
        "zile_post_intre_1_09_si_1_11": len(near),
        "parte_din_test": round(len(near) / len(res), 4),
        "acuratete_clasificare_langa_prag": round(float(((near.m_p_exceed >= 0.5) == (near.exceed == 1)).mean()), 3),
        "ratari_fn": len(fn),
        "fn_tensiune_mediana_reala": round(float(fn.vmax_day.median()), 4) if len(fn) else None,
        "fn_parte_sub_1_115": round(float((fn.vmax_day < 1.115).mean()), 3) if len(fn) else None,
        "alarme_false_fp": len(fp),
        "fp_tensiune_mediana_reala": round(float(fp.vmax_day.median()), 4) if len(fp) else None,
        "fp_parte_peste_1_09": round(float((fp.vmax_day > 1.09).mean()), 3) if len(fp) else None,
    }
    worst = res.nlargest(200, "abs_err")
    t["cele_mai_mari_200_erori"] = {
        "eroare_medie_absoluta": round(float(worst.abs_err.mean()), 4),
        "parte_subestimari": round(float((worst.err < 0).mean()), 3),
        "topologii": worst.topology.value_counts().to_dict(),
        "conductori": worst.line_type.value_counts().to_dict(),
        "nori_median": round(float(worst.cloud_mean.median()), 1),
        "nori_median_test": round(float(res.cloud_mean.median()), 1),
        "baterii_median": round(float(worst.battery_pv_share.median()), 3),
        "sens_pv_median": round(float(worst.sens_pv_pu.median()), 4),
        "sens_pv_median_test": round(float(res.sens_pv_pu.median()), 4),
    }
    return t


def main() -> None:
    t = tables()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "error_tables.json").write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(t, indent=1, ensure_ascii=False)[:6000])


if __name__ == "__main__":
    _ = np
    main()
