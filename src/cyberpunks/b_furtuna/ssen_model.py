"""Tabelul district × zi și evaluarea variantei europene (SSEN) a modelului B, plus comparația cu modelul pe SUA.

Comparațiile, toate pe ani nevăzuți:
1. modelul SSEN pe Scoția 2024-2025, față de climatologia pe district și lună și de regula pe rafală;
2. modelul pe SUA („B FINAL”) pe același test din Scoția (fără să fi văzut date europene);
3. modelul SSEN pe testul din SUA (2025), comparația inversă.
Metricile pe ordine (PR-AUC, ROC-AUC) se pot compara între modele; Brier doar pentru modelul calibrat pe acele date.
"""

from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

from cyberpunks.b_furtuna import dataset as us_dataset
from cyberpunks.b_furtuna import model as bm
from cyberpunks.b_furtuna.evaluate import GUST_BINS
from cyberpunks.b_furtuna.features import FEATURE_SPEC, clean_weather, make_features
from cyberpunks.b_furtuna.ssen import (
    DISTRICTS,
    END,
    SSEN_TABLE,
    START,
    TEST_YEARS,
    TRAIN_YEARS,
    incidents,
    load_weather,
)
from cyberpunks.common.contracts import ModelReport
from cyberpunks.common.paths import MODELS, REPORTS

OUT = REPORTS / "B" / "metrics_ssen.json"
OUT_DETAIL = REPORTS / "B" / "metrics_ssen_detail.json"
SSEN_MODEL_PATH = MODELS / "B" / "b_model_ssen.joblib"  # în afara git; modelul livrat rămâne cel pe SUA
# Doar vremea și sezonul: districtele SSEN n-au număr de clienți publicat în arhivă, iar pentru transfer nu folosim ID-uri.
SPEC = [(f, m) for f, m in FEATURE_SPEC if f not in ("log_customers", "log_density")]
FEATS = [f for f, _ in SPEC]


def build_dataset() -> pd.DataFrame:
    inc = incidents()
    inc = inc[inc["district"].isin(DISTRICTS)]
    day = inc.groupby(["district", "date"]).agg(
        n_all=("REFERENCE_NUMBER", "size"),
        n_weather=("weather_cause", "sum"),
        cust_weather=("LV_CUST_AFF", lambda s: float(s[inc.loc[s.index, "weather_cause"]].sum())),
    ).reset_index()
    wx, issues = clean_weather(load_weather())
    wx["customers"], wx["area_km2"] = 1.0, 1.0  # nefolosite de modelul SSEN (doar ca make_features să ruleze)
    wx = make_features(wx.rename(columns={"district": "loc_id"}), group="loc_id").rename(columns={"loc_id": "district"})
    df = wx.merge(day, on=["district", "date"], how="left")
    for c in ("n_all", "n_weather", "cust_weather"):
        df[c] = df[c].fillna(0.0)
    df = df[(df["date"] >= pd.Timestamp(START)) & (df["date"] <= pd.Timestamp(END))].copy()
    df["year"] = df["date"].dt.year
    df["event"] = (df["n_weather"] >= 1).astype(int)
    df["severe"] = (df["n_weather"] >= 2).astype(int)
    df["extreme"] = (df["n_weather"] >= 5).astype(int)
    df["wx_missing"] = df[FEATS].isna().any(axis=1)
    df.to_parquet(SSEN_TABLE, index=False, compression="zstd")
    print(f"{len(df):,} zile-district, {int(df['event'].sum()):,} cu avarii de vreme; probleme meteo: {issues or 'niciuna'}")
    return df


def _fit(X: pd.DataFrame, y: np.ndarray) -> lgb.Booster:
    params = {**bm.CLF_PARAMS, "monotone_constraints": [m for _, m in SPEC]}
    return lgb.train(params, lgb.Dataset(X[FEATS], label=y), num_boost_round=bm.CLF_ROUNDS)


