"""Registrul posturilor de transformare: unitatea comună a produsului (C, A, bilanțul pe post).

Toate posturile sunt SINTETICE: 191 pe poziții reale din OpenStreetMap (ODbL), 109 pe poziții sintetice în
Ilfov; rețeaua din spatele fiecăruia e o variantă a unei topologii SimBench. Registrul stă în git la
`data/samples/C/posts.csv`, deci merge și dintr-o clonă curată.

    from cyberpunks.c_prosumatori.posts import load_posts, build_post
    posts = load_posts()                 # un rând pe post
    post = build_post("PT-1001")         # rețeaua pandapower, consumatorii, panourile, modelul de calcul vectorizat

Coloane principale: post_id, label, lat, lon, zone_id, county, locality, area, position_source, osm_ref,
topology, simbench_code, kva, n_customers, n_houses, n_prosumers, pv_kw, battery_kwh, line_type, tap_pos,
trăsăturile statice ale modelului C și coloanele spec_* (parametrii exacți ai simulării).
"""

from __future__ import annotations

from functools import cache

import pandas as pd

from cyberpunks.c_prosumatori import grids
from cyberpunks.common.paths import DATA_PROCESSED, DATA_SAMPLES

POSTS_CSV = DATA_SAMPLES / "C" / "posts.csv"
REGISTRY_PARQUET = DATA_PROCESSED / "C" / "population" / "registry.parquet"


@cache
def _load() -> pd.DataFrame:
    df = pd.read_parquet(REGISTRY_PARQUET) if REGISTRY_PARQUET.exists() else pd.read_csv(POSTS_CSV)
    if "simbench_code" not in df:
        df["simbench_code"] = df["topology"].map(grids.TOPOLOGIES)
    df["synthetic"] = True
    return df


def load_posts() -> pd.DataFrame:
    """Registrul posturilor (copie). Un rând pe post, index simplu."""
    return _load().copy()


def post_spec(post_id: str) -> grids.PostSpec:
    row = _load().set_index("post_id").loc[post_id]
    return grids.spec_from_row(row)


def build_post(post_id: str) -> grids.Post:
    """Rețeaua exactă a postului (aceeași ca în simularea C)."""
    return grids.build_post(post_spec(post_id))
