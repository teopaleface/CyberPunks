"""Experiment (ramura Eden): ajută mai mulți ani de vreme, mai multe regiuni și variabile meteo noi la modelul C?

Aceleași 480 de posturi sintetice de antrenare (aceleași specificații SimBench, același seed), aceeași fizică,
aceeași schemă de evaluare: o topologie lăsată deoparte × luni nevăzute (test ≥ 2025-01-01). Variantele:

1. `baza`: vremea București 2023-2024 la antrenare (ca modelul livrat).
2. `mai_multi_ani`: vremea București 2015-2024 la antrenare (de 5 ori mai multe zile, mai multe tipuri de vreme).
3. `mai_multe_regiuni`: + aceleași posturi simulate cu vremea din Timișoara, Cluj, Iași și Constanța (2019-2024).
   Testul se face și pe regiunile acestea (2025+), ca să vedem dacă modelul învățat la București merge în alte
   zone ale țării.
4. Fizică mai realistă (`fizica_v2`): răcirea panourilor de către vânt (modelul Faiman) și panourile acoperite de
   zăpadă. Etichetele se schimbă, deci se compară doar între ele: modelul fără vânt și zăpadă față de modelul
   care le vede ca trăsături (`fizica_v2_fara_vant_zapada` față de `fizica_v2_cu_vant_zapada`).

Etichetele sunt din simulare fizică pe rețele SINTETICE (ca la modelul livrat).

    uv run python -m cyberpunks.c_prosumatori.experiments_extra sim        # simulările (~15 min, 4 procese)
    uv run python -m cyberpunks.c_prosumatori.experiments_extra eval       # reports/C/experiments_extra.json
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import features as F
from cyberpunks.c_prosumatori import simulate, weather
from cyberpunks.c_prosumatori import train as T
from cyberpunks.common.paths import DATA_PROCESSED, REPORTS

OUT = REPORTS / "C" / "experiments_extra.json"
EXTRA = weather.RAW / "extra"
END = "2026-11-06"
CITIES = {"bucuresti": "2015-01-01", "timisoara": "2019-01-01", "cluj": "2019-01-01", "iasi": "2019-01-01",
          "constanta": "2019-01-01"}

# Faiman (IEC 61853-2; valorile implicite din PVsyst / pvlib): T_celulă = T_aer + G / (U0 + U1 · v)
FAIMAN_U0, FAIMAN_U1 = 25.0, 6.84
WIND_10M_TO_MODULE = 0.67  # IPOTEZĂ: vântul la înălțimea acoperișului (~3 m) din cel la 10 m, profil logaritmic
SNOW_COVER_M = 0.03  # IPOTEZĂ: de la 3 cm de zăpadă la sol, panourile sunt considerate acoperite
SNOW_GTI_FACTOR = 0.2  # IPOTEZĂ: un panou acoperit mai produce ~20% (lumină prin stratul subțire, margini libere)


def city_weather(city: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(coloanele modelului livrat, variabilele noi: vânt, zăpadă, umiditate), index UTC."""
    path = EXTRA / f"openmeteo_archive_utc_{city}_{CITIES[city]}_{END}.json"
    wx = weather.read_openmeteo(path)
    h = json.loads(path.read_text())["hourly"]
    ex = pd.DataFrame({"wind": h["wind_speed_10m"], "snow_depth": h["snow_depth"], "rh": h["relative_humidity_2m"]},
                      index=wx.index, dtype=float)
    return wx, ex


def physics_v2(wx: pd.DataFrame, ex: pd.DataFrame) -> pd.DataFrame:
    """Vremea „efectivă” pentru simulare: GTI redus când panoul e sub zăpadă și temperatura echivalentă care, prin
    formula livrată (T + NOCT_K·G), dă temperatura celulei din modelul Faiman cu vânt."""
    out = wx.copy()
    snow = ex["snow_depth"].fillna(0).to_numpy() >= SNOW_COVER_M
    out["gti"] = np.where(snow, out["gti"] * SNOW_GTI_FACTOR, out["gti"])
    g = np.clip(np.nan_to_num(out["gti"].to_numpy()), 0, 1400)
    v = ex["wind"].fillna(ex["wind"].median()).to_numpy() / 3.6 * WIND_10M_TO_MODULE  # km/h -> m/s
    t_cell = out["temp"].to_numpy() + g / (FAIMAN_U0 + FAIMAN_U1 * v)
    out["temp"] = t_cell - weather.NOCT_K * g
    return out


