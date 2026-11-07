"""Teste pentru topologia SINTETICĂ a firului A. Citesc CSV-urile generate, fără rețea."""

import re

import pytest

from cyberpunks.a_contoare.topology import BBOX, load_topology

ZONE_RE = re.compile(r"^(B-S[1-6]|IF-[A-Z0-9-]+)$")


@pytest.fixture(scope="module")
def topo():
    return load_topology()


def test_unique_ids(topo):
    posts, meters = topo
    assert posts["post_id"].is_unique
    assert meters["meter_id"].is_unique


def test_every_meter_has_a_post(topo):
    posts, meters = topo
    assert set(meters["post_id"]) <= set(posts["post_id"])


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


def test_sizes(topo):
    posts, meters = topo
    assert 9_000 <= len(meters) <= 11_000
    assert 300 <= len(posts) <= 500


def test_meter_counts_match(topo):
    posts, meters = topo
    counted = meters.groupby("post_id").size()
    declared = posts.set_index("post_id")["n_meters"]
    assert (declared.sort_index() == counted.reindex(declared.index).fillna(0).astype(int).sort_index()).all()


def test_meters_are_synthetic(topo):
    assert topo[1]["synthetic"].all()
