"""Experiment (ramura Eden): ajută mai multe gospodării la antrenare și vremea din Londra la modelul A?

Setul de test rămâne exact cel al modelului livrat: aceleași gospodării nevăzute, aceeași perioadă ulterioară
(sept. 2013 - feb. 2014), aceleași probleme injectate (același seed). Variantele schimbă doar antrenarea:

1. `baza`: modelul livrat (45 de fișiere LCL, ~1.500 de gospodării cu tarif fix).
2. `mai_multe_gospodarii`: plus toate gospodăriile din celelalte 123 de fișiere LCL (tarif fix și tarif dinamic
   ToU), puse DOAR în antrenare (calibrarea și testul nu se schimbă).
3. `vreme`: features noi din temperatura zilnică la Londra (Open-Meteo, ERA5): grade-zile de încălzire în fereastra
   recentă față de istoric, cât de sensibilă e gospodăria la frig și raportul recent/istoric corectat cu vremea.
   Ideea: o scădere de consum primăvara e vremea, nu furt.
4. `mai_multe_gospodarii_si_vreme`: ambele.

Etichetele sunt SINTETICE (probleme injectate peste consum real), ca în modelul livrat.

    uv run python -m cyberpunks.a_contoare.experiments_extra       # reports/A/experiments_extra.json
"""

from __future__ import annotations

import json
from typing import Self

import httpx
import numpy as np
import pandas as pd

from cyberpunks.a_contoare import features as F
from cyberpunks.a_contoare import lcl
from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.evaluate import OBVIOUS_KINDS
from cyberpunks.a_contoare.model import MeterModel
from cyberpunks.a_contoare.train import ALPHA_NORMAL, ALPHA_PROBLEM, DETERMINISTIC, FAMILY_TO_Y, LCL_CLASSES
from cyberpunks.common.paths import DATA_INTERIM, DATA_RAW, REPORTS

OUT = REPORTS / "A" / "experiments_extra.json"
EXTRA_DIR = DATA_INTERIM / "A" / "extra"
WX_FILE = DATA_RAW / "A" / "london_daily_temperature.json"
LONDON = (51.51, -0.13)
HDD_BASE_C = 15.5  # pragul britanic pentru grade-zile de încălzire
BASE_FILES = 45
ALL_FILES = 168
WX_FEATURES = ["hdd_recent", "hdd_delta", "temp_sens", "wx_expected_ratio", "ratio_vs_wx"]


# ------------------------------------------------------------------------------------------
# vremea la Londra
# ------------------------------------------------------------------------------------------

def london_temperature() -> pd.Series:
    """Temperatura medie zilnică la Londra, indexată pe ziua din tabloul LCL (0 = CAL_START)."""
    if not WX_FILE.exists():
        params = {"latitude": LONDON[0], "longitude": LONDON[1], "start_date": f"{lcl.CAL_START:%Y-%m-%d}",
                  "end_date": f"{lcl.CAL_END:%Y-%m-%d}", "daily": "temperature_2m_mean", "timezone": "Europe/London"}
        r = httpx.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=120,
                      headers={"User-Agent": "cyberpunks-smarthack-2026 (research, non-commercial)"})
        r.raise_for_status()
        WX_FILE.parent.mkdir(parents=True, exist_ok=True)
        WX_FILE.write_bytes(r.content)
    d = json.loads(WX_FILE.read_text())["daily"]
    s = pd.Series(d["temperature_2m_mean"], index=pd.to_datetime(d["time"]), dtype=float)
    return pd.Series(s.to_numpy(), index=(s.index - lcl.CAL_START).days)


