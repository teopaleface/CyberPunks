"""Formatele comune de date (contractele) dintre firele de lucru.

Sursa de adevăr pentru toate formatele. Schemele JSON din `contracts/` se generează de aici:

    uv run python -m cyberpunks.common.contracts export-schemas
    uv run python -m cyberpunks.common.contracts validate contracts/fixtures/work_items_A.jsonl

Proprietar: orchestratorul (conversația care coordonează). Firele cer schimbări în `status/<fir>.md`,
secțiunea "Cereri către orchestrator". Nu modificați fișierul direct.

Convenții:
- Ora: ISO 8601 cu fus orar (Europe/Bucharest, de exemplu 2026-11-09T08:00:00+02:00).
- Bani: lei (RON). Energie: kWh. Tensiune: unități relative (pu), 1.0 = nominal.
- Coordonate: WGS84. Validatorul respinge punctele din afara României (intrare greșită).
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

CONTRACT_VERSION = "1.0"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------------------------
# WorkItem: ieșirea fiecărui model (A, B, C), intrarea planificatorului
# --------------------------------------------------------------------------------------------


class Source(str, Enum):
    A = "A"  # contoare defecte sau manipulate
    B = "B"  # furtună: risc de avarii, echipe trimise din timp
    C = "C"  # prosumatori: tensiune prea mare în posturile de transformare


class Kind(str, Enum):
    meter_inspection = "meter_inspection"  # A
    storm_prepositioning = "storm_prepositioning"  # B
    voltage_mitigation = "voltage_mitigation"  # C


KIND_BY_SOURCE = {
    Source.A: Kind.meter_inspection,
    Source.B: Kind.storm_prepositioning,
    Source.C: Kind.voltage_mitigation,
}


class AssetType(str, Enum):
    meter = "meter"
    zone = "zone"
    transformer_post = "transformer_post"


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class RecommendedAction(str, Enum):
    inspect_on_site = "inspect_on_site"  # A: verificare la fața locului
    remote_reading = "remote_reading"  # A: citire la distanță la cerere (sistemul de contorizare)
    watchlist = "watchlist"  # A, C: urmărire, fără vizită
    human_review = "human_review"  # orice sursă: "nu sunt sigur", decide un om
    preposition_crew = "preposition_crew"  # B: echipă mutată din timp în zonă
    adjust_tap = "adjust_tap"  # C: schimbarea prizei transformatorului (cere întrerupere planificată)
    measurement_campaign = "measurement_campaign"  # C: analizor de calitate a energiei montat la post
    notify_customers = "notify_customers"  # C: mesaj către prosumatori (PPC Energy), fără echipă
    office_correction = "office_correction"  # bilanț: corecție în bază (client la postul greșit), fără deplasare
    grid_inspection = "grid_inspection"  # bilanț: echipă de rețea (lv_grid) pentru pierderi tehnice, faze
    phase_rebalance = "phase_rebalance"  # C (scara): mută câteva case pe altă fază
    offer_battery = "offer_battery"  # C (scara): ofertă de baterii pentru prosumatori (PPC Energie)
    export_limit = "export_limit"  # C (scara): limită de injecție pe oră
    transformer_upgrade = "transformer_upgrade"  # C (scara): transformator nou (investiție)
    no_action = "no_action"


class CrewSkill(str, Enum):
    metering = "metering"  # contorizare
    lv_grid = "lv_grid"  # joasă tensiune
    mv_grid = "mv_grid"  # medie tensiune


class Location(_Strict):
    lat: float = Field(ge=43.5, le=48.5, description="Latitudine WGS84, în România")
    lon: float = Field(ge=20.0, le=30.0, description="Longitudine WGS84, în România")
    zone_id: str = Field(min_length=1, description="Zona operativă (vezi config/area.yaml)")
    county: str | None = None
    label: str | None = Field(default=None, description="Etichetă lizibilă, de exemplu 'PT 1432, Chiajna'")


class TimeWindow(_Strict):
    start: datetime
    end: datetime

    @model_validator(mode="after")
    def _ordered(self) -> TimeWindow:
        if self.end <= self.start:
            raise ValueError("time_window.end trebuie să fie după start")
        return self


class Prediction(_Strict):
    model_id: str = Field(min_length=1, description="De exemplu 'a-lgbm', 'b-lgbm-quantile', 'c-surrogate'")
    model_version: str = Field(min_length=1, description="Versiunea modelului, de exemplu 'a-lgbm@3f2c1ab'")
    prediction_id: str = Field(min_length=1, description="ID unic al predicției (uuid4)")
    label: str = Field(min_length=1, description="Clasa sau problema estimată: 'faulty', 'tamper', 'outage_risk', 'overvoltage'")
    score: float = Field(ge=0.0, le=1.0, description="Probabilitate calibrată ca problema să fie reală")
    interval_low: float | None = Field(default=None, ge=0.0, le=1.0)
    interval_high: float | None = Field(default=None, ge=0.0, le=1.0)
    point_estimate: float | None = Field(default=None, description="Valoare estimată: tensiune maximă (pu), clienți afectați etc.")
    point_unit: str | None = None
    point_interval: tuple[float, float] | None = Field(default=None, description="Interval pentru point_estimate (P10, P90)")
    confidence: Confidence
    abstain: bool = Field(default=False, description="Modelul spune 'nu sunt sigur'")
    abstain_reason: str | None = None

    @model_validator(mode="after")
    def _intervals(self) -> Prediction:
        bounded = self.interval_low is not None and self.interval_high is not None
        if bounded and not (self.interval_low <= self.score <= self.interval_high):
            raise ValueError("score trebuie să fie între interval_low și interval_high")
        if self.abstain and not self.abstain_reason:
            raise ValueError("abstain=True cere abstain_reason")
        return self


class Impact(_Strict):
    expected_value_lei: float = Field(description="score × value_if_true_lei, minus nimic; costul vizitei îl scade planificatorul")
    value_if_true_lei: float = Field(ge=0.0, description="Câți lei se câștigă sau se evită dacă problema e reală și o rezolvăm")
    customers_affected: int = Field(default=0, ge=0)
    urgency_hours: float = Field(gt=0.0, description="În câte ore trebuie acționat ca să mai conteze")
    safety_flag: bool = Field(default=False, description="Risc pentru oameni (de exemplu șuntare cu risc de incendiu)")
    assumptions_ref: str | None = Field(default=None, description="Cheia din config/economics.yaml folosită la calcul")


class Effort(_Strict):
    duration_min: int = Field(gt=0, le=720)
    crew_skill: CrewSkill
    crew_size: int = Field(default=2, ge=1, le=6)
    requires_planned_outage: bool = False


class Factor(_Strict):
    feature: str
    label_ro: str = Field(description="Motivul în cuvinte simple, de exemplu '9 zile cu consum zero'")
    value: float | str | None = None
    contribution: float = Field(description="Contribuția la scor (de exemplu valoarea SHAP)")


class SimilarCase(_Strict):
    case_id: str
    outcome: str = Field(description="Ce s-a confirmat atunci, de exemplu 'contor_blocat', 'furtuna_confirmata'")
    similarity: float = Field(ge=0.0, le=1.0)
    note_ro: str | None = None


class Explanation(_Strict):
    top_factors: list[Factor] = Field(min_length=1, max_length=8)
    similar_cases: list[SimilarCase] = Field(default_factory=list, max_length=5)
    summary_ro: str = Field(min_length=1, description="O frază generată din șablon, cu cifrele verificate în cod")


class DataQuality(_Strict):
    missing_ratio: float = Field(ge=0.0, le=1.0)
    input_issues: list[str] = Field(default_factory=list, description="Probleme găsite la intrare și cum au fost tratate")
    synthetic: bool = Field(description="True dacă activul sau datele sunt sintetice")
    data_sources: list[str] = Field(min_length=1, description="Surse citate, de exemplu 'SGCC', 'Open-Meteo forecast'")


class WorkItem(_Strict):
    contract_version: Literal["1.0"] = CONTRACT_VERSION
    work_item_id: str = Field(pattern=r"^[ABC]-\d{8}-[A-Za-z0-9_.-]+$", description="<sursă>-<YYYYMMDD>-<asset_id>")
    source: Source
    kind: Kind
    asset_id: str = Field(min_length=1)
    asset_type: AssetType
    location: Location
    target_date: date
    time_window: TimeWindow | None = None
    prediction: Prediction
    impact: Impact
    effort: Effort
    explanation: Explanation
    data_quality: DataQuality
    recommended_action: RecommendedAction
    created_at: datetime
    extra: dict[str, Any] = Field(default_factory=dict, description="Câmpuri specifice sursei (serii pentru grafice etc.)")

    @model_validator(mode="after")
    def _consistency(self) -> WorkItem:
        if self.work_item_id[0] != self.source.value:
            raise ValueError("work_item_id trebuie să înceapă cu litera sursei")
        if KIND_BY_SOURCE[self.source] != self.kind:
            raise ValueError(f"sursa {self.source.value} trebuie să aibă kind={KIND_BY_SOURCE[self.source].value}")
        if self.prediction.abstain and self.recommended_action != RecommendedAction.human_review:
            raise ValueError("o predicție cu abstain=True trebuie să recomande human_review")
        return self


class RemedyOption(_Strict):
    """O treaptă din scara de soluții pentru tensiune (C), în `WorkItem.extra["remedy_options"]` (listă).

    Efectul se calculează cu calculul de rețea al lui C, nu se ghicește.
    """

    action: RecommendedAction
    cost_lei: float = Field(ge=0.0)
    p90_after_pu: float = Field(gt=0.5, lt=1.5, description="P90 al tensiunii maxime după soluție")
    effect_pu: float = Field(description="Cât scade P90 (pu), negativ = scade")
    confidence: Confidence
    duration_min: int = Field(ge=0, description="Timp de lucru; 0 pentru mesaje")
    needs_crew: bool
    crew_skill: CrewSkill | None = None
    combinable: bool = Field(default=True, description="Se poate combina cu alte trepte")
    note_ro: str
    # Treapta 3 (mesaje țintite pe post) și treapta 4 (baterii pe profil), completări aprobate la 14:00
    participation_rate: float | None = Field(default=None, ge=0.0, le=1.0, description="Rata de participare folosită (IPOTEZĂ)")
    risk_hours: list[str] = Field(default_factory=list, description="Orele cu risc vizate, de exemplu ['12:00-15:00']")
    inverter_trips_avoided: float | None = Field(default=None, ge=0.0, description="Opriri ale invertoarelor evitate")
    message_preview_ro: str | None = Field(default=None, description="Textul de grup, pe post, fără date personale")
    customers_targeted: int | None = Field(default=None, ge=0)
    battery_kwh_total: float | None = Field(default=None, ge=0.0, description="kWh de baterii propuși, total pe post")
    revenue_lei: float | None = Field(default=None, ge=0.0, description="Venit estimat pentru PPC Energie")
    payback_years: float | None = Field(default=None, ge=0.0, description="Perioada de recuperare pentru client")


class BilantFusion(_Strict):
    """Confirmarea independentă bilanț + contor, în `WorkItem.extra["fusion"]` pentru lucrările A pe contoare."""

    post_id: str
    bilant_prediction_id: str
    post_excess_loss_kwh_day: float = Field(description="Lipsa peste normal la post, kWh pe zi")
    post_excess_loss_lei_month: float
    a_score: float = Field(ge=0.0, le=1.0, description="Scorul inițial al modelului A")
    combined_score: float = Field(ge=0.0, le=1.0, description="Scorul după confirmare (devine prediction.score)")
    note_ro: str


# --------------------------------------------------------------------------------------------
# Plan: ieșirea planificatorului (agentul)
# --------------------------------------------------------------------------------------------


class Stop(_Strict):
    seq: int = Field(ge=1)
    work_item_id: str
    eta: datetime
    duration_min: int = Field(gt=0)
    travel_km: float = Field(ge=0.0)


class Route(_Strict):
    crew_id: str
    depot_id: str
    depart_at: datetime | None = Field(default=None, description="Plecarea din bază")
    return_at: datetime | None = Field(default=None, description="Întoarcerea în bază")
    stops: list[Stop]
    total_km: float = Field(ge=0.0)
    total_work_min: int = Field(ge=0)
    total_travel_min: int = Field(ge=0)


class DecisionType(str, Enum):
    assigned = "assigned"  # intră în traseul unei echipe
    deferred = "deferred"  # amânat (sub prag sau fără capacitate)
    human_review = "human_review"  # "nu sunt sigur": decide un om
    remote_action = "remote_action"  # acțiune fără echipă (citire la distanță)
    notify = "notify"  # mesaj către clienți
    rejected_invalid = "rejected_invalid"  # intrare greșită, pusă în carantină


class Decision(_Strict):
    work_item_id: str
    decision: DecisionType
    reason_ro: str = Field(min_length=1)
    rule_id: str = Field(description="Regula din stratul de decizie care a produs decizia")
    threshold: dict[str, float] = Field(default_factory=dict, description="Pragurile folosite, cu valorile lor")
    priority_score: float | None = None
    rank: int | None = Field(default=None, ge=1)
    crew_id: str | None = None
    audit_id: str


class Alert(_Strict):
    alert_id: str
    severity: Literal["info", "warning", "critical"]
    title_ro: str
    body_ro: str
    work_item_ids: list[str] = Field(default_factory=list)
    channel: Literal["dispecerat", "echipa", "clienti"]
    created_at: datetime


class Notification(_Strict):
    notification_id: str
    audience: Literal["prosumatori", "clienti_zona", "echipa"]
    asset_id: str
    message_ro: str
    scheduled_for: datetime
    work_item_id: str | None = None
    demo_only: bool = Field(default=True, description="În demo nu se trimite nimic în afară")


class PlanSummary(_Strict):
    items_in: int = Field(ge=0)
    items_valid: int = Field(ge=0)
    items_invalid: int = Field(ge=0)
    assigned: int = Field(ge=0)
    deferred: int = Field(ge=0)
    human_review: int = Field(ge=0)
    remote_actions: int = Field(ge=0)
    notifications: int = Field(ge=0)
    crews_used: int = Field(ge=0)
    expected_value_lei: float
    total_km: float = Field(ge=0.0)


class Plan(_Strict):
    contract_version: Literal["1.0"] = CONTRACT_VERSION
    plan_id: str
    plan_date: date
    generated_at: datetime
    planner_version: str
    scenario: str
    summary: PlanSummary
    routes: list[Route]
    decisions: list[Decision]
    alerts: list[Alert] = Field(default_factory=list)
    notifications: list[Notification] = Field(default_factory=list)
    sources_status: dict[Literal["A", "B", "C"], Literal["ok", "missing", "degraded"]]


class AuditRecord(_Strict):
    audit_id: str
    ts: datetime
    actor: Literal["agent", "human"]
    action: str
    work_item_id: str | None = None
    prediction_id: str | None = None
    model_version: str | None = None
    rule_id: str | None = None
    threshold: dict[str, float] = Field(default_factory=dict)
    inputs_sha256: str | None = None
    note: str | None = None


# --------------------------------------------------------------------------------------------
# Raportul de evaluare al fiecărui model (reports/<A|B|C>/metrics.json)
# --------------------------------------------------------------------------------------------


class ModelReport(_Strict):
    contract_version: Literal["1.0"] = CONTRACT_VERSION
    source: Source
    model_id: str
    model_version: str
    task: str = Field(description="De exemplu 'clasificare dezechilibrată', 'regresie cuantilă'")
    dataset: list[str] = Field(min_length=1, description="Surse de date folosite, citate")
    split: str = Field(description="Cum e făcut setul de test (pe timp, pe clienți, pe rețele nevăzute)")
    test_size: int = Field(gt=0)
    primary_metric: str
    metrics: dict[str, float]
    baseline_id: str
    baseline_metrics: dict[str, float]
    synthetic_share: float = Field(ge=0.0, le=1.0, description="Ce parte din datele de test e sintetică")
    created_at: datetime
    reproduce_cmd: str = Field(description="Comanda care refăce exact aceste cifre")

    @model_validator(mode="after")
    def _primary_present(self) -> ModelReport:
        if self.primary_metric not in self.metrics or self.primary_metric not in self.baseline_metrics:
            raise ValueError("primary_metric trebuie să existe și în metrics, și în baseline_metrics")
        return self


# --------------------------------------------------------------------------------------------
# Seria pentru graficul din detaliul unei lucrări (outputs/series/<scenariu>/<work_item_id>.json)
# --------------------------------------------------------------------------------------------


class SeriesPoint(_Strict):
    t: datetime | date
    value: float | None = Field(default=None, description="Valoarea observată sau prognozată")
    expected: float | None = Field(default=None, description="Ce ar fi fost normal (A) sau P50 (B, C)")
    low: float | None = Field(default=None, description="Marginea de jos a intervalului (P10)")
    high: float | None = Field(default=None, description="Marginea de sus a intervalului (P90)")
    flag: str | None = Field(default=None, description="De exemplu 'zero', 'gol', 'salt', 'peste_limita'")


class SeriesAnnotation(_Strict):
    t: datetime | date
    label_ro: str


class Series(_Strict):
    contract_version: Literal["1.0"] = CONTRACT_VERSION
    work_item_id: str
    source: Source
    title_ro: str
    unit: str = Field(description="kWh, km/h, pu etc.")
    points: list[SeriesPoint] = Field(min_length=1)
    thresholds: dict[str, float] = Field(default_factory=dict, description="De exemplu {'limita_tensiune_pu': 1.10}")
    annotations: list[SeriesAnnotation] = Field(default_factory=list)
    synthetic: bool


MODELS: dict[str, type[BaseModel]] = {
    "work_item": WorkItem,
    "plan": Plan,
    "audit": AuditRecord,
    "model_report": ModelReport,
    "series": Series,
    "remedy_option": RemedyOption,
    "bilant_fusion": BilantFusion,
}


def _guess_model(path: Path) -> type[BaseModel]:
    name = path.name
    if name.startswith("work_items") or name.endswith(".jsonl") and "audit" not in name:
        return WorkItem
    if "audit" in name:
        return AuditRecord
    if "plan" in name:
        return Plan
    if "metrics" in name or "report" in name:
        return ModelReport
    if path.parent.name and "series" in str(path):
        return Series
    raise SystemExit(f"Nu știu ce contract are {path}. Folosește: validate <fișier> --as <{'|'.join(MODELS)}>")


def validate_file(path: Path, model: type[BaseModel] | None = None) -> tuple[int, list[str]]:
    """Validează un fișier .json sau .jsonl. Întoarce (nr. obiecte valide, erori)."""
    model = model or _guess_model(path)
    errors: list[str] = []
    ok = 0
    text = path.read_text(encoding="utf-8")
    records: list[tuple[int, Any]]
    if path.suffix == ".jsonl":
        records = [(i, json.loads(line)) for i, line in enumerate(text.splitlines(), 1) if line.strip()]
    else:
        records = [(1, json.loads(text))]
    for line_no, obj in records:
        try:
            model.model_validate(obj)
            ok += 1
        except ValidationError as exc:
            errors.append(f"{path}:{line_no}: {exc.error_count()} erori: {exc.errors()[0]['loc']} {exc.errors()[0]['msg']}")
    return ok, errors


def export_schemas(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in MODELS.items():
        p = out_dir / f"{name}.schema.json"
        p.write_text(json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(p)
    return written


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0
    cmd, *rest = argv
    if cmd == "export-schemas":
        out = Path(rest[0]) if rest else Path("contracts")
        for p in export_schemas(out):
            print(f"scris {p}")
        return 0
    if cmd == "validate":
        model = None
        if "--as" in rest:
            i = rest.index("--as")
            model = MODELS[rest[i + 1]]
            rest = rest[:i] + rest[i + 2 :]
        total_err = 0
        for f in rest:
            ok, errs = validate_file(Path(f), model)
            total_err += len(errs)
            print(f"{f}: {ok} valide, {len(errs)} invalide")
            for e in errs[:20]:
                print("  " + e)
        return 1 if total_err else 0
    print(f"Comandă necunoscută: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
