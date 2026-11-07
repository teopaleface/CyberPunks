"""Lume SINTETICĂ pentru evaluarea agentului și pentru măsurarea solverului.

Generează, pentru o zi, lucrări A, B, C valide după contract, cu adevărul cunoscut (problema e reală sau nu).
Scorurile sunt calibrate prin construcție: adevărul se trage Bernoulli(scor). Pentru testul de robustețe,
`miscalibration` > 1 face modelul supra-încrezător (adevărul ~ Bernoulli(scor ** miscalibration)).

Toate valorile de aici sunt IPOTEZE de simulare (documentate în reports/planner/README.md), nu date reale.
Costurile și prețurile vin din config/economics.yaml, ca planificatorul și simularea să folosească aceleași cifre.
"""

from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any

from cyberpunks.planner.settings import TZ, Settings

SIM_SOURCES = ["simulare sintetică (cyberpunks.planner.simulate), nu date reale"]

# Zone pentru B: centroizi aproximativi de județ/localitate în cele 3 regiuni (puncte reale pe hartă, risc simulat).
STORM_ZONES = [
    ("IF-SNAGOV", "Ilfov", 44.704, 26.172),
    ("IF-BUFTEA", "Ilfov", 44.567, 25.948),
    ("GR-GIURGIU", "Giurgiu", 43.903, 25.969),
    ("GR-BOLINTIN", "Giurgiu", 44.445, 25.757),
    ("CT-MEDGIDIA", "Constanța", 44.250, 28.273),
    ("CT-MANGALIA", "Constanța", 43.817, 28.583),
    ("TL-TULCEA", "Tulcea", 45.172, 28.791),
    ("CL-CALARASI", "Călărași", 44.200, 27.330),
    ("IL-SLOBOZIA", "Ialomița", 44.564, 27.366),
    ("TM-LUGOJ", "Timiș", 45.689, 21.903),
    ("AR-ARAD", "Arad", 46.186, 21.312),
    ("CS-RESITA", "Caraș-Severin", 45.300, 21.889),
    ("HD-DEVA", "Hunedoara", 45.883, 22.900),
    ("TM-SANNICOLAU", "Timiș", 46.072, 20.630),
]
ILFOV_LOCALITIES = [
    ("IF-CHIAJNA", 44.459, 25.975),
    ("IF-OTOPENI", 44.553, 26.070),
    ("IF-VOLUNTARI", 44.490, 26.180),
    ("IF-POPESTI", 44.380, 26.170),
    ("IF-BRAGADIRU", 44.371, 25.975),
    ("IF-PANTELIMON", 44.452, 26.205),
    ("IF-MOGOSOAIA", 44.529, 26.000),
    ("IF-CORBEANCA", 44.600, 26.050),
]


@dataclass
class SimDay:
    plan_date: date
    items: list[dict[str, Any]]
    truth: dict[str, bool]
    meta: dict[str, Any] = field(default_factory=dict)


def _tw(d: date, start_h: float, hours: float) -> dict[str, str]:
    s = datetime.combine(d, time(0), tzinfo=TZ) + timedelta(hours=start_h)
    return {"start": s.isoformat(), "end": (s + timedelta(hours=hours)).isoformat()}


def _confidence(score: float, width: float) -> str:
    if width > 0.45:
        return "low"
    return "high" if (score >= 0.8 or score <= 0.1) and width < 0.25 else "medium"


def _prediction(
    rng: random.Random, model: str, label: str, score: float, abstain: bool = False, **extra: Any
) -> dict[str, Any]:
    width = rng.uniform(0.08, 0.35) if not abstain else rng.uniform(0.4, 0.6)
    lo, hi = max(0.0, score - width * 0.6), min(1.0, score + width * 0.4)
    return {
        "model_id": model,
        "model_version": f"{model}@sim",
        "prediction_id": str(uuid.UUID(int=rng.getrandbits(128), version=4)),
        "label": label,
        "score": round(score, 4),
        "interval_low": round(lo, 4),
        "interval_high": round(hi, 4),
        "confidence": "low" if abstain else _confidence(score, hi - lo),
        "abstain": abstain,
        "abstain_reason": "istoric prea scurt (simulat)" if abstain else None,
        **extra,
    }


def _truth(rng: random.Random, score: float, miscalibration: float) -> bool:
    return rng.random() < score**miscalibration


def _score(rng: random.Random, a: float, b: float) -> float:
    return min(0.995, max(0.005, rng.betavariate(a, b)))