def weather_features(x: np.ndarray, end_days: np.ndarray, temp: pd.Series, recent: int = lcl.RECENT) -> pd.DataFrame:
    """`x`: (n, WINDOW) kWh pe zi, cum îl vede modelul; `end_days`: ziua de evaluare a fiecărui rând."""
    w = x.shape[1]
    tvec = temp.reindex(np.arange(temp.index.min(), temp.index.max() + 1)).to_numpy()
    offs = np.arange(-w + 1, 1)
    t = tvec[np.clip(end_days[:, None] + offs[None, :] - int(temp.index.min()), 0, len(tvec) - 1)]
    hdd = np.clip(HDD_BASE_C - t, 0, None)
    base, rec = slice(0, w - recent), slice(w - recent, w)
    hdd_b, hdd_r = np.nanmean(hdd[:, base], axis=1), np.nanmean(hdd[:, rec], axis=1)
    # regresia consumului pe grade-zile, pe istoric (fără fereastra recentă, unde poate fi problema)
    xb, hb = x[:, base], hdd[:, base]
    ok = np.isfinite(xb) & np.isfinite(hb)
    cnt = ok.sum(axis=1).clip(min=1)
    mx = np.where(ok, xb, 0).sum(axis=1) / cnt
    mh = np.where(ok, hb, 0).sum(axis=1) / cnt
    cov = np.where(ok, (xb - mx[:, None]) * (hb - mh[:, None]), 0).sum(axis=1)
    var = np.where(ok, (hb - mh[:, None]) ** 2, 0).sum(axis=1)
    slope = np.where(var > 1e-6, cov / np.maximum(var, 1e-6), 0.0)
    a = mx - slope * mh
    pred_b, pred_r = a + slope * hdd_b, a + slope * hdd_r
    with np.errstate(all="ignore"):
        exp_ratio = np.where(pred_b > F.MIN_DENOMINATOR_KWH, np.clip(pred_r, 0, None) / pred_b, np.nan)
        act_ratio = np.nanmean(x[:, rec], axis=1) / np.where(mx > F.MIN_DENOMINATOR_KWH, mx, np.nan)
        ratio_vs = act_ratio / np.where(exp_ratio > 0.05, exp_ratio, np.nan)
        sens = slope / np.where(mx > F.MIN_DENOMINATOR_KWH, mx, np.nan)
    return pd.DataFrame({
        "hdd_recent": hdd_r, "hdd_delta": hdd_r - hdd_b, "temp_sens": np.clip(sens, -1, 1),
        "wx_expected_ratio": np.clip(exp_ratio, 0, F.RATIO_CAP), "ratio_vs_wx": np.clip(ratio_vs, 0, F.RATIO_CAP),
    })


# ------------------------------------------------------------------------------------------
# eșantioanele: setul livrat și gospodăriile în plus (doar antrenare)
# ------------------------------------------------------------------------------------------

class _Capture:
    """Prinde seria zilnică văzută de model, ca să calculăm features de vreme pe aceleași rânduri."""

    def __init__(self) -> None:
        self.x: np.ndarray | None = None
        self._orig = lcl.daily_features

    def __enter__(self) -> Self:
        def wrapped(x: np.ndarray, peer: np.ndarray | None = None, *a, **k) -> pd.DataFrame:
            self.x = np.asarray(x)
            return self._orig(x, peer, *a, **k)

        lcl.daily_features = wrapped
        return self

    def __exit__(self, *exc) -> None:
        lcl.daily_features = self._orig


def _with_weather(s: pd.DataFrame, x: np.ndarray, temp: pd.Series) -> pd.DataFrame:
    end_days = (pd.to_datetime(s["date"]) - lcl.CAL_START).dt.days.to_numpy()
    return pd.concat([s.reset_index(drop=True), weather_features(x, end_days, temp)], axis=1)


def base_samples(temp: pd.Series) -> pd.DataFrame:
    path = EXTRA_DIR / "base_samples_wx.parquet"
    if path.exists():
        return pd.read_parquet(path)
    names = [f"LCL-June2015v2_{k}.csv" for k in range(BASE_FILES)]
    orig = (lcl.expected_lcl_files, lcl.HH_NPY, lcl.HH_META, lcl.SAMPLES)
    lcl.expected_lcl_files = lambda: names
    lcl.HH_NPY, lcl.HH_META, lcl.SAMPLES = EXTRA_DIR / "base_hh.npy", EXTRA_DIR / "base_meta.parquet", EXTRA_DIR / "base_samples.parquet"
    try:
        EXTRA_DIR.mkdir(parents=True, exist_ok=True)
        with _Capture() as cap:
            s = lcl.build_samples(force=True)
        out = _with_weather(s, cap.x, temp)
    finally:
        lcl.expected_lcl_files, lcl.HH_NPY, lcl.HH_META, lcl.SAMPLES = orig
    out.to_parquet(path, index=False)
    return out


def extra_train_samples(temp: pd.Series) -> pd.DataFrame:
    """Gospodăriile din fișierele 45-167, toate în antrenare (aceleași date de evaluare ca setul de antrenare)."""
    path = EXTRA_DIR / "extra_samples_wx.parquet"
    if path.exists():
        return pd.read_parquet(path)
    names = [f"LCL-June2015v2_{k}.csv" for k in range(BASE_FILES, ALL_FILES)]
    orig = (lcl.expected_lcl_files, lcl.HH_NPY, lcl.HH_META, lcl.SAMPLES, lcl.split_households)
    lcl.expected_lcl_files = lambda: names
    lcl.HH_NPY, lcl.HH_META, lcl.SAMPLES = EXTRA_DIR / "extra_hh.npy", EXTRA_DIR / "extra_meta.parquet", EXTRA_DIR / "extra_samples.parquet"
    lcl.split_households = lambda n, seed=lcl.SEED: np.array(["train"] * n, dtype=object)
    try:
        with _Capture() as cap:
            s = lcl.build_samples(force=True, seed=lcl.SEED + 1000)  # alt seed: alte injecții decât în setul de bază
        out = _with_weather(s, cap.x, temp)
    finally:
        lcl.expected_lcl_files, lcl.HH_NPY, lcl.HH_META, lcl.SAMPLES, lcl.split_households = orig
    out["sample_id"] = "X" + out["sample_id"].astype(str)
    out.to_parquet(path, index=False)
    return out


