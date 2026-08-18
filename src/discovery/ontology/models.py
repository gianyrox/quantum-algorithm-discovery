from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DisciplineRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    discipline_id: str
    name: str
    parent_id: str | None = None
    level: int
    description: str | None = None


class ConceptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    discipline_id: str | None = None
    canonical_concept: str
    concept_type: str = "other"
    short_definition: str | None = None


class TermRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    term: str
    term_type: str
    context: str = ""


class ConceptRelationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_concept_id: str
    relationship: str
    target_concept_id: str


class OntologyImportReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disciplines: int = 0
    concepts: int = 0
    terms: int = 0
    relationships: int = 0
    models_equations_methods: int = 0
    warnings: list[str] = Field(default_factory=list)
