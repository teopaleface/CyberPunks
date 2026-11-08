"""Shared agentic-v1 contracts; identity is always supplied by the server."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: Literal["analyze_queue", "recommend_queue", "route_brief", "case_brief", "prepare_operation"]
    scenario: str = Field(default="demo-vara", pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    language: Literal["ro", "en"] = "ro"
    work_item_id: str | None = Field(default=None, max_length=120)
    case_id: str | None = Field(default=None, max_length=120)
    action: (
        Literal[
            "create_case", "record_verdict", "review_work_item", "approve_plan", "set_availability", "request_human"
        ]
        | None
    ) = None
    data: dict[str, Any] = Field(default_factory=dict)
    preference: str | None = Field(default=None, max_length=4000)
    request_key: str | None = Field(default=None, max_length=120)


class TaskView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    goal: str
    scenario: str
    status: Literal[
        "queued",
        "running",
        "needs_information",
        "awaiting_confirmation",
        "completed",
        "failed",
        "cancelled",
        "needs_reconciliation",
    ]
    plan_version: str
    created_at: str
    updated_at: str
    reply: str = ""
    result: dict[str, Any] = Field(default_factory=dict)
    proposal: dict[str, Any] | None = None
    error: str | None = None