def yearly_yield(wx: pd.DataFrame) -> dict[int, float]:
    return weather.annual_yield_check(wx)


# ------------------------------------------------------------------------------------------
# simulările
# ------------------------------------------------------------------------------------------

def run_pool_with(name: str, wx_sim: pd.DataFrame, workers: int = 4) -> None:
    if (DATA_PROCESSED / "C" / name / "daily.parquet").exists():
        print(f"{name}: există deja")
        return
    orig = simulate.weather_inputs
    from cyberpunks.c_prosumatori import profiles

    simulate.weather_inputs = lambda *a, **k: (wx_sim, profiles.shapes_for(wx_sim.index), profiles.system_load_index(wx_sim.index))
    try:
        t0 = time.perf_counter()
        simulate.run_pool(name, simulate.train_specs(80), workers=workers)
        print(f"{name}: {time.perf_counter() - t0:.0f} s", flush=True)
    finally:
        simulate.weather_inputs = orig


def sim() -> None:
    for city in CITIES:
        wx, ex = city_weather(city)
        print(city, "kWh/kWp pe an, fizica livrată:", yearly_yield(wx), "| fizica v2:", yearly_yield(physics_v2(wx, ex)), flush=True)
        run_pool_with(f"x_{city}", wx)
    wx, ex = city_weather("bucuresti")
    run_pool_with("x_bucuresti_v2", physics_v2(wx, ex))


# ------------------------------------------------------------------------------------------
# trăsăturile și evaluarea
# ------------------------------------------------------------------------------------------

NEW_FEATURES = ["wind_noon", "snow_depth_max", "rh_noon"]


def daily_extra(ex: pd.DataFrame) -> pd.DataFrame:
    loc = ex.index.tz_convert(weather.TZ) - pd.Timedelta(hours=1)
    df = ex.assign(date=loc.date, hour=loc.hour)
    noon = df[(df.hour >= F.NOON_WINDOW[0]) & (df.hour < F.NOON_WINDOW[1])]
    return pd.DataFrame({"wind_noon": noon.groupby("date")["wind"].mean(), "rh_noon": noon.groupby("date")["rh"].mean(),
                         "snow_depth_max": df.groupby("date")["snow_depth"].max()}).reset_index().rename(columns={"index": "date"})


def load_pool(name: str, city: str) -> pd.DataFrame:
    """Ca `train.load_daily`, dar cu vremea orașului (trăsăturile din vremea brută, nu din cea „efectivă”)."""
    base = DATA_PROCESSED / "C" / name
    cache = base / "daily_features_x.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    wx, ex = city_weather(city)
    posts = pd.read_parquet(base / "posts.parquet")
    labels = pd.read_parquet(base / "daily.parquet")
    X = F.daily_features(posts, F.hourly_weather(wx))
    df = X.merge(labels, on=["post_id", "date"], how="inner").merge(posts[["post_id", "topology"]], on="post_id")
    df = df.merge(daily_extra(ex), on="date", how="left")
    df["exceed"] = (df["vmax_day"] > T.LIMIT).astype(int)
    df["city"] = city
    df.to_parquet(cache)
    return df


BASE_TRAIN_ROWS = 480 * 731  # 480 de posturi × 2023-2024: mărimea antrenării modelului livrat


def lotu_eval(train: pd.DataFrame, tests: dict[str, pd.DataFrame], feats: list[str]) -> dict:
    """Topologia de test nu e văzută la antrenare. Întoarce scorurile pe fiecare set de test.

    Calibrarea folosește un eșantion de zile de aceeași mărime ca la modelul livrat (35% din 2023-2024), ca
    variantele cu mai multe date să nu dureze ore; modelul în sine se antrenează pe toate rândurile."""
    from cyberpunks.c_prosumatori.evaluate import scores

    oof_frac = min(0.35, 0.35 * BASE_TRAIN_ROWS / max(len(train), 1))

    preds = {k: [] for k in tests}
    for t in sorted(train["topology"].unique()):
        tr = train[train.topology != t]
        oof = T.logo_oof(T.sample_for_oof(tr, oof_frac), feats)
        model = T.DailyModel(features=list(feats)).fit(tr, calib=oof)
        for k, te_all in tests.items():
            te = te_all[te_all.topology == t].copy()
            pm = model.predict(te)
            for c, v in pm.items():
                te[f"m_{c}"] = v
            preds[k].append(te)
        print(f"    topologia {t} gata", flush=True)
    out = {}
    for k, parts in preds.items():
        r = pd.concat(parts, ignore_index=True)
        p = {c: r[f"m_{c}"].to_numpy() for c in ("q10", "q50", "q90", "p_exceed")}
        s = scores(r["vmax_day"].to_numpy(), r["exceed"].to_numpy(), p)
        out[k] = {m: round(float(v), 5) for m, v in s.items() if m in
                  ("mae_vmax_pu", "coverage_p10_p90", "pr_auc_exceed", "recall_exceed", "precision_exceed", "brier", "exceed_rate")}
        out[k]["test_rows"] = len(r)
    return out


