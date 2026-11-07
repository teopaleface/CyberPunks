"""Serii ILUSTRATIVE pentru lucrările din contracts/fixtures/, ca interfața să-și construiască graficele
înainte să existe ieșirile reale ale modelelor A, B, C.

Nu sunt date de model și nu apar în planurile reale: API-ul le servește doar în modul "fixtures",
cu `synthetic: true` și cu "(ilustrativ)" în titlu.
"""

from __future__ import annotations

import hashlib
import math
import random
from datetime import date, datetime, time, timedelta
from typing import Any

from cyberpunks.planner.settings import TZ


def _rng(work_item_id: str) -> random.Random:
    seed = int(hashlib.sha256(work_item_id.encode()).hexdigest()[:12], 16)
    return random.Random(seed)


def _meter(item: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    d = date.fromisoformat(item["target_date"])
    label = item["prediction"]["label"]
    days = 60
    base = rng.uniform(5.5, 9.5)
    points = []
    anomaly_start = days - 9
    for i in range(days):
        t = d - timedelta(days=days - i)
        weekly = 1.0 + (0.18 if t.weekday() >= 5 else 0.0)
        normal = round(base * weekly * rng.uniform(0.85, 1.15), 2)
        point: dict[str, Any] = {"t": t.isoformat(), "expected": round(base * weekly, 2)}
        if i >= anomaly_start:
            if label == "tamper":
                point.update(value=0.0, flag="zero")
            else:
                point.update(value=None, flag="gol") if i % 3 == 0 else point.update(value=round(base * 0.31, 2), flag="plat")
        else:
            point["value"] = normal
        points.append(point)
    return {
        "title_ro": "Consum zilnic față de normal (ilustrativ)",
        "unit": "kWh",
        "points": points,
        "thresholds": {},
        "annotations": [{"t": (d - timedelta(days=days - anomaly_start)).isoformat(), "label_ro": "Începe anomalia"}],
    }


def _storm(item: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    d = date.fromisoformat(item["target_date"])
    tw = item.get("time_window") or {}
    start = datetime.fromisoformat(tw["start"]) if tw else datetime.combine(d, time(12), tzinfo=TZ)
    end = datetime.fromisoformat(tw["end"]) if tw else start + timedelta(hours=8)
    peak = 40 + 60 * item["prediction"]["score"]
    points = []
    for h in range(24):
        t = datetime.combine(d, time(h), tzinfo=TZ)
        inside = start <= t < end
        mid = start + (end - start) / 2
        dist = abs((t - mid).total_seconds()) / 3600
        p50 = 18 + (peak - 18) * math.exp(-(dist**2) / 8) if inside or dist < 4 else 18 + rng.uniform(-4, 4)
        points.append(
            {"t": t.isoformat(), "expected": round(p50, 1), "low": round(p50 * 0.72, 1), "high": round(p50 * 1.25, 1)}
        )
    return {
        "title_ro": "Rafale de vânt prognozate, P10-P90 (ilustrativ)",
        "unit": "km/h",
        "points": points,
        "thresholds": {"rafala_periculoasa_kmh": 70.0},
        "annotations": [{"t": start.isoformat(), "label_ro": "Începe fereastra de risc"}],
    }


def _voltage(item: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    d = date.fromisoformat(item["target_date"])
    vmax = item["prediction"].get("point_estimate") or 1.10
    points = []
    for q in range(6 * 4, 21 * 4):  # 06:00-21:00, la 15 minute
        t = datetime.combine(d, time(q // 4, (q % 4) * 15), tzinfo=TZ)
        hour = q / 4
        sun = max(0.0, math.cos((hour - 13.0) / 7.0 * math.pi / 2)) ** 2
        p50 = 1.02 + (vmax - 1.02) * sun + rng.uniform(-0.002, 0.002)
        points.append(
            {"t": t.isoformat(), "expected": round(p50, 4), "low": round(p50 - 0.012 * sun - 0.004, 4), "high": round(p50 + 0.01 * sun + 0.003, 4)}
        )
    return {
        "title_ro": "Tensiunea maximă prognozată la post, P10-P90 (ilustrativ)",
        "unit": "pu",
        "points": points,
        "thresholds": {"limita_tensiune_pu": 1.10},
        "annotations": [{"t": datetime.combine(d, time(13), tzinfo=TZ).isoformat(), "label_ro": "Vârful de la prânz"}],
    }


def make_series(item: dict[str, Any]) -> dict[str, Any]:
    rng = _rng(item["work_item_id"])
    body = {"A": _meter, "B": _storm, "C": _voltage}[item["source"]](item, rng)
    return {"contract_version": "1.0", "work_item_id": item["work_item_id"], "source": item["source"], "synthetic": True, **body}