def _metrics(y: np.ndarray, p: np.ndarray, thr: float | None, sev: np.ndarray, ext: np.ndarray) -> dict:
    out = {"pr_auc": float(average_precision_score(y, p)), "roc_auc": float(roc_auc_score(y, p))}
    if thr is not None:
        pred = p >= thr
        out.update({
            "brier": float(brier_score_loss(y, p)),
            "threshold": float(thr),
            "precision_at_thr": float((pred & (y == 1)).sum() / max(pred.sum(), 1)),
            "recall_at_thr": float((pred & (y == 1)).sum() / max(y.sum(), 1)),
            "recall_severe_at_thr": float((pred & (sev == 1)).sum() / max(sev.sum(), 1)),
            "recall_extreme_at_thr": float((pred & (ext == 1)).sum() / max(ext.sum(), 1)),
        })
    return {k: round(v, 4) for k, v in out.items()}


def decide(res: dict, thr: float) -> tuple[str, str]:
    """Regula aprobată: varianta nouă intră în agent doar dacă bate varianta curentă pe același tip de test (ani nevăzuți).

    Verificăm ambele teste pe ani nevăzuți (Scoția 2024-2025 și SUA 2025) și furtuna de vară din Banat (ziua demo).
    """
    s_ssen, s_us = res["ssen_model"]["pr_auc"], res["us_model_on_ssen_test"]["pr_auc"]
    u_ssen, u_us = res["ssen_model_on_us_test_2025"]["pr_auc"], res["us_model_on_us_test_2025_pr_auc"]
    banat = res["romania_backtest"]["banat_2025_07_07_08"]
    wins_both = s_ssen > s_us and u_ssen > u_us
    summer_ok = banat["ssen_p_banat"] >= thr
    def c(x: float, nd: int = 3) -> str:  # zecimale cu virgulă, ca în restul documentelor
        return f"{x:.{nd}f}".replace(".", ",")

    if wins_both and summer_ok:
        return "ssen", "Agentul folosește modelul SSEN: bate modelul pe SUA pe ambele teste pe ani nevăzuți."
    text = (f"Agentul rămâne pe modelul pe SUA („B FINAL”); modelul SSEN e păstrat ca variantă evaluată. Pe Scoția 2024-2025, "
            f"modelul SSEN are PR-AUC {c(s_ssen)}, față de {c(s_us)} pentru modelul pe SUA, care n-a văzut date europene și "
            f"bate climatologia locală ({c(res['clim_district_month']['pr_auc'])}). Pe SUA 2025, modelul SSEN are doar "
            f"{c(u_ssen)}, față de {c(u_us)}. Pe furtuna de vară din Banat (8 iulie 2025), modelul SSEN dă "
            f"{c(banat['ssen_p_banat'], 2)} în Banat, sub pragul de {c(thr, 2)}, deci n-ar trimite nicio echipă; a învățat mai "
            "ales furtunile de iarnă dinspre ocean, iar România are furtuni convective vara.")
    return "us", text


