"""Contractele operaționale. Actorul vine exclusiv de la serverul web autentificat."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Actor(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    user_id: str = Field(min_length=1, max_length=120)
    role: Literal["customer", "technician", "dispatcher"]
    organization_id: str = Field(min_length=1, max_length=120)
    crew_id: str | None = Field(default=None, max_length=64)
    connection_ids: list[str] = Field(default_factory=list, max_length=100)
    permissions: list[str] = Field(default_factory=list, max_length=100)


Action = Literal[
    "create_case", "record_verdict", "review_work_item", "approve_plan", "set_availability", "request_human"
]


class ProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Action
    data: dict[str, Any]
    scenario: str = Field(default="demo-vara", pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")


class Data(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)
    case_id: str | None = Field(default=None, max_length=64)
    case_version: int | None = Field(default=None, ge=1)
    plan_version: str | None = Field(default=None, max_length=80)
    note: str | None = Field(default=None, max_length=2000)


class CreateCase(Data):
    connection_id: str = Field(min_length=1, max_length=64)
    symptom: str = Field(min_length=3, max_length=2000)
    symptom_type: Literal["voltage", "meter", "outage", "other"] = "other"


class Verdict(Data):
    work_item_id: str = Field(min_length=1, max_length=120)
    outcome: Literal["confirmed", "not_found", "other_problem", "no_access"]


class Review(Data):
    work_item_id: str = Field(min_length=1, max_length=120)
    decision: Literal["approve", "reject", "defer"]


class Approval(Data):
    plan_id: str = Field(min_length=1, max_length=120)
    crew_id: str | None = Field(default=None, max_length=64)


class Availability(Data):
    case_id: str = Field(min_length=1, max_length=64)
    start: str = Field(min_length=10, max_length=40)
    end: str = Field(min_length=10, max_length=40)


class HumanRequest(Data):
    connection_id: str | None = Field(default=None, max_length=64)
    reason: str = Field(min_length=3, max_length=2000)
    priority: Literal["normal", "urgent"] = "normal"


DATA_MODELS = {
    "create_case": CreateCase,
    "record_verdict": Verdict,
    "review_work_item": Review,
    "approve_plan": Approval,
    "set_availability": Availability,
    "request_human": HumanRequest,
}


class OperationError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code, self.code, self.message = status_code, code, message
        super().__init__(message)
