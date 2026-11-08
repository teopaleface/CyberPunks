"""Pachetul livrat trebuie să poată fi folosit fără modelele locale vechi."""

import hashlib
import json

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import dataset, diagnose, features, normal, predict


def test_release_loads_complete_matched_models_without_legacy_files(tmp_path, monkeypatch):
    manifest = json.loads((normal.RELEASE_DIR / "release.json").read_text())
    for name, digest in manifest["model_sha256"].items():
        assert hashlib.sha256((normal.RELEASE_DIR / name).read_bytes()).hexdigest() == digest

    monkeypatch.setattr(diagnose, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(normal, "MODEL_DIR", tmp_path)
    models = normal.load_for_prediction()
    x = pd.DataFrame([{feature: 0.0 for feature in features.NORMAL_FEATURES}])
    for model in models.values():
        q = model.predict(x).iloc[0]
        assert np.isfinite(q).all() and q.p10 <= q.p50 <= q.p90
    diag = diagnose.load_best()
    win = pd.DataFrame([{feature: 0.0 for feature in diag.features}])
    prob = diag.proba(win).to_numpy()
    assert prob.shape == (1, 6) and np.isfinite(prob).all()
    assert np.allclose(prob.sum(axis=1), 1)

    # O clonă cu lotul de test deja disponibil nu reantrenează modelele vechi.
    sample = tmp_path / "bilant" / "pop" / "daily.parquet"
    sample.parent.mkdir(parents=True)
    sample.touch()
    monkeypatch.setattr(predict, "DATA_PROCESSED", tmp_path)
    monkeypatch.setattr(dataset, "build", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("reantrenare")))
    predict.ensure_ready("pop")
