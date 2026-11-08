"""FeederBW: prognoza maximului zilnic măsurat, separat de C (maxim spațial simulat).

    uv run --group bench python -m cyberpunks.benchmark.tensiune_reala --prepare
    uv run --group bench python -m cyberpunks.benchmark.tensiune_reala

Agregatele publicate sunt derivate din FeederBW (Netze BW / KIT), CC BY 4.0,
https://doi.org/10.5281/zenodo.17831177. Numai tensiunea măsurată, fără etichete injectate.
Predicția se emite după încheierea zilei UTC; nu folosește măsurători din ziua țintă.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile

import numpy as np
import pandas as pd

from cyberpunks.benchmark import common as C
from cyberpunks.common.paths import DATA_RAW, DATA_SAMPLES

DAILY = DATA_SAMPLES / "C" / "feederbw_voltage_daily.parquet"
FEATURES = ["v_max", "v_mean", "v_min", "v_std", "v_mean_7d", "v_max_7d", "month_sin", "month_cos", "weekday"]
SOURCE = "https://doi.org/10.5281/zenodo.17831177"
ATTRIBUTION = "Manuel Treutlein, Pascal Bothe, Marc Schmidt, Roman Hahn, Oliver Neumann, Ralf Mikut, Veit Hagenmeyer; Netze BW / KIT"
SEED = 20261108


def aggregate(frame: pd.DataFrame, feeder: int) -> tuple[pd.DataFrame, dict]:
    """O zi validă are ≥95% din minute; citirile anormale nu sunt transformate în normale."""
    ts = pd.to_datetime(frame["timestamp_UTC"], utc=True, errors="coerce")
    v = pd.to_numeric(frame["voltage_one_phase_V"], errors="coerce")
    good = ts.notna() & np.isfinite(v) & v.between(150, 300)
    d = pd.DataFrame({"timestamp": ts[good], "v": v[good]}).drop_duplicates("timestamp")
    daily = d.set_index("timestamp").v.resample("D").agg(["count", "max", "mean", "min", "std"])
    # Numărăm minute distincte: duplicatele subminut nu pot face o zi incompletă să pară completă.
    minute_count = d.groupby(d.timestamp.dt.floor("D")).timestamp.apply(lambda s: s.dt.floor("min").nunique())
    daily["count"] = minute_count
    valid = daily["count"] >= 1368
    out = daily[valid].rename(columns={k: f"v_{k}" for k in ["max", "mean", "min", "std"]})
    out = out.rename_axis("date").reset_index()
    out["feeder"] = feeder
    return out, {"raw_rows": len(frame), "invalid_rows": int((~good).sum()),
                 "duplicate_timestamps": int(good.sum() - len(d)), "days": len(daily),
                 "accepted_days": int(valid.sum()), "excluded_days": int((~valid).sum())}


def prepare() -> None:
    path = DATA_RAW / "bilant" / "feederbw" / "feeder_measurement_data_001-040.zip"
    if not path.exists():
        raise FileNotFoundError("Descarcă sursa: uv run python -m cyberpunks.a_bilant.feederbw download")
    parts, quality = [], {}
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith(".parquet") or "/._" in name:
                continue
            feeder = int(name.rsplit("_", 1)[-1].split(".")[0])
            frame = pd.read_parquet(io.BytesIO(archive.read(name)), columns=["timestamp_UTC", "voltage_one_phase_V"])
            part, quality[str(feeder)] = aggregate(frame, feeder)
            parts.append(part)
            print(f"Feeder {feeder}: {len(part)} zile acceptate", flush=True)
    DAILY.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(parts, ignore_index=True).to_parquet(DAILY, index=False)
    with path.open("rb") as source_file:
        archive_hash = hashlib.file_digest(source_file, "sha256").hexdigest()
    manifest = {"source": SOURCE, "attribution": ATTRIBUTION, "license": "CC BY 4.0",
                "transform": "Agregare zilnică UTC a voltage_one_phase_V; interval de calitate [150,300] V; "
                             "minimum 1368 minute distincte/zi. Fără interpolare și fără etichete sintetice.",
                "archive_sha256": archive_hash,
                "quality": quality}
    DAILY.with_suffix(".json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def supervised(daily: pd.DataFrame) -> pd.DataFrame:
    parts = []
    for feeder, g in daily.groupby("feeder"):
        g = g.copy().sort_values("date").set_index("date").asfreq("D")
        g["feeder"] = feeder
        g["v_mean_7d"] = g.v_mean.rolling(7, min_periods=7).mean()
        g["v_max_7d"] = g.v_max.rolling(7, min_periods=7).mean()
        g["target"] = g.v_max.shift(-1)
        g["target_date"] = g.index + pd.Timedelta(days=1)
        g["month_sin"] = np.sin(2 * np.pi * g.target_date.dt.month / 12)
        g["month_cos"] = np.cos(2 * np.pi * g.target_date.dt.month / 12)
        g["weekday"] = g.target_date.dt.dayofweek
        parts.append(g.reset_index().dropna(subset=FEATURES + ["target"]))
    return pd.concat(parts, ignore_index=True)


def split(df: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict]:
    ids = np.random.default_rng(SEED).permutation(sorted(df.feeder.unique()))
    n = len(ids)
    train, val, test = np.split(ids, [int(n * .6), int(n * .8)])
    dates = df.target_date
    parts = {"train": df[df.feeder.isin(train) & (dates < "2024-07-01")],
             "validation": df[df.feeder.isin(val) & (dates >= "2024-07-01") & (dates < "2024-10-01")],
             "test": df[df.feeder.isin(test) & (dates >= "2024-10-01")]}
    for key, part in parts.items():
        if part.empty:
            raise ValueError(f"Partiție goală: {key}; nu se poate evalua")
    meta = {k: {"rows": len(p), "feeders": sorted(map(int, p.feeder.unique())),
                "first_target": str(p.target_date.min()), "last_target": str(p.target_date.max())}
            for k, p in parts.items()}
    return parts, meta


def run() -> dict:
    # CatBoost se importă înaintea altor biblioteci native în procesul dedicat benchmarkului.
    from catboost import CatBoostRegressor
    from lightgbm import LGBMRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBRegressor

    if not DAILY.exists():
        raise FileNotFoundError("Lipsește agregatul public FeederBW; rulează această comandă cu --prepare")
    parts, meta = split(supervised(pd.read_parquet(DAILY)))
    tr, va, te = (parts[k] for k in ("train", "validation", "test"))
    models = {"ridge": make_pipeline(StandardScaler(), Ridge(alpha=10)),
              "lightgbm": LGBMRegressor(n_estimators=300, num_leaves=15, max_depth=5, learning_rate=.03,
                                        min_child_samples=50, reg_lambda=5, n_jobs=4, random_state=SEED, verbosity=-1),
              "catboost": CatBoostRegressor(iterations=300, depth=5, learning_rate=.03, l2_leaf_reg=5,
                                            thread_count=4, random_seed=SEED, verbose=False, allow_writing_files=False),
              "xgboost": XGBRegressor(n_estimators=300, max_depth=5, learning_rate=.03, reg_lambda=5,
                                      n_jobs=4, random_state=SEED)}
    val_pred = {"persistence": va.v_max.to_numpy(), "mean_7d": va.v_max_7d.to_numpy()}
    test_pred = {"persistence": te.v_max.to_numpy(), "mean_7d": te.v_max_7d.to_numpy()}
    times = {}
    for name, model in models.items():
        with C.timer(times, name):
            model.fit(tr[FEATURES], tr.target)
            val_pred[name] = model.predict(va[FEATURES])
            test_pred[name] = model.predict(te[FEATURES])
    val_mae = {k: float(np.abs(va.target.to_numpy() - p).mean()) for k, p in val_pred.items()}
    selected = min(val_mae, key=val_mae.get)  # selecție finalizată înaintea metricilor de test
    y = te.target.to_numpy()
    pred = te[["feeder", "date", "target_date", "target"]].copy()
    metrics = {}
    for name, p in test_pred.items():
        pred[name] = p
        errors = np.abs(y - p)
        delta = errors - np.abs(y - test_pred["persistence"])
        metrics[name] = {"mae_volts": float(errors.mean()), "rmse_volts": float(np.sqrt(np.mean((y-p)**2))),
                         "p95_absolute_error_volts": float(np.quantile(errors, .95)),
                         "delta_mae_vs_persistence_by_feeder": C.ci90(lambda i, d=delta: float(d[i].mean()), te.feeder, n=1000),
                         "by_feeder_mae": {str(k): float(errors[g].mean()) for k, g in
                                           pd.Series(np.arange(len(te))).groupby(te.feeder.to_numpy())}}
    out = {"task": "Maximul temporal al tensiunii monofazate la plecare, mâine (V); sarcină separată de C",
           "labels": "REALE: măsurători FeederBW; agregare maxim zilnic, fără injecții",
           "source": SOURCE, "license": "CC BY 4.0", "features": FEATURES, "split": meta,
           "protocol": "Plecări disjuncte și timp separat; istoricul local până ieri este disponibil inclusiv "
                       "pe plecări noi. 300 arbori/model, setări fixe, zero tuning; alegere pe MAE validare.",
           "selected_on_validation": selected, "validation_mae_volts": val_mae, "test": metrics,
           "test_days_above_253V": int((y > 253).sum()), "test_rows": len(y),
           "limits": ["Nu măsoară maximul spațial în rețea și nu validează direct modelul C.",
                      "Maximul din minutele disponibile poate rata vârfuri în minutele lipsă (≤5%).",
                      "Pragul 253 V este descriptiv; nu este un diagnostic de conformitate normativă.",
                      "Intervale exploratorii pe puține plecări; fără corecție pentru comparații multiple."],
           "data_sha256": hashlib.sha256(DAILY.read_bytes()).hexdigest(), "timing_seconds": times,
           "environment": C.environment()}
    C.write_predictions("tensiune_reala_test", pred)
    C.write_json("tensiune_reala", out)
    print(f"Ales pe validare: {selected}; test MAE={metrics[selected]['mae_volts']:.3f} V", flush=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    run()


if __name__ == "__main__":
    main()
