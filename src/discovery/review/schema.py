from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReviewDecision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    REVISE = "revise"
    DEFER = "defer"


class ReviewEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    object_type: str
    object_id: str
    reviewer_id: str
    decision: ReviewDecision
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
