"""Firul B: cache-ul Open-Meteo (fără rețea). Protejează cota comună și demo-ul live dacă pică internetul."""

import json
import os
import time

import pytest

from cyberpunks.b_furtuna import openmeteo


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(openmeteo, "CACHE_DIR", tmp_path)
    openmeteo.STALE_NOTES.clear()
    return tmp_path


def test_fresh_cache_does_not_call_network(cache, monkeypatch):
    params = {"latitude": "45.7", "longitude": "21.2"}
    path = openmeteo._cache_path(openmeteo.FORECAST, params)
    path.write_text(json.dumps({"daily": {"x": [1]}}), encoding="utf-8")

    def boom(*a, **k):
        raise AssertionError("nu trebuia să cheme rețeaua")

    monkeypatch.setattr(openmeteo, "_get_live", boom)
    data, cost = openmeteo.get(openmeteo.FORECAST, params)
    assert data == {"daily": {"x": [1]}} and cost == 0.0


def test_stale_forecast_is_used_when_network_fails(cache, monkeypatch):
    params = {"latitude": "45.7", "longitude": "21.2", "forecast_days": 2}
    path = openmeteo._cache_path(openmeteo.FORECAST, params)
    path.write_text(json.dumps({"daily": {"x": [2]}}), encoding="utf-8")
    old = time.time() - 5 * 3600  # mai vechi decât TTL-ul de 3 ore
    os.utime(path, (old, old))

    def fail(*a, **k):
        raise openmeteo.RateLimited("Daily API request limit exceeded")

    monkeypatch.setattr(openmeteo, "_get_live", fail)
    data, _ = openmeteo.get(openmeteo.FORECAST, params)
    assert data == {"daily": {"x": [2]}}
    assert openmeteo.STALE_NOTES and "n-a răspuns" in openmeteo.STALE_NOTES[0]


def test_no_cache_and_no_network_raises(cache, monkeypatch):
    def fail(*a, **k):
        raise openmeteo.RateLimited("limit")

    monkeypatch.setattr(openmeteo, "_get_live", fail)
    with pytest.raises(openmeteo.RateLimited):
        openmeteo.get(openmeteo.FORECAST, {"latitude": "1", "longitude": "2"})


def test_archive_is_cached_forever(cache, monkeypatch):
    params = {"start_date": "2025-07-01"}
    path = openmeteo._cache_path(openmeteo.ARCHIVE, params)
    path.write_text(json.dumps([{"ok": 1}]), encoding="utf-8")
    old = time.time() - 30 * 24 * 3600
    os.utime(path, (old, old))
    monkeypatch.setattr(openmeteo, "_get_live", lambda *a, **k: (_ for _ in ()).throw(AssertionError("rețea")))
    data, _ = openmeteo.get(openmeteo.ARCHIVE, params)
    assert data == [{"ok": 1}]
