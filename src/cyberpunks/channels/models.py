"""Intrări limitate și intenții fără identitate sau acces la instrumente."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class HistoryMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class Selection(StrictModel):
    connection_id: str | None = Field(default=None, max_length=120)
    work_item_id: str | None = Field(default=None, max_length=120)
    case_id: str | None = Field(default=None, max_length=120)


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)
    scenario: str = Field(default="demo-vara", pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    selection: Selection | None = None


class VoiceRequest(StrictModel):
    scenario: str = Field(default="demo-vara", pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")


class IntentionData(StrictModel):
    # Every field is required and nullable in the model schema. No open dictionaries.
    connection_id: str | None
    work_item_id: str | None
    case_id: str | None
    plan_id: str | None
    crew_id: str | None
    symptom: str | None
    symptom_type: Literal["voltage", "meter", "outage", "other"] | None
    outcome: Literal["confirmed", "not_found", "other_problem", "no_access"] | None
    decision: Literal["approve", "reject", "defer"] | None
    start: str | None
    end: str | None
    note: str | None
    reason: str | None
    priority: Literal["normal", "urgent"] | None


class Evidence(StrictModel):
    # RFC 6901 pointer into the actual scoped context; exact JSON value is checked.
    path: str = Field(min_length=1, max_length=500)
    value_json: str = Field(max_length=12000)


class Intention(StrictModel):
    kind: Literal["read", "clarify", "prepare", "refuse", "task"]
    task_goal: Literal["analyze_queue", "recommend_queue", "route_brief", "case_brief"] | None = None
    language: Literal["ro", "en"]
    reply: str = Field(min_length=1, max_length=2400)
    action: (
        Literal[
            "create_case", "record_verdict", "review_work_item", "approve_plan", "set_availability", "request_human"
        ]
        | None
    )
    data: IntentionData
    evidence: list[Evidence] = Field(max_length=12)


class ChannelError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 503):
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(message)