def gen_meters(
    rng: random.Random, d: date, s: Settings, n: int, miscal: float, created: datetime
) -> tuple[list[dict], dict[str, bool]]:
    bbox = s.area.get(
        "demo_bbox_bucuresti_ilfov", {"lat_min": 44.25, "lat_max": 44.65, "lon_min": 25.85, "lon_max": 26.40}
    )
    price = s.econ("energy", "loss_cost_lei_per_kwh")
    horizon = s.econ("meters", "detection_horizon_days")
    items, truth = [], {}
    for i in range(n):
        asset = f"MTR-S{d:%m%d}{i:04d}"
        label = "tamper" if rng.random() < 0.35 else "faulty"
        score = _score(rng, 1.3, 2.2)  # cei mai mulți candidați au scor mediu-mic, câțiva mare
        commercial = rng.random() < 0.06
        daily_kwh = rng.lognormvariate(math.log(9.0 if label == "tamper" else 6.0), 0.75) * (8.0 if commercial else 1.0)
        value = round(daily_kwh * horizon * price, 2)
        abstain = rng.random() < 0.03
        wid = f"A-{d:%Y%m%d}-{asset}"
        items.append(
            {
                "work_item_id": wid,
                "source": "A",
                "kind": "meter_inspection",
                "asset_id": asset,
                "asset_type": "meter",
                "location": {
                    "lat": round(rng.uniform(bbox["lat_min"], bbox["lat_max"]), 5),
                    "lon": round(rng.uniform(bbox["lon_min"], bbox["lon_max"]), 5),
                    "zone_id": "B-SIM",
                    "county": "București",
                    "label": f"Contor {asset} (sintetic)",
                },
                "target_date": d.isoformat(),
                "prediction": _prediction(rng, "a-sim", label, score, abstain),
                "impact": {
                    "expected_value_lei": round(score * value, 2),
                    "value_if_true_lei": value,
                    "customers_affected": 1,
                    "urgency_hours": 72,
                    "safety_flag": label == "tamper" and score > 0.85 and rng.random() < 0.3,
                    "assumptions_ref": "meters",
                },
                "effort": {
                    "duration_min": int(s.econ("meters", "service_time_min")),
                    "crew_skill": "metering",
                    "crew_size": 2,
                    "requires_planned_outage": False,
                },
                "explanation": {
                    "top_factors": [
                        {"feature": "sim", "label_ro": "factor simulat", "value": None, "contribution": 0.3}
                    ],
                    "similar_cases": [],
                    "summary_ro": "Lucrare sintetică pentru evaluarea agentului.",
                },
                "data_quality": {
                    "missing_ratio": round(rng.uniform(0, 0.15), 3),
                    "input_issues": [],
                    "synthetic": True,
                    "data_sources": SIM_SOURCES,
                },
                "recommended_action": "human_review"
                if abstain
                else ("inspect_on_site" if score > 0.6 else "remote_reading"),
                "created_at": (created - timedelta(minutes=rng.randint(0, 600))).isoformat(),
                "extra": {"smart_meter": rng.random() < 0.85},
            }
        )
        truth[wid] = _truth(rng, score, miscal)
    return items, truth


def gen_storm(
    rng: random.Random, d: date, s: Settings, storm_day: bool, miscal: float, created: datetime
) -> tuple[list[dict], dict[str, bool]]:
    cph = s.econ("storm", "cost_per_customer_hour_lei")
    speedup = s.econ("storm", "restoration_speedup_hours")
    zones = rng.sample(STORM_ZONES, rng.randint(3, 7) if storm_day else rng.randint(0, 2))
    items, truth = [], {}
    for zid, county, lat, lon in zones:
        score = _score(rng, 2.5, 2.0) if storm_day else _score(rng, 1.2, 4.0)
        p50 = int(rng.lognormvariate(math.log(700), 0.7))
        value = round(p50 * speedup * cph, 2)
        start_h = rng.choice([11, 12, 13, 14, 15, 16])
        wid = f"B-{d:%Y%m%d}-{zid}"
        items.append(
            {
                "work_item_id": wid,
                "source": "B",
                "kind": "storm_prepositioning",
                "asset_id": zid,
                "asset_type": "zone",
                "location": {
                    "lat": lat,
                    "lon": lon,
                    "zone_id": zid,
                    "county": county,
                    "label": f"Zona {zid} (risc simulat)",
                },
                "target_date": d.isoformat(),
                "time_window": _tw(d, start_h, rng.choice([4, 6, 8])),
                "prediction": _prediction(
                    rng,
                    "b-sim",
                    "outage_risk",
                    score,
                    point_estimate=float(p50),
                    point_unit="clienți fără curent",
                    point_interval=[float(int(p50 * 0.3)), float(int(p50 * 2.2))],
                ),
                "impact": {
                    "expected_value_lei": round(score * value, 2),
                    "value_if_true_lei": value,
                    "customers_affected": p50,
                    "urgency_hours": max(1.0, start_h - 8.0),
                    "safety_flag": False,
                    "assumptions_ref": "storm",
                },
                "effort": {
                    "duration_min": 480,
                    "crew_skill": "mv_grid",
                    "crew_size": 3,
                    "requires_planned_outage": False,
                },
                "explanation": {
                    "top_factors": [
                        {"feature": "sim", "label_ro": "rafale simulate", "value": None, "contribution": 0.4}
                    ],
                    "similar_cases": [],
                    "summary_ro": "Risc de furtună sintetic pentru evaluarea agentului.",
                },
                "data_quality": {
                    "missing_ratio": 0.0,
                    "input_issues": [],
                    "synthetic": True,
                    "data_sources": SIM_SOURCES,
                },
                "recommended_action": "preposition_crew",
                "created_at": created.isoformat(),
            }
        )
        truth[wid] = _truth(rng, score, miscal)
    return items, truth


