from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvidenceSpan(BaseModel):
    """Character-addressable evidence for one extracted problem field."""

    model_config = ConfigDict(extra="forbid")

    field: str
    document_id: str | None = None
    section_id: str | None = None
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    text: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    extraction_rule: str | None = None


class FieldConfidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    confidence: float = Field(ge=0, le=1)
    evidence_count: int = Field(default=0, ge=0)
    unresolved: bool = False
