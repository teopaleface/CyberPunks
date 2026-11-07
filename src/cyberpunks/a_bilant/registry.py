"""Registrul posturilor de transformare: cel comun, al firului C.

Folosește `cyberpunks.c_prosumatori.posts.load_posts()` când există în `Teo`. Până atunci citește copia registrului
publicat de C (`data/samples/bilant/posts_C_registry_copy.csv`, luată din `data/samples/C/posts_population_full.csv`
de pe branch-ul lui C), ca bilanțul, A și C să se întâlnească la aceleași `post_id`. Posturile sunt SINTETICE.
"""

from __future__ import annotations

from functools import cache

import pandas as pd

from cyberpunks.c_prosumatori import grids
from cyberpunks.common.paths import DATA_SAMPLES

COPY = DATA_SAMPLES / "bilant" / "posts_C_registry_copy.csv"
C_FULL = DATA_SAMPLES / "C" / "posts_population_full.csv"
SPEC_FIELDS = [f for f in grids.PostSpec.__dataclass_fields__]


@cache
def load_posts() -> pd.DataFrame:
    """Registrul complet (post_id, lat, lon, zone_id, kva, topologia SimBench și parametrii rețelei)."""
    try:  # registrul oficial al lui C, când ajunge în Teo
        from cyberpunks.c_prosumatori.posts import load_posts as c_load  # type: ignore[import-not-found]

        reg = c_load()
        if set(SPEC_FIELDS) - {"post_id", "mode"} <= set(reg.columns):
            return reg.reset_index(drop=True)
    except Exception:  # noqa: BLE001, S110 - modulul lui C poate lipsi sau poate avea alt format
        pass
    path = C_FULL if C_FULL.exists() else COPY
    reg = pd.read_csv(path)
    reg = reg.loc[:, ~reg.columns.duplicated()]
    return reg.reset_index(drop=True)


def spec_from_row(row: pd.Series) -> grids.PostSpec:
    """Specificația rețelei unui post din registru (aceeași rețea ca în firul C, din seed)."""
    vals = {}
    for f in SPEC_FIELDS:
        if f == "mode":
            vals[f] = str(row.get("mode", "population"))
        elif f in ("post_id", "topology", "line_type"):
            vals[f] = str(row[f])
        elif f in ("seed", "kva", "tap_pos"):
            vals[f] = round(float(row[f]))
        else:
            vals[f] = float(row[f])
    return grids.PostSpec(**vals)
