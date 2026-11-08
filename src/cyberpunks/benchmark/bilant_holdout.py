"""Audit nou pe 300 posturi SINTETICE; protocol și artefacte fixate înaintea generării.

    uv run --group bench python -m cyberpunks.benchmark.bilant_holdout --freeze
    uv run --group bench python -m cyberpunks.benchmark.bilant_holdout

Nu antrenează, nu schimbă praguri și nu promovează modele pe baza acestui test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from cyberpunks.benchmark import common as C
from cyberpunks.common.paths import DATA_PROCESSED, MODELS, ROOT

PROTOCOL = C.OUT / "bilant_holdout_protocol.json"


def frozen_inputs() -> dict:
    paths = [p for p in (MODELS / "release" / "bilant-v2").rglob("*") if p.is_file()]
    paths += list((ROOT / "src/cyberpunks/a_bilant").glob("*.py"))
    paths += list((ROOT / "src/cyberpunks/c_prosumatori").glob("*.py"))
    paths.append(ROOT / "src/cyberpunks/benchmark/bilant_holdout.py")
    paths.append(ROOT / "src/cyberpunks/benchmark/common.py")
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def freeze() -> None:
    from cyberpunks.a_bilant.dataset import SEEDS
    if PROTOCOL.exists():
        raise FileExistsError("Protocolul este deja fixat; nu se suprascrie după vizualizarea testului")
    if (DATA_PROCESSED / "bilant/holdout").exists():
        raise FileExistsError("Lotul există înainte de protocol: nu îl putem numi test nou")
    C.write_json("bilant_holdout_protocol", {
        "created_at": datetime.now(ZoneInfo("Europe/Bucharest")).isoformat(), "seed": SEEDS["holdout"],
        "posts": 300, "topologies": 6, "primary_metric": "macro_f1", "bootstrap_unit": "cartier",
        "model": "models/release/bilant-v2", "baseline": "tabelul de reguli existent, diagnose.rules",
        "selection": "Nicio selecție, antrenare sau ajustare de prag pe acest test; publicăm și un rezultat mai slab.",
        "labels": "SINTETICE, același simulator; posturi/seed noi, nu topologii fizice noi și nu teren real",
        "frozen_inputs": frozen_inputs()})


def run() -> None:
    from cyberpunks.a_bilant import dataset as D
    from cyberpunks.a_bilant import diagnose as G
    from cyberpunks.a_bilant import features as F
    from cyberpunks.a_bilant import normal as N
    from cyberpunks.a_bilant import windows as W
    from cyberpunks.a_bilant.v2 import f1s, full_decision

    if not PROTOCOL.exists():
        raise FileNotFoundError("Fixează întâi protocolul cu --freeze")
    protocol = json.loads(PROTOCOL.read_text())
    if protocol["frozen_inputs"] != frozen_inputs():
        raise ValueError("Codul sau modelul s-a schimbat după fixarea protocolului; auditul nu poate continua")
    pool = DATA_PROCESSED / "bilant/holdout"
    if not (pool / "meta.json").exists():
        D.build("holdout", workers=4)
    cache = pool / "windows.parquet"
    if cache.exists():
        win = pd.read_parquet(cache)
    else:
        d = F.load_pool("holdout")
        normal = {"warm": N.load("normal", N.PREVIOUS_RELEASE_DIR),
                  "cold": N.load("normal_cold", N.PREVIOUS_RELEASE_DIR)}
        win = W.build_windows(d, W.predict_normal(normal, d), "holdout")
        win.to_parquet(cache, index=False)
    model = G.load_packaged(N.PREVIOUS_RELEASE_DIR)
    pred = full_decision(model, win)
    rule = G.rules(win).to_numpy()
    y, yp = win.true_class.to_numpy(), pred.label.to_numpy()
    meta = pd.read_parquet(pool / "posts.parquet")
    groups = win.post_id.map(meta.set_index("post_id").cluster).to_numpy()
    result = {"protocol": protocol, "rows": len(win), "posts": int(win.post_id.nunique()),
              "class_counts": win.true_class.value_counts().to_dict(), "model": f1s(y, yp), "baseline": f1s(y, rule),
              "delta_macro_f1": C.ci90(lambda i: f1s(y[i], yp[i])["macro_f1"] - f1s(y[i], rule[i])["macro_f1"],
                                       groups, n=1000),
              "abstain_share": float(pred.abstain.mean()),
              "confident_accuracy": float(np.mean(yp[~pred.abstain] == y[~pred.abstain])),
              "windows_sha256": hashlib.sha256(cache.read_bytes()).hexdigest(),
              "environment": C.environment(), "release_changed": frozen_inputs() != protocol["frozen_inputs"]}
    output = win[["post_id", "day", "true_class"]].copy()
    output["cluster"], output["lightgbm_label"], output["rules_label"] = groups, yp, rule
    output["abstain"] = pred.abstain.to_numpy()
    C.write_predictions("bilant_holdout_test", output)
    C.write_json("bilant_holdout", result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    freeze() if args.freeze else run()


if __name__ == "__main__":
    main()
