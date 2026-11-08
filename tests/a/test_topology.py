"""Teste pentru topologia SINTETICĂ a firului A: contoarele stau pe posturile din registrul comun (firul C)."""

import re

import pytest

from cyberpunks.a_contoare.topology import BBOX, SMART_METER_INTEGRATION, load_topology

ZONE_RE = re.compile(r"^(B-S[1-6]|IF-[A-Z0-9-]+)$")


@pytest.fixture(scope="module")
def topo():
    return load_topology()


def test_unique_ids(topo):
    posts, meters = topo
    assert posts["post_id"].is_unique
    assert meters["meter_id"].is_unique


def test_every_meter_is_on_a_registry_post(topo):
    posts, meters = topo
    assert set(meters["post_id"]) <= set(posts["post_id"])
    assert meters["post_id"].str.match(r"^PT-1\d{3}$").all()


@pytest.mark.parametrize("name", [0, 1])
def test_coordinates_inside_bbox(topo, name):
    df = topo[name]
    assert df["lat"].between(BBOX["lat_min"], BBOX["lat_max"]).all()
    assert df["lon"].between(BBOX["lon_min"], BBOX["lon_max"]).all()


@pytest.mark.parametrize("name", [0, 1])
def test_zone_and_county(topo, name):
    df = topo[name]
    assert df["zone_id"].map(lambda z: bool(ZONE_RE.match(z))).all()
    assert set(df["county"]) <= {"București", "Ilfov"}
    expected = df["zone_id"].map(lambda z: "București" if z.startswith("B-") else "Ilfov")
    assert (df["county"] == expected).all()


def test_meters_follow_smart_meter_integration(topo):
    posts, meters = topo
    expected = (posts["n_customers"] * SMART_METER_INTEGRATION).round().clip(lower=1)
    assert abs(len(meters) - expected.sum()) <= len(posts)
    assert (posts["n_meters"] <= posts["n_customers"]).all()


def test_meters_are_synthetic(topo):
    assert topo[1]["synthetic"].all()
