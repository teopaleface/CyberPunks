"""Testele C rulează fără rețea: vremea vine din mostra din git (`data/samples/C/weather_2025_utc.parquet`, 2025),
iar orice descărcare (arhivă sau prognoză) e blocată. Așa `make check` merge și dintr-o clonă curată, offline."""

from __future__ import annotations

import pytest

from cyberpunks.c_prosumatori import weather


def _no_network(*args, **kwargs):
    raise ConnectionError("testele C rulează fără rețea (vezi tests/c/conftest.py)")


@pytest.fixture(scope="session", autouse=True)
def offline_weather():
    mp = pytest.MonkeyPatch()
    mp.setattr(weather, "archive", lambda *args, **kwargs: weather.archive_sample())
    mp.setattr(weather, "download_archive", _no_network)
    mp.setattr(weather, "download_forecast", _no_network)
    yield
    mp.undo()
