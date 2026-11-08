"""Setările agentului, citite din config/: ipoteze economice, echipe, baze, zonă, scenarii, praguri.

Nimic din stratul de decizie nu are cifre scrise de mână: pragurile stau în config/planner.yaml,
ipotezele economice în config/economics.yaml (cu sursa sau cu eticheta IPOTEZĂ).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from cyberpunks.common.paths import CONFIG

TZ = ZoneInfo("Europe/Bucharest")


def load_yaml(name: str, config_dir: Path | None = None) -> dict[str, Any]:
    path = (config_dir or CONFIG) / f"{name}.yaml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _parse_hhmm(value: str) -> time:
    hh, mm = str(value).split(":")
    return time(int(hh), int(mm))


@dataclass(frozen=True)
class Depot:
    depot_id: str
    label_ro: str
    lat: float
    lon: float
    region: str


@dataclass(frozen=True)
class Crew:
    crew_id: str
    depot_id: str
    skills: frozenset[str]
    size: int


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    label_ro: str
    date_spec: str | None
    weather: str | None

    def resolve_date(self, override: str | date | None = None, today: date | None = None) -> date | None:
        """Data planului: parametrul explicit, data din config sau mâine. None dacă data nu e încă aleasă."""
        if override:
            return override if isinstance(override, date) else date.fromisoformat(str(override))
        spec = (self.date_spec or "").strip()
        if spec == "auto_tomorrow":
            base = today or datetime.now(TZ).date()
            return base + timedelta(days=1)
        try:
            return date.fromisoformat(spec)
        except ValueError:
            return None  # de exemplu "TBD-B": data o alege firul B


@dataclass
class Settings:
    economics: dict[str, Any]
    planner: dict[str, Any]
    depots: dict[str, Depot]
    crews: list[Crew]
    shift_start: time
    shift_end: time
    regions: dict[str, dict[str, Any]]
    scenarios: dict[str, Scenario]
    area: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_dir: Path | None = None) -> Settings:
        economics = load_yaml("economics", config_dir)
        planner = load_yaml("planner", config_dir)
        area = load_yaml("area", config_dir)
        crews_cfg = load_yaml("crews", config_dir)
        scen_cfg = load_yaml("scenarios", config_dir)
        depots = {
            d["depot_id"]: Depot(d["depot_id"], d.get("label_ro", d["depot_id"]), float(d["lat"]), float(d["lon"]), d.get("region", ""))
            for d in area.get("depots", [])
        }
        crews = [
            Crew(c["crew_id"], c["depot_id"], frozenset(c.get("skills", [])), int(c.get("size", 2)))
            for c in crews_cfg.get("crews", [])
        ]
        shift = crews_cfg.get("shift", {"start": "08:00", "end": "16:00"})
        scenarios = {
            sid: Scenario(sid, s.get("label_ro", sid), None if s.get("date") is None else str(s.get("date")), s.get("weather"))
            for sid, s in (scen_cfg.get("scenarios") or {}).items()
        }
        return cls(
            economics=economics,
            planner=planner,
            depots=depots,
            crews=crews,
            shift_start=_parse_hhmm(shift["start"]),
            shift_end=_parse_hhmm(shift["end"]),
            regions=area.get("regions", {}),
            scenarios=scenarios,
            area=area,
        )

    # ---- acces comod, cu valori implicite documentate ----

    def econ(self, section: str, key: str, default: float | None = None) -> float:
        value = (self.economics.get(section) or {}).get(key, default)
        if value is None:
            raise KeyError(f"lipsește {section}.{key} din config/economics.yaml")
        return float(value)

    def rule(self, *path: str, default: Any = None) -> Any:
        node: Any = self.planner
        for key in path:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def region_of_county(self, county: str | None) -> str | None:
        if not county:
            return None
        for rid, reg in self.regions.items():
            if county in (reg.get("counties") or []):
                return rid
        return None

    def depot_region(self, depot_id: str) -> str:
        return self.depots[depot_id].region

    def shift_bounds(self, plan_date: date) -> tuple[datetime, datetime]:
        return (
            datetime.combine(plan_date, self.shift_start, tzinfo=TZ),
            datetime.combine(plan_date, self.shift_end, tzinfo=TZ),
        )
