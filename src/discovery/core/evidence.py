from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from discovery.problems.enums import EvidenceKind


class EvidenceLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    paragraph: int | None = Field(default=None, ge=1)
    equation_label: str | None = None
    figure_label: str | None = None
    table_label: str | None = None
    quote: str | None = None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: EvidenceKind
    location: EvidenceLocation | None = None
    source_url: HttpUrl | None = None
    source_identifier: str | None = None
    note: str | None = None
