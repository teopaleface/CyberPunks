"""Calculul vectorizat trebuie să dea aceleași tensiuni ca pandapower.runpp."""

from __future__ import annotations

import numpy as np
import pytest

from cyberpunks.c_prosumatori import grids
from cyberpunks.c_prosumatori.powerflow import validate


@pytest.mark.parametrize("topology", ["rural1", "semiurb4"])
def test_vectorized_matches_pandapower(topology: str) -> None:
    rng = np.random.default_rng(3)
    spec = grids.sample_spec(topology, rng, post_id=f"TEST-{topology}", mode="train")
    spec.prosumer_share = 0.5
    post = grids.build_post(spec)
    res = validate(post.net, post.model, n=15, seed=1)
    assert res["max_abs_diff_pu"] < 1e-6, res


def test_post_features_are_sane() -> None:
    rng = np.random.default_rng(5)
    post = grids.build_post(grids.sample_spec("rural2", rng, post_id="TEST-F", mode="population"))
    f = post.features
    assert f["kva"] > 0 and f["n_customers"] > 0
    assert 0.0 <= f["prosumer_share"] <= 1.0
    assert f["sens_pv_pu"] >= 0.0 and f["r_max_ohm"] > 0.0
    assert 0.95 < f["v0_est"] < 1.1
