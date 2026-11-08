"""Experiment bilanț: forma importului FeederBW REALĂ, rețele și etichete SINTETICE.

    uv run python -m cyberpunks.a_bilant.feederbw download
    uv run python -m cyberpunks.a_bilant.feederbw prepare --workers 4
    uv run python -m cyberpunks.a_bilant.feederbw tune --trials 40 --workers 4

FeederBW, Netze BW / KIT, CC BY 4.0, doi:10.5281/zenodo.17831177.
Treutlein et al., Scientific Data 13, 1283 (2026), doi:10.1038/s41597-026-08152-9.
Nu conține perechi complete contor-post / contoare-clienți sau verdicte reale.
Folosim primul lot public (40 de plecări); exportul se taie la zero, media orară
se normalizează, apoi se scalează la clienții sintetici. PV și vremea rămân cele
ale simulatorului românesc. Nu este validare pe pierderi măsurate sau pe PPC.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

import httpx
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score

from cyberpunks.a_bilant import dataset as D
from cyberpunks.a_bilant import diagnose as G
from cyberpunks.a_bilant import features as F
from cyberpunks.a_bilant import normal as N
from cyberpunks.a_bilant import windows as W
from cyberpunks.a_bilant import world
from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.a_bilant.v2 import full_decision
from cyberpunks.common.paths import DATA_PROCESSED, DATA_RAW, DATA_SAMPLES, MODELS, REPORTS

RECORD = "https://zenodo.org/api/records/17831177"
ARCHIVE = "feeder_measurement_data_001-040.zip"
RAW = DATA_RAW / "bilant" / "feederbw"
POOL = "feederbw_import_v1"
OUT = DATA_PROCESSED / "bilant" / POOL
REPORT = REPORTS / "bilant" / "feederbw_optuna.json"
MANIFEST = DATA_SAMPLES / "bilant" / "feederbw_manifest.json"
PERIOD = ("2024-04-02", "2025-03-30")  # complet în arhiva FeederBW, inclusiv marginile UTC
SEED = 20261108


def download() -> None:
    """Descarcă lotul oficial în 4 segmente reluabile, verifică MD5 de la editor."""
    RAW.mkdir(parents=True, exist_ok=True)
    r = httpx.get(RECORD, timeout=60)
    r.raise_for_status()
    record = r.json()
    (RAW / "record.json").write_text(json.dumps(record, indent=2))
    entry = next(f for f in record["files"] if f["key"] == ARCHIVE)
    target = RAW / ARCHIVE
    if not target.exists():
        size = entry["size"]
        span = (size + 3) // 4

        def part(k: int) -> None:
            start, stop = k * span, min((k + 1) * span, size) - 1
            dest = RAW / f"{ARCHIVE}.part{k}"
            done = dest.stat().st_size if dest.exists() else 0
            if done == stop - start + 1:
                return
            if done > stop - start + 1:
                raise ValueError(f"Segment prea mare: {dest}")
            with httpx.stream("GET", entry["links"]["self"], headers={"Range": f"bytes={start + done}-{stop}"},
                              follow_redirects=True, timeout=180) as response:
                response.raise_for_status()
                if response.status_code != 206 or response.headers.get("content-range", "").split("/")[0] != f"bytes {start + done}-{stop}":
                    raise ValueError("Serverul nu a respectat intervalul cerut")
                with dest.open("ab") as f:
                    for block in response.iter_bytes(1024 * 1024):
                        f.write(block)
            if dest.stat().st_size != stop - start + 1:
                raise ValueError(f"Segment incomplet: {dest}")
            print(f"descărcare segment {k + 1}/4 gata", flush=True)

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(part, range(4)))
        import shutil

        tmp = RAW / f"{ARCHIVE}.assembling"
        with tmp.open("wb") as f:
            for k in range(4):
                with (RAW / f"{ARCHIVE}.part{k}").open("rb") as src:
                    shutil.copyfileobj(src, f)
        with tmp.open("rb") as f:
            digest = "md5:" + hashlib.file_digest(f, "md5").hexdigest()
        if digest != entry["checksum"] or tmp.stat().st_size != size:
            raise ValueError("Arhiva nu corespunde sumei editorului")
        tmp.replace(target)
        for k in range(4):
            (RAW / f"{ARCHIVE}.part{k}").unlink()
    with target.open("rb") as f:
        if "md5:" + hashlib.file_digest(f, "md5").hexdigest() != entry["checksum"]:
            raise ValueError("Arhiva locală nu corespunde sumei editorului")
    print(f"arhivă verificată: {target}", flush=True)


def hourly_import(frame: pd.DataFrame, index: pd.DatetimeIndex) -> tuple[np.ndarray, dict]:
    """Timestamp FeederBW = începutul minutului UTC; simulatorul = sfârșitul orei.

    O oră cere minimum 45 de minute valide. Golurile orare se completează numai
    din trecut (aceeași oră de acum 7 zile, apoi ultima valoare). Fără backfill.
    """
    ts = pd.to_datetime(frame["timestamp_UTC"], utc=True)
    power = pd.Series(frame["active_power_kW"].to_numpy(dtype=float), index=ts).sort_index()
    duplicates = int(power.index.duplicated().sum())
    power = power.groupby(level=0).mean().replace([np.inf, -np.inf], np.nan)
    hours = power.resample("h").agg(["mean", "count"])
    values = hours["mean"].where(hours["count"] >= 45)
    target_index = index - pd.Timedelta(hours=1)
    missing = int(values.reindex(target_index).isna().sum())
    if missing / len(index) > 0.10:
        raise ValueError(f"Prea multe ore lipsă: {missing}/{len(index)}")
    # Păstrăm și istoricul anterior perioadei pentru completarea cauzală.
    values = values.reindex(pd.date_range(min(values.index.min(), target_index.min()), target_index.max(), freq="h"))
    for _ in range(54):
        if not values.isna().any():
            break
        values = values.fillna(values.shift(168))
    values = values.ffill().reindex(target_index)
    if values.isna().any():
        raise ValueError("Prima oră nu are istoric: nu completăm din viitor")
    info = {"missing_hours": missing, "hours": len(values), "duplicate_minutes": duplicates,
            "export_hours_clipped": int((values < 0).sum()), "min_hourly_kw": float(values.min()),
            "max_hourly_kw": float(values.max())}
    values = values.clip(lower=0).to_numpy()
    if values.mean() <= 0:
        raise ValueError("Profil fără import pozitiv")
    return values, info


def source_assignment(meta: pd.DataFrame, feeders: list[int]) -> dict[str, int]:
    # Vecinii rămân împreună, inclusiv perechile client-post greșit; aceeași
    # plecare reală poate avea mai multe rețele sintetice, toate în același split.
    clusters = sorted(meta["cluster"].unique())
    mapping = {c: feeders[i % len(feeders)] for i, c in enumerate(clusters)}
    return meta.set_index("post_id")["cluster"].map(mapping).to_dict()


def feeder_split(feeders: list[int]) -> dict[str, list[int]]:
    ids = np.random.default_rng(SEED).permutation(sorted(feeders))
    n = len(ids)
    return {"train": sorted(int(x) for x in ids[:int(n * 0.6)]),
            "validation": sorted(int(x) for x in ids[int(n * 0.6):int(n * 0.8)]),
            "test": sorted(int(x) for x in ids[int(n * 0.8):])}


def prepare(workers: int) -> None:
    if not (RAW / ARCHIVE).exists():
        raise FileNotFoundError("Rulează întâi feederbw download")
    wx = world.load_weather(PERIOD)
    profiles, quality, excluded = {}, {}, {}
    with zipfile.ZipFile(RAW / ARCHIVE) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith(".parquet"):
                continue
            feeder = int(name.rsplit("_", 1)[-1].split(".")[0])
            frame = pd.read_parquet(io.BytesIO(archive.read(name)), columns=["timestamp_UTC", "active_power_kW"])
            try:
                profiles[feeder], quality[str(feeder)] = hourly_import(frame, wx.index)
            except ValueError as exc:
                excluded[str(feeder)] = str(exc)
                print(f"profil {feeder} exclus: {exc}", flush=True)
                continue
            print(f"profil real {feeder}/40", flush=True)
    if len(profiles) < 30:
        raise ValueError(f"Doar {len(profiles)} profile valide; prea puține pentru experiment")
    _, meta = D.train_specs()
    mapping = source_assignment(meta, sorted(profiles))
    split = feeder_split(sorted(profiles))
    D.build("train", workers, output_pool=POOL, weather_data=wx,
            load_shapes={post: profiles[f] for post, f in mapping.items()})
    provenance = {"source": "FeederBW, Netze BW / KIT", "record": "https://zenodo.org/records/17831177",
                  "paper": "https://doi.org/10.1038/s41597-026-08152-9", "license": "CC BY 4.0",
                  "archive": ARCHIVE, "archive_sha256": "", "period": PERIOD, "seed": SEED,
                  "simulation_seed": D.SEEDS["train"],
                  "real": "forma importului orar: max(media puterii nete măsurate, 0), normalizată",
                  "synthetic": "rețele, scară kWh, clienți, PV, pierderi, măsurători simulate și toate etichetele",
                  "weather": "Open-Meteo București, nu vremea plecărilor germane",
                  "split_feeders": split, "post_source_feeder": mapping, "quality": quality,
                  "excluded_feeders": excluded}
    with (RAW / ARCHIVE).open("rb") as f:
        provenance["archive_sha256"] = hashlib.file_digest(f, "sha256").hexdigest()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    (OUT / "provenance.json").write_text(MANIFEST.read_text())
    print("lot cu profile reale și etichete SINTETICE gata", flush=True)


def macro(y: np.ndarray, pred: np.ndarray) -> float:
    return float(f1_score(y, pred, labels=list(CLASSES), average="macro", zero_division=0))


def scores(y: np.ndarray, pred: np.ndarray) -> dict:
    per_class = f1_score(y, pred, labels=list(CLASSES), average=None, zero_division=0)
    return {"macro_f1": macro(y, pred), "accuracy": float(np.mean(y == pred)),
            "f1_by_class": dict(zip(CLASSES, map(float, per_class), strict=True)),
            "confusion_matrix": confusion_matrix(y, pred, labels=list(CLASSES)).tolist()}


def bootstrap(y: np.ndarray, before: np.ndarray, after: np.ndarray, groups: np.ndarray) -> list[float]:
    # Unitatea independentă este plecarea REALĂ, nu ferestrele suprapuse.
    ids = np.unique(groups)
    indices = {g: np.flatnonzero(groups == g) for g in ids}
    rng = np.random.default_rng(SEED)
    deltas = []
    for _ in range(1000):
        idx = np.concatenate([indices[g] for g in rng.choice(ids, len(ids), replace=True)])
        deltas.append(macro(y[idx], after[idx]) - macro(y[idx], before[idx]))
    return [float(x) for x in np.quantile(deltas, [0.05, 0.95])]


def tune(trials: int, workers: int) -> None:
    t0 = time.perf_counter()
    manifest = json.loads(MANIFEST.read_text())
    mapping = manifest["post_source_feeder"]
    split = manifest["split_feeders"]
    data = F.load_pool(POOL)
    source = data["post_id"].map(mapping)
    train_mask = source.isin(split["train"])
    clean = data["clean"] & (data["hist_days"] > 0)
    normal_models = N.fit_pair(data[train_mask & clean], SEED)
    pred = W.predict_normal(normal_models, data)
    # OOF parcurge plecările reale, nu posturile sintetice individuale.
    for k in range(3):
        fold = set(split["train"][k::3])
        held = source.isin(fold)
        fit_rows = train_mask & ~held & clean
        fold_models = N.fit_pair(data[fit_rows], SEED)
        pred.loc[held] = W.predict_normal(fold_models, data[held]).to_numpy()
        print(f"normal OOF {k + 1}/3 gata", flush=True)
    win = W.build_windows_parallel(data, pred, POOL, workers=workers)
    win["source_feeder"] = win["post_id"].map(mapping)
    win.to_parquet(OUT / "windows.parquet")
    tr = win[win["source_feeder"].isin(split["train"])]
    va = win[win["source_feeder"].isin(split["validation"])]
    te = win[win["source_feeder"].isin(split["test"])]
    for a, b in ((tr, va), (tr, te), (va, te)):
        assert set(a["source_feeder"]).isdisjoint(b["source_feeder"])
        assert set(a["post_id"]).isdisjoint(b["post_id"])
    # Diagnosticul livrat v2, reantrenat pe aceleași rânduri și trăsături.
    current = json.loads((REPORTS / "bilant" / "v2_params.json").read_text())["params"]
    baseline = G.fit(tr, seed=SEED, features=W.WIN_FEATURES_V2, params=current, n_jobs=workers)
    baseline_val = macro(va["true_class"].to_numpy(), full_decision(baseline, va)["label"].to_numpy())
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED))

    def objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 200, 900, step=100),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 127, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 200, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.0, 10.0),
            "class_weight_power": trial.suggest_float("class_weight_power", 0.0, 1.0),
        }
        model = G.fit(tr, seed=SEED, features=W.WIN_FEATURES_V2, params=params, n_jobs=workers)
        value = macro(va["true_class"].to_numpy(), full_decision(model, va)["label"].to_numpy())
        print(f"Optuna {trial.number + 1}/{trials}: F1 validare {value:.4f}", flush=True)
        return value

    study.enqueue_trial(current)
    study.enqueue_trial(G.DEFAULT_PARAMS)
    study.optimize(objective, n_trials=trials)
    study.trials_dataframe().to_csv(OUT / "trials.csv", index=False)
    # Alegerea este închisă pe validare înainte să citim etichetele testului.
    best = G.fit(tr, seed=SEED, features=W.WIN_FEATURES_V2, params=study.best_params, n_jobs=workers)
    y = te["true_class"].to_numpy()
    before = full_decision(baseline, te)["label"].to_numpy()
    after = full_decision(best, te)["label"].to_numpy()
    # G.save permite și un nume cu subdirector, fără a înlocui diagnose_v2.
    (MODELS / "bilant" / "experiments").mkdir(parents=True, exist_ok=True)
    best.save("experiments/feederbw_optuna", params=study.best_params)
    for name, model in normal_models.items():
        model.save(f"experiments/feederbw_normal_{name}")
    predictions = te[["post_id", "source_feeder", "day", "true_class"]].copy()
    predictions["baseline"], predictions["optuna"] = before, after
    predictions.to_parquet(OUT / "test_predictions.parquet")
    ci = bootstrap(y, before, after, te["source_feeder"].to_numpy())
    result = {
        "source": manifest["record"], "license": manifest["license"], "period": PERIOD,
        "real": manifest["real"], "synthetic": manifest["synthetic"],
        "split_feeders": split, "excluded_feeders": manifest["excluded_feeders"],
        "posts": {k: int(v["post_id"].nunique()) for k, v in (("train", tr), ("validation", va), ("test", te))},
        "windows": {k: len(v) for k, v in (("train", tr), ("validation", va), ("test", te))},
        "class_counts": {k: {c: int((v["true_class"] == c).sum()) for c in CLASSES}
                         for k, v in (("train", tr), ("validation", va), ("test", te))},
        "features": W.WIN_FEATURES_V2, "classes": list(CLASSES), "trials": len(study.trials), "seed": SEED,
        "objective": "macro-F1 pe validare, inclusiv regula perechii și a contorului martor; aceleași reguli la test",
        "baseline_params": current, "best_params": study.best_params,
        "validation": {"baseline_macro_f1": baseline_val, "optuna_macro_f1": study.best_value},
        "test": {"baseline": scores(y, before), "optuna": scores(y, after),
                 "delta_macro_f1": macro(y, after) - macro(y, before), "delta_macro_f1_bootstrap90_by_real_feeder": ci},
        "confirmed_gain": bool(ci[0] > 0), "release_changed": False,
        "normal_model": "parametrii existenți, antrenat numai pe plecările train; OOF 3 grupe de plecări pentru diagnosticul train",
        "limitations": ["Toate etichetele sunt SINTETICE, inclusiv furtul și pierderea normală.",
                        f"Primul lot oficial: {sum(map(len, split.values()))}/40 plecări valide din 200; test pe {len(split['test'])} plecări reale; putere statistică mică.",
                        "Se păstrează forma importului, nu scara, exportul sau măsurătorile pereche post-clienți.",
                        "Vreme București și PV simulate, fără sincronizare cu vremea germană.",
                        "Test spațial pe plecări nevăzute, în aceeași perioadă; nu este test în viitor."],
        "seconds": round(time.perf_counter() - t0, 1),
    }
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["download", "prepare", "tune"])
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.trials < 2 or not 1 <= args.workers <= D.MAX_WORKERS:
        ap.error("minimum 2 încercări; workers între 1 și 8")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[key] = "1"
    if args.command == "download":
        download()
    elif args.command == "prepare":
        prepare(args.workers)
    else:
        tune(args.trials, args.workers)


if __name__ == "__main__":
    main()