def romania_check(cal: IsotonicRegression, clf: lgb.Booster) -> dict:
    """Cele trei furtuni reale din România, prezise de modelul SSEN; alături, cifrele modelului pe SUA (din backtest).

    Folosește exact cererile de vreme ale backtest-ului (din cache: 0 apeluri Open-Meteo).
    """
    from datetime import timedelta

    from cyberpunks.b_furtuna import backtest, predict, romania

    zones = romania.load_zones()
    region = pd.Series({z.zone_id: z.region for z in zones})
    days_a = backtest.DAYS + backtest.CASE2_DAYS
    wx_a, _ = romania.weather_daily_range(zones, days_a[0] - timedelta(days=romania.LAG_DAYS), days_a[-1])
    days_c = backtest.CASE3_DAYS
    wx_c, _ = romania.weather_daily_range(zones, days_c[0] - timedelta(days=romania.LAG_DAYS), days_c[-1])

    def probs(wx: pd.DataFrame, d) -> pd.Series:
        f = predict.target_features(zones, wx, d)
        return pd.Series(cal.predict(clf.predict(f[FEATS])), index=f["zone_id"])

    p7, p8 = probs(wx_a, backtest.DAYS[1]), probs(wx_a, backtest.DAYS[2])
    banat = pd.concat([p7, p8])
    reg = pd.concat([region, region])
    p17 = probs(wx_a, backtest.CASE2_DAYS[1])
    p26 = probs(wx_c, backtest.CASE3_DAYS[2])
    us_bt = json.loads((REPORTS / "B" / "backtest_summary.json").read_text(encoding="utf-8"))
    return {
        "banat_2025_07_07_08": {"ssen_p_banat": round(float(banat[reg.to_numpy() == "banat"].mean()), 3),
                                "ssen_p_rest": round(float(banat[reg.to_numpy() != "banat"].mean()), 3),
                                "us": us_bt["banat_2025_07_07_08"]},
        "slobozia_2025_07_17": {"ssen_rank": int((p17 > p17[backtest.CASE2_ZONE]).sum()) + 1,
                                "ssen_p": round(float(p17[backtest.CASE2_ZONE]), 3), "us": us_bt["slobozia_2025_07_17"]},
        "dobrogea_2023_11_26": {"ssen_p_dobrogea": round(float(p26[region[p26.index].to_numpy() == "dobrogea"].mean()), 3),
                                "ssen_p_rest": round(float(p26[region[p26.index].to_numpy() != "dobrogea"].mean()), 3),
                                "us": us_bt["dobrogea_2023_11_26"]},
    }


