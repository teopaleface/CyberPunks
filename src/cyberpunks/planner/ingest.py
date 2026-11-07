"""Încărcarea și validarea lucrărilor (prima parte din Decide: carantina intrărilor greșite).

Fiecare linie din `{A,B,C}.jsonl` trece prin două verificări:
1. contractul (`WorkItem`, pydantic): format, intervale, coerența sursă-tip-ID, abstain → human_review;
2. verificări de sens, în plus față de contract: ID duplicat, altă zi decât planul, punct în afara zonei
   de operare, valoare așteptată incoerentă cu scorul, fereastră de timp în altă zi.
Ce nu trece intră în carantină (decizia `rejected_invalid`, cu motivul). Restul planului merge mai departe.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from cyberpunks.common.contracts import WorkItem
from cyberpunks.planner.settings import Settings

SourceStatus = Literal["ok", "missing", "degraded"]
Origin = Literal["model", "stale", "fixture", "missing"]  # stale = ieșire veche, folosită după o eroare

# Cutia în care operează Rețele Electrice (Muntenia Sud, Dobrogea, Banat), cu margine. Contractul acceptă
# toată România; planificatorul respinge punctele din afara zonei distribuitorului.
SERVICE_BBOX = {"lat_min": 43.6, "lat_max": 46.6, "lon_min": 20.2, "lon_max": 29.8}
EV_TOLERANCE_LEI = 1.0  # expected_value_lei trebuie să fie score × value_if_true_lei (± 1 leu sau 2%)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Item:
    """O lucrare validă, cu amprenta exactă a liniei primite (pentru jurnal)."""

    wi: WorkItem
    sha256: str
    line_no: int
    origin: Origin

    @property
    def id(self) -> str:
        return self.wi.work_item_id


@dataclass
class Quarantined:
    source: str
    line: int
    work_item_id: str
    errors: list[str]
    raw: Any
    sha256: str

    def to_json(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "line": self.line,
            "work_item_id": self.work_item_id,
            "errors": self.errors,
            "raw": self.raw,
            "sha256": self.sha256,
        }


@dataclass
class SourceLoad:
    source: str
    path: Path | None
    origin: Origin
    items: list[Item] = field(default_factory=list)
    quarantined: list[Quarantined] = field(default_factory=list)
    note: str = ""
    status: SourceStatus = "ok"  # calculat de finalize_status
    optional: bool = False  # sursă suplimentară care încă nu există (de exemplu bilanțul): lipsa ei nu strică starea


def _pydantic_errors(exc: ValidationError) -> list[str]:
    out = []
    for err in exc.errors()[:5]:
        loc = ".".join(str(p) for p in err.get("loc", ()))
        out.append(f"{loc}: {err.get('msg')}" if loc else str(err.get("msg")))
    return out


def semantic_errors(wi: WorkItem, plan_date: date | None) -> list[str]:
    """Verificări de sens pe care contractul nu le face."""
    errs: list[str] = []
    if plan_date is not None and wi.target_date != plan_date:
        errs.append(f"lucrarea e pentru {wi.target_date.isoformat()}, planul e pentru {plan_date.isoformat()}")
    if wi.work_item_id[2:10] != wi.target_date.strftime("%Y%m%d"):
        errs.append("data din ID nu e target_date")
    if not wi.work_item_id.endswith(wi.asset_id):
        errs.append("ID-ul nu se termină cu asset_id")
    loc = wi.location
    if not (SERVICE_BBOX["lat_min"] <= loc.lat <= SERVICE_BBOX["lat_max"] and SERVICE_BBOX["lon_min"] <= loc.lon <= SERVICE_BBOX["lon_max"]):
        errs.append(f"punctul ({loc.lat:.4f}, {loc.lon:.4f}) e în afara zonei Rețele Electrice")
    expected = wi.prediction.score * wi.impact.value_if_true_lei
    if abs(wi.impact.expected_value_lei - expected) > max(EV_TOLERANCE_LEI, 0.02 * expected):
        errs.append(
            f"expected_value_lei={wi.impact.expected_value_lei:.2f} nu e score × value_if_true_lei = {expected:.2f}"
        )
    if wi.impact.expected_value_lei < 0:
        errs.append("valoare așteptată negativă")
    tw = wi.time_window
    if tw is not None and tw.start.date() != wi.target_date and tw.end.date() != wi.target_date:
        errs.append("fereastra de timp nu e în ziua lucrării")
    return errs


def load_source(source: str, path: Path | None, origin: Origin, plan_date: date | None, seen: set[str]) -> SourceLoad:
    """Citește un fișier JSONL de lucrări. Linii goale ignorate; JSON stricat, contract sau sens greșit → carantină."""
    load = SourceLoad(source=source, path=path, origin=origin)
    if path is None or not path.exists():
        load.origin = "missing"
        load.note = "fișierul lipsește"
        return load
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        load.origin = "missing"
        load.note = f"nu se poate citi: {exc}"
        return load
    qids: set[str] = set()

    def unique(qid: str, line_no: int) -> str:
        """ID unic pentru o intrare respinsă (un duplicat nu are voie să ascundă lucrarea validă cu același ID)."""
        if qid in seen or qid in qids:
            qid = f"{qid}~linia{line_no}"
        qids.add(qid)
        return qid

    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        digest = sha256_text(line)
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            load.quarantined.append(
                Quarantined(source, line_no, unique(f"{source}-linia-{line_no}", line_no), [f"JSON stricat: {exc.msg}"], line[:500], digest)
            )
            continue
        raw_id = raw.get("work_item_id") if isinstance(raw, dict) else None
        qid = unique(raw_id if isinstance(raw_id, str) and raw_id else f"{source}-linia-{line_no}", line_no)
        if isinstance(raw, dict) and raw.get("source") not in (None, source):
            load.quarantined.append(
                Quarantined(source, line_no, qid, [f"lucrare din sursa {raw.get('source')!r} în fișierul sursei {source}"], raw, digest)
            )
            continue
        try:
            wi = WorkItem.model_validate(raw)
        except ValidationError as exc:
            load.quarantined.append(Quarantined(source, line_no, qid, _pydantic_errors(exc), raw, digest))
            continue
        errs = semantic_errors(wi, plan_date)
        if wi.work_item_id in seen:
            errs.append("ID duplicat: lucrarea a mai apărut o dată (se păstrează prima apariție)")
        if errs:
            load.quarantined.append(Quarantined(source, line_no, qid, errs, raw, digest))
            continue
        seen.add(wi.work_item_id)
        load.items.append(Item(wi=wi, sha256=digest, line_no=line_no, origin=origin))
    return load


def infer_plan_date(paths: list[Path]) -> date | None:
    """Data cea mai frecventă din target_date, când scenariul nu are încă dată fixată."""
    counts: Counter[str] = Counter()
    for p in paths:
        if not p or not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line).get("target_date")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(d, str):
                counts[d] += 1
    if not counts:
        return None
    try:
        return date.fromisoformat(counts.most_common(1)[0][0])
    except ValueError:
        return None


def finalize_status(load: SourceLoad, settings: Settings) -> None:
    """ok / degraded / missing, după origine și după cota de linii respinse."""
    if load.origin == "missing":
        load.status = "missing"
        return
    total = len(load.items) + len(load.quarantined)
    share = len(load.quarantined) / total if total else 0.0
    limit = float(settings.rule("global", "degraded_invalid_share", default=0.2))
    load.status = "degraded" if (load.origin != "model" or share > limit or not load.items) else "ok"
