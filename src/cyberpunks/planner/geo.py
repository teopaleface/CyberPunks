"""Distanțe și timpi de deplasare: distanța în linie dreaptă (haversine) × factorul de drum, la viteza medie din config."""

from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


@dataclass(frozen=True)
class TravelModel:
    """Drumul = linia dreaptă × road_factor. Primii `urban_km` km se fac cu viteza urbană, restul cu cea extraurbană."""

    road_factor: float = 1.35
    speed_urban_kmh: float = 22.0
    speed_rural_kmh: float = 45.0
    urban_km: float = 10.0

    @classmethod
    def from_economics(cls, economics: dict) -> TravelModel:
        t = economics.get("travel") or {}
        return cls(
            road_factor=float(t.get("road_factor", 1.35)),
            speed_urban_kmh=float(t.get("avg_speed_kmh_urban", 22)),
            speed_rural_kmh=float(t.get("avg_speed_kmh_rural", 45)),
            urban_km=float(t.get("urban_km", 10)),
        )

    def road_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return haversine_km(lat1, lon1, lat2, lon2) * self.road_factor

    def minutes(self, road_km: float) -> float:
        urban = min(road_km, self.urban_km)
        rural = max(0.0, road_km - self.urban_km)
        return 60.0 * (urban / self.speed_urban_kmh + rural / self.speed_rural_kmh)
