"""Firul B: robustețea cap-coadă, prin `predict.run()`, cu răspunsuri Open-Meteo SINTETICE (construite în test).

Cele patru cazuri cerute: vreme lipsă, valori imposibile, zonă fără istoric, prognoză cu interval prea larg.
Folosește modelul livrat (`models/release/b_model.joblib`); fără rețea.
"""

from datetime import datetime, timedelta

import pytest

from cyberpunks.b_furtuna import openmeteo, predict, romania
from cyberpunks.common.contracts import WorkItem

ZONES = romania.load_zones()
IDX = {z.zone_id: i for i, z in enumerate(ZONES)}


def _target():
    return datetime.now(predict.TZ).date() + timedelta(days=1)


def _day_values(gust=20.0, precip=0.0):
    return {"weather_code": 3, "temperature_2m_max": 12.0, "temperature_2m_min": 4.0, "precipitation_sum": precip,
            "rain_sum": precip, "snowfall_sum": 0.0, "precipitation_hours": 2.0 if precip else 0.0,
            "wind_speed_10m_max": gust / 2, "wind_gusts_10m_max": gust, "shortwave_radiation_sum": 8.0}


def _payload(target, today_override: dict | None = None, missing: bool = False):
    """Un răspuns SINTETIC de prognoză pentru o zonă: 9 zile liniștite înainte, ziua țintă (eventual altfel), ziua după."""
    days = [target - timedelta(days=k) for k in range(8, -2, -1)]
    daily = {"time": [d.isoformat() for d in days]}
    for var in openmeteo.DAILY_VARS:
        vals = []
        for d in days:
            v = _day_values()
            if d == target and today_override:
                v = {**v, **today_override}
            vals.append(None if (missing and d == target) else v[var])
        daily[var] = vals
    hours = [datetime.combine(target, datetime.min.time()) + timedelta(hours=h) for h in range(-24, 48)]
    g_today = (today_override or {}).get("wind_gusts_10m_max", 20.0)
    hourly = {"time": [h.strftime("%Y-%m-%dT%H:%M") for h in hours]}
    hourly["wind_gusts_10m"] = [g_today if (h.date() == target and 15 <= h.hour <= 18) else 15.0 for h in hours]
    hourly["wind_speed_10m"] = [8.0 for _ in hours]
    hourly["precipitation"] = [0.0 for _ in hours]
    hourly["temperature_2m"] = [10.0 for _ in hours]
    hourly["weather_code"] = [3 for _ in hours]
    return {"daily": daily, "hourly": hourly, "timezone": "Europe/Bucharest"}


def _ensemble(target, wide_zone: str | None = None):
    """Ensemble SINTETIC cu 20 de membri: liniștit peste tot; pentru `wide_zone`, jumătate liniștiți, jumătate violenți."""
    hours = [datetime.combine(target, datetime.min.time()) + timedelta(hours=h) for h in range(48)]
    out = []
    for z in ZONES:
        hourly = {"time": [h.strftime("%Y-%m-%dT%H:%M") for h in hours]}
        for m in range(1, 21):
            violent = z.zone_id == wide_zone and m > 10
            hourly[f"wind_gusts_10m_member{m:02d}"] = [110.0 if violent and 15 <= h.hour <= 18 else 20.0 for h in hours]
            hourly[f"precipitation_member{m:02d}"] = [10.0 if violent and 15 <= h.hour <= 18 else 0.0 for h in hours]
        out.append({"hourly": hourly})
    return out


@pytest.fixture
def fake_run(tmp_path, monkeypatch):
    """Rulează `predict.run('maine')` cu răspunsuri sintetice; întoarce lucrările, după zonă."""

    def _run(overrides: dict[str, dict] | None = None, missing: set[str] | None = None, wide_zone: str | None = None):
        target = _target()
        overrides, missing = overrides or {}, missing or set()

        def fake_get(url, params, **kw):
            if url == openmeteo.ENSEMBLE:
                return _ensemble(target, wide_zone), 0.0
            return [_payload(target, overrides.get(z.zone_id), z.zone_id in missing) for z in ZONES], 0.0

        monkeypatch.setattr(openmeteo, "get", fake_get)
        monkeypatch.setattr(predict, "OUTPUTS", tmp_path)
        monkeypatch.setattr(predict, "work_items_path", lambda s, src: tmp_path / "work_items" / s / f"{src}.jsonl")
        out = predict.run("maine", None)
        items = [WorkItem.model_validate_json(x) for x in out.read_text(encoding="utf-8").splitlines()]
        assert len(items) == len(ZONES)
        return {it.asset_id: it for it in items}

    return _run


def test_missing_weather_for_one_zone_goes_to_a_human(fake_run):
    items = fake_run(missing={"TM-LUGOJ"})
    it = items["TM-LUGOJ"]
    assert it.recommended_action == "human_review"
    assert "lipsesc rafala sau ploaia" in it.prediction.abstain_reason
    assert any("vreme lipsă" in s for s in it.data_quality.input_issues)
    assert items["TM-TIMISOARA"].prediction.abstain is False  # celelalte zone nu sunt afectate


def test_impossible_values_are_cleaned_and_flagged(fake_run):
    items = fake_run(overrides={"CS-RESITA": {"wind_gusts_10m_max": 900.0, "precipitation_sum": -5.0}})
    it = items["CS-RESITA"]
    assert any("valori imposibile" in s for s in it.data_quality.input_issues)
    assert it.recommended_action == "human_review"  # rafala imposibilă devine lipsă, deci decide omul
    assert it.extra["gust_max_kmh"] is None


def test_zone_without_history_in_a_storm_goes_to_a_human(fake_run):
    storm = {"wind_gusts_10m_max": 80.0, "precipitation_sum": 30.0, "rain_sum": 30.0}
    items = fake_run(overrides={"B-BUCURESTI": storm})
    it = items["B-BUCURESTI"]
    assert it.recommended_action == "human_review"
    assert "mai mare sau mai densă" in it.prediction.abstain_reason


def test_zone_without_history_on_a_calm_day_stays_quiet(fake_run):
    it = fake_run()["B-BUCURESTI"]
    assert it.prediction.abstain is False
    assert it.recommended_action == "no_action"
    assert "Vreme liniștită" in it.explanation.summary_ro


def test_too_wide_forecast_interval_goes_to_a_human(fake_run):
    moderate = {"wind_gusts_10m_max": 45.0, "precipitation_sum": 5.0, "rain_sum": 5.0}
    items = fake_run(overrides={"AR-ARAD": moderate}, wide_zone="AR-ARAD")
    it = items["AR-ARAD"]
    assert it.prediction.interval_high - it.prediction.interval_low >= predict.DISAGREE_WIDTH
    assert it.recommended_action == "human_review"
    assert "nu se pun de acord" in it.prediction.abstain_reason
