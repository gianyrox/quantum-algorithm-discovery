from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.core.provenance import ProvenanceRecord


class SymbolGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    meaning: str | None = None
    entity_type: str | None = None
    units: str | None = None
    evidence_text: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)
    context_before: str | None = None
    context_after: str | None = None
    source_section_id: str | None = None


class MathNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operator: str
    value: str | None = None
    children: list[MathNode] = Field(default_factory=list)


class MathExpression(BaseModel):
    """Multi-view mathematical representation; no single view is treated as truth."""

    model_config = ConfigDict(extra="forbid")

    id: str
    work_id: str
    equation_label: str | None = None
    raw_source: str | None = None
    latex: str | None = None
    presentation_mathml: str | None = None
    content_mathml: str | None = None
    semantic_form: str | None = None
    ast: MathNode | None = None
    operator_graph: dict[str, object] = Field(default_factory=dict)
    symbols: list[SymbolGrounding] = Field(default_factory=list)
    alpha_normalized: str | None = None
    units: list[str] = Field(default_factory=list)
    cas_variants: list[str] = Field(default_factory=list)
    provenance: list[ProvenanceRecord] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    context_before: str | None = None
    context_after: str | None = None
    source_section_id: str | None = None


class MathematicalStructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    structure_type: str
    properties: list[str] = Field(default_factory=list)
    operators: list[str] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    source_expression_ids: list[str] = Field(default_factory=list)
