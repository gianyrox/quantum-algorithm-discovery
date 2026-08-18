from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.core.provenance import ProvenanceRecord


class DocumentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str | None = None
    section_type: str | None = None
    order: int = Field(ge=0)
    text: str
    parent_id: str | None = None


class EquationOccurrence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    section_id: str | None = None
    label: str | None = None
    latex: str | None = None
    mathml: str | None = None
    surrounding_text: str | None = None


class FigureOccurrence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    section_id: str | None = None
    label: str | None = None
    caption: str | None = None
    asset_id: str | None = None


class TableOccurrence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    section_id: str | None = None
    label: str | None = None
    caption: str | None = None
    structured_data: list[dict[str, object]] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_id: str
    asset_id: str
    source_format: str
    parser: str
    parser_version: str | None = None
    sections: list[DocumentSection] = Field(default_factory=list)
    equations: list[EquationOccurrence] = Field(default_factory=list)
    figures: list[FigureOccurrence] = Field(default_factory=list)
    tables: list[TableOccurrence] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