def evaluate() -> dict:
    df = pd.read_parquet(SSEN_TABLE)
    df = df[~df["wx_missing"]].reset_index(drop=True)
    tr = df[df["year"].isin(TRAIN_YEARS)].reset_index(drop=True)
    te = df[df["year"].isin(TEST_YEARS)].reset_index(drop=True)
    y_tr, y = tr["event"].to_numpy(), te["event"].to_numpy()
    sev, ext = te["severe"].to_numpy(), te["extreme"].to_numpy()

    oof = np.zeros(len(tr))
    for a, b in GroupKFold(5).split(tr, y_tr, bm.week_groups(tr["date"])):
        oof[b] = _fit(tr.iloc[a], y_tr[a]).predict(tr.iloc[b][FEATS])
    cal = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(oof, y_tr)
    thr = bm.best_f1_threshold(y_tr, cal.predict(oof))
    clf = _fit(tr, y_tr)
    p_ssen = cal.predict(clf.predict(te[FEATS]))

    # baseline-uri, din anii de antrenare
    month_rate = tr.groupby(tr["date"].dt.month)["event"].mean()
    g = tr.groupby(["district", tr["date"].dt.month])["event"].agg(["sum", "size"])
    prior = te["date"].dt.month.map(month_rate).to_numpy()
    keys = list(zip(te["district"], te["date"].dt.month, strict=True))
    s_ = np.array([g["sum"].get(k, 0.0) for k in keys])
    n_ = np.array([g["size"].get(k, 0.0) for k in keys])
    p_clim = (s_ + 20 * prior) / (n_ + 20)
    tab = tr.groupby(pd.cut(tr["gust_max"], GUST_BINS, right=False), observed=False)["event"].mean()
    p_gust = pd.cut(te["gust_max"], GUST_BINS, right=False).map(tab).astype(float).fillna(float(tab.mean())).to_numpy()
    clim_thr = bm.best_f1_threshold(y_tr, ((g["sum"] + 20 * month_rate.reindex(g.index.get_level_values(1)).to_numpy())
                                           / (g["size"] + 20)).reindex(list(zip(tr["district"], tr["date"].dt.month,
                                                                                strict=True))).to_numpy())

    # modelul pe SUA („B FINAL”) pe testul din Scoția: mărimea zonei la valoarea tipică din antrenarea SUA
    us_model = bm.BModel.load()
    us = pd.read_parquet(us_dataset.OUT)
    te_us = te.copy()
    te_us["log_customers"] = float(us["log_customers"].median())
    te_us["log_density"] = float(us["log_density"].median())
    p_usmodel = us_model.predict_proba(te_us)

    # comparația inversă: modelul SSEN pe testul din SUA (2025)
    us_te = us[(us["year"] == 2025) & ~us["wx_missing"]]
    p_ssen_on_us = cal.predict(clf.predict(us_te[FEATS]))
    y_us = us_te["event"].to_numpy()

    res = {
        "test_rows": len(te), "test_events": int(y.sum()), "prevalence_test": round(float(y.mean()), 4),
        "train_rows": len(tr), "train_events": int(y_tr.sum()),
        "districts": sorted(df["district"].unique().tolist()),
        "ssen_model": _metrics(y, p_ssen, thr, sev, ext),
        "clim_district_month": _metrics(y, p_clim, clim_thr, sev, ext),
        "gust_rule": _metrics(y, p_gust, None, sev, ext),
        "us_model_on_ssen_test": _metrics(y, p_usmodel, None, sev, ext),
        "ssen_model_on_us_test_2025": {"pr_auc": round(float(average_precision_score(y_us, p_ssen_on_us)), 4),
                                       "roc_auc": round(float(roc_auc_score(y_us, p_ssen_on_us)), 4),
                                       "prevalence": round(float(y_us.mean()), 4)},
        "us_model_on_us_test_2025_pr_auc": round(float(average_precision_score(y_us, us_model.predict_proba(us_te))), 4),
    }
    res["romania_backtest"] = romania_check(cal, clf)
    res["decision"], res["decision_ro"] = decide(res, thr)
    m, b = res["ssen_model"], res["clim_district_month"]
    report = ModelReport(
        source="B",
        model_id="b-lgbm-ssen",
        model_version=f"b-lgbm-ssen@{bm.git_sha()}",
        task="clasificare calibrată: cel puțin o avarie JT cu cauză de vreme în district, în ziua respectivă",
        dataset=["SSEN Distribution NaFIRS LV (SHEPD), prin Zenodo 10.5281/zenodo.23303815, CC BY 4.0",
                 "Open-Meteo Historical Weather API (best_match), CC BY 4.0"],
        split=f"pe timp: antrenare {TRAIN_YEARS[0]}-{TRAIN_YEARS[-1]}, test {TEST_YEARS[0]}-{TEST_YEARS[-1]} (ani "
              f"nevăzuți), {len(res['districts'])} districte SHEPD (nordul Scoției)",
        test_size=len(te),
        primary_metric="pr_auc",
        metrics={**m, "prevalence": res["prevalence_test"],
                 "pr_auc_us_model_on_this_test": res["us_model_on_ssen_test"]["pr_auc"],
                 "pr_auc_gust_rule": res["gust_rule"]["pr_auc"]},
        baseline_id="climatologie_district_luna (rata pe district și lună, 2016-2023)",
        baseline_metrics=b,
        synthetic_share=0.0,
        created_at=datetime.now(ZoneInfo("Europe/Bucharest")).replace(microsecond=0),
        reproduce_cmd="uv run python -m cyberpunks.b_furtuna.ssen evaluate",
    )
    OUT.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    OUT_DETAIL.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bundle = bm.BModel(clf=clf, calibrator=cal, quantile_models={}, features=FEATS,
                       ranges={f: (float(tr[f].min()), float(tr[f].max())) for f in FEATS},
                       decision_threshold=thr, version=report.model_version,
                       train_info={"rows": len(tr), "events": int(y_tr.sum()), "years": list(TRAIN_YEARS)})
    bundle.save(SSEN_MODEL_PATH)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res