def evaluate(only: list[str] | None = None) -> int:
    split = pd.Timestamp(T.SPLIT_DATE)
    pools = {c: load_pool(f"x_{c}", c) for c in CITIES}
    for d in pools.values():
        d["date"] = pd.to_datetime(d["date"])
    buc = pools["bucuresti"]
    tests = {"bucuresti_2025": buc[buc.date >= split]}
    for c in CITIES:
        if c != "bucuresti":
            tests[f"{c}_2025"] = pools[c][pools[c].date >= split]
    feats = list(F.DAILY_FEATURES)
    others = pd.concat([pools[c][(pools[c].date < split)] for c in CITIES if c != "bucuresti"], ignore_index=True)
    variants = {
        "baza": ("vremea București 2023-2024 (ca modelul livrat)", buc[(buc.date >= "2023-01-01") & (buc.date < split)], feats),
        "mai_multi_ani": ("vremea București 2015-2024", buc[buc.date < split], feats),
        "mai_multe_regiuni": ("București 2023-2024 + Timișoara, Cluj, Iași, Constanța 2019-2024",
                              pd.concat([buc[(buc.date >= "2023-01-01") & (buc.date < split)], others], ignore_index=True), feats),
        "ani_si_regiuni": ("București 2015-2024 + celelalte 4 regiuni 2019-2024",
                           pd.concat([buc[buc.date < split], others], ignore_index=True), feats),
    }
    rows = []
    for name, (desc, tr, ff) in variants.items():
        if only and name not in only:
            continue
        t0 = time.perf_counter()
        print(f"{name}: {len(tr):,} zile-post la antrenare", flush=True)
        res = lotu_eval(tr, tests, ff)
        rows.append({"varianta": name, "ce": desc, "train_rows": len(tr), "seconds": round(time.perf_counter() - t0), **res})
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
        _write(rows)

    # fizica v2: etichetele cu vânt și zăpadă; trăsăturile din vremea brută, fără și cu variabilele noi
    if not only or any(n.startswith("fizica") for n in only):
        v2 = load_pool("x_bucuresti_v2", "bucuresti")
        v2["date"] = pd.to_datetime(v2["date"])
        tr2 = v2[(v2.date >= "2023-01-01") & (v2.date < split)]
        te2 = {"bucuresti_2025_fizica_v2": v2[v2.date >= split]}
        for name, desc, ff in [("fizica_v2_fara_vant_zapada", "etichete cu vânt și zăpadă, trăsăturile livrate", feats),
                               ("fizica_v2_cu_vant_zapada", "etichete cu vânt și zăpadă, + vântul, zăpada, umiditatea", feats + NEW_FEATURES)]:
            t0 = time.perf_counter()
            res = lotu_eval(tr2, te2, ff)
            rows.append({"varianta": name, "ce": desc, "train_rows": len(tr2), "seconds": round(time.perf_counter() - t0), **res})
            print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
            _write(rows)
    return 0


def _write(rows: list[dict]) -> None:
    wx, ex = city_weather("bucuresti")
    meta = {"test": "zile ≥ 2025-01-01, topologia de test nevăzută la antrenare", "etichete": "simulare fizică, rețele SINTETICE",
            "kwh_per_kwp_bucuresti": {"fizica_livrata": yearly_yield(wx), "fizica_v2": yearly_yield(physics_v2(wx, ex)),
                                      "pvgis_referinta": 1282},
            "ipoteze_fizica_v2": {"faiman_u0": FAIMAN_U0, "faiman_u1": FAIMAN_U1, "vant_10m_la_panou": WIND_10M_TO_MODULE,
                                  "zapada_acopera_de_la_m": SNOW_COVER_M, "factor_gti_sub_zapada": SNOW_GTI_FACTOR},
            "note": "experiment pe ramura Eden; modelul livrat nu e schimbat"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"meta": meta, "rows": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "eval"])
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    if a.cmd == "sim":
        sim()
        return 0
    return evaluate([x for x in a.only.split(",") if x] or None)


if __name__ == "__main__":
    raise SystemExit(main())