# ------------------------------------------------------------------------------------------
# antrenare și evaluare, pe același test
# ------------------------------------------------------------------------------------------

def fit_eval(train: pd.DataFrame, cal: pd.DataFrame, test: pd.DataFrame, feats: list[str], params: dict | None = None) -> dict:
    y = train["family"].map(FAMILY_TO_Y).to_numpy()
    m = MeterModel("a-lgbm-exp", feats, LCL_CLASSES).fit(train, y, params={**DETERMINISTIC, **(params or {})},
                                                          groups=train["household"].to_numpy())
    m.calibrate(cal, cal["problem"].to_numpy(), alpha_normal=ALPHA_NORMAL, alpha_problem=ALPHA_PROBLEM)
    s = m.predict(test)["score"].to_numpy()
    y_te = test["problem"].to_numpy()
    subtle = ~(test["kind"].isin(OBVIOUS_KINDS) & (test["problem"] == 1)).to_numpy()
    ys, ss = y_te[subtle], s[subtle]
    k = M.k_for(int(subtle.sum()))
    return {
        "subtle_precision_at_k": round(M.precision_at_k(ys, ss, k), 4),
        "subtle_recall_at_k": round(M.recall_at_k(ys, ss, k), 4),
        "subtle_pr_auc": round(M.pr_auc(ys, ss), 4),
        "subtle_precision_at_5pct": round(M.precision_at_k(ys, ss, M.k_for(int(subtle.sum()), 0.05)), 4),
        "pr_auc": round(M.pr_auc(y_te, s), 4),
        "n_train": len(train), "households_train": int(train["household"].nunique()),
        "_scores": ss, "_y": ys, "_groups": test["household"].to_numpy()[subtle],
    }


def paired_ci(r0: dict, r1: dict, n: int = 400, seed: int = 0) -> list[float]:
    """Interval 90% pentru diferența de PR-AUC pe problemele subtile, reeșantionând gospodării."""
    g = r0["_groups"]
    uniq = np.unique(g)
    idx = {u: np.flatnonzero(g == u) for u in uniq}
    rng = np.random.default_rng(seed)
    d = []
    for _ in range(n):
        ii = np.concatenate([idx[u] for u in rng.choice(uniq, len(uniq))])
        if r0["_y"][ii].sum() == 0:
            continue
        d.append(M.pr_auc(r1["_y"][ii], r1["_scores"][ii]) - M.pr_auc(r0["_y"][ii], r0["_scores"][ii]))
    return [round(float(v), 4) for v in np.percentile(d, [5, 95])]


def main() -> int:
    np.seterr(all="ignore")
    MeterModel.save = lambda self, *a, **k: None  # experimentul nu suprascrie modelele
    temp = london_temperature()
    base = base_samples(temp)
    extra = extra_train_samples(temp)
    tr, ca, te = (base[base.split == x].reset_index(drop=True) for x in ("train", "cal", "test"))
    tr_more = pd.concat([tr, extra], ignore_index=True)
    feats0, feats_wx = list(F.ALL_FEATURES), list(F.ALL_FEATURES) + WX_FEATURES
    variants = [
        ("baza", "modelul livrat (45 de fișiere LCL)", tr, feats0),
        ("mai_multe_gospodarii", "+ gospodăriile din celelalte 123 de fișiere LCL, doar la antrenare", tr_more, feats0),
        ("vreme", "+ grade-zile la Londra, sensibilitatea la frig, raportul corectat cu vremea", tr, feats_wx),
        ("mai_multe_gospodarii_si_vreme", "ambele", tr_more, feats_wx),
    ]
    rows, r0 = [], None
    for name, desc, train, feats in variants:
        r = fit_eval(train, ca, te, feats)
        if r0 is None:
            r0 = r
        else:
            r["delta_subtle_pr_auc_ci90"] = paired_ci(r0, r)
        rows.append({"varianta": name, "ce": desc, **{k: v for k, v in r.items() if not k.startswith("_")}})
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    meta = {"test": "setul de test livrat (gospodării nevăzute, sept. 2013 - feb. 2014)", "n_test": len(te),
            "etichete": "SINTETICE: probleme injectate peste consum real", "note": "experiment pe ramura Eden"}
    OUT.write_text(json.dumps({"meta": meta, "rows": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
