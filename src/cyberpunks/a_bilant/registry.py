"""Registrul posturilor de transformare: cel comun, al firului C (`cyberpunks.c_prosumatori.posts`).

Bilanțul, A și C folosesc aceleași `post_id` (PT-1001…), ca harta să arate un singur set de posturi. Rețeaua din
spatele fiecărui post se reconstruiește exact ca la C, din specificația lui. Posturile sunt SINTETICE.
"""

from __future__ import annotations

import pandas as pd

from cyberpunks.c_prosumatori import grids, posts


def load_posts() -> pd.DataFrame:
    """Registrul complet (post_id, lat, lon, zone_id, kva, topologia SimBench, trăsăturile din GIS)."""
    return posts.load_posts()


def spec_for(post_id: str) -> grids.PostSpec:
    """Specificația rețelei unui post (aceeași rețea ca în firul C)."""
    return posts.post_spec(post_id)
