"""Firul B: zonele din România (fișierul din git, fără rețea)."""

import re

import yaml

from cyberpunks.b_furtuna.romania import ZONES_YAML, load_zones


def test_26_zones_inside_romania_with_unique_ids():
    zones = load_zones()
    assert len(zones) == 26
    ids = [z.zone_id for z in zones]
    assert len(set(ids)) == 26
    for z in zones:
        assert re.fullmatch(r"[A-Z]{1,2}-[A-Z0-9-]+", z.zone_id)
        assert 43.5 <= z.lat <= 48.5 and 20.0 <= z.lon <= 30.0
        assert z.customers > 0 and z.area_km2 > 0


def test_zone_customers_add_up_to_official_county_totals():
    cfg = yaml.safe_load(ZONES_YAML.read_text(encoding="utf-8"))
    zones = load_zones()
    for code, c in cfg["counties"].items():
        total = sum(z.customers for z in zones if z.county_code == code)
        assert abs(total - c["customers"]) <= 3, code  # doar rotunjiri
    assert sum(c["customers"] for c in cfg["counties"].values()) == 3_180_331  # total RER, 31.12.2024