def gen_voltage(
    rng: random.Random, d: date, s: Settings, sunny: bool, miscal: float, created: datetime
) -> tuple[list[dict], dict[str, bool]]:
    limit = s.econ("voltage", "overvoltage_limit_pu")
    pv_value = s.econ("voltage", "lost_pv_value_lei_per_kwh")
    n = rng.randint(4, 12) if sunny else rng.randint(0, 3)
    items, truth = [], {}
    for i in range(n):
        zid, lat, lon = rng.choice(ILFOV_LOCALITIES)
        post = f"PT-S{d:%m%d}{i:03d}"
        score = _score(rng, 2.0, 2.0)
        vmax = round(limit + rng.uniform(-0.02, 0.04), 3)
        customers = rng.randint(15, 80)
        season_kwh = rng.uniform(1500, 9000)  # energia pierdută pe un sezon dacă invertoarele se opresc la prânz
        value = round(season_kwh * pv_value, 2)
        tap = score > 0.7
        wid = f"C-{d:%Y%m%d}-{post}"
        items.append(
            {
                "work_item_id": wid,
                "source": "C",
                "kind": "voltage_mitigation",
                "asset_id": post,
                "asset_type": "transformer_post",
                "location": {
                    "lat": round(lat + rng.uniform(-0.01, 0.01), 5),
                    "lon": round(lon + rng.uniform(-0.01, 0.01), 5),
                    "zone_id": zid,
                    "county": "Ilfov",
                    "label": f"{post}, {zid} (sintetic)",
                },
                "target_date": d.isoformat(),
                "time_window": _tw(d, 11, 4),
                "prediction": _prediction(
                    rng,
                    "c-sim",
                    "overvoltage",
                    score,
                    point_estimate=vmax,
                    point_unit="pu",
                    point_interval=[round(vmax - 0.02, 3), round(vmax + 0.015, 3)],
                ),
                "impact": {
                    "expected_value_lei": round(score * value, 2),
                    "value_if_true_lei": value,
                    "customers_affected": customers,
                    "urgency_hours": 30,
                    "safety_flag": False,
                    "assumptions_ref": "voltage",
                },
                "effort": {
                    "duration_min": 120,
                    "crew_skill": "lv_grid",
                    "crew_size": 3,
                    "requires_planned_outage": tap,
                },
                "explanation": {
                    "top_factors": [
                        {
                            "feature": "sim",
                            "label_ro": "panouri multe pe post (simulat)",
                            "value": None,
                            "contribution": 0.35,
                        }
                    ],
                    "similar_cases": [],
                    "summary_ro": "Supratensiune sintetică pentru evaluarea agentului.",
                },
                "data_quality": {
                    "missing_ratio": 0.0,
                    "input_issues": [],
                    "synthetic": True,
                    "data_sources": SIM_SOURCES,
                },
                "recommended_action": "adjust_tap" if tap else "measurement_campaign",
                "created_at": created.isoformat(),
                "extra": {"planned_outage_notified": rng.random() < 0.5},
            }
        )
        truth[wid] = _truth(rng, score, miscal)
    return items, truth


def generate_day(
    day: int,
    settings: Settings,
    *,
    seed: int = 7,
    start: date = date(2026, 7, 6),
    n_meters: int = 120,
    miscalibration: float = 1.0,
    storm_prob: float = 0.4,
    sunny_prob: float = 0.7,
) -> SimDay:
    rng = random.Random(seed * 100_003 + day)
    d = start + timedelta(days=day)
    created = datetime.combine(d - timedelta(days=1), time(17, 30), tzinfo=TZ)
    storm_day = rng.random() < storm_prob
    sunny = rng.random() < sunny_prob
    a, ta = gen_meters(rng, d, settings, n_meters, miscalibration, created)
    b, tb = gen_storm(rng, d, settings, storm_day, miscalibration, created)
    c, tc = gen_voltage(rng, d, settings, sunny, miscalibration, created)
    return SimDay(
        d,
        a + b + c,
        {**ta, **tb, **tc},
        {"storm_day": storm_day, "sunny": sunny, "n": {"A": len(a), "B": len(b), "C": len(c)}},
    )
