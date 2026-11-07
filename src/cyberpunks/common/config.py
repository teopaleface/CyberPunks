"""Citirea fișierelor din config/. Configurările le deține firul planificatorului."""

from __future__ import annotations

from functools import cache
from typing import Any

import yaml

from cyberpunks.common.paths import CONFIG


@cache
def load(name: str) -> dict[str, Any]:
    """load('economics') citește config/economics.yaml."""
    with open(CONFIG / f"{name}.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
