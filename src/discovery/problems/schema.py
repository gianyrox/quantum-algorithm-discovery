from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.core.evidence import Evidence
from discovery.problems.enums import (
    ExtractionMethod,
    ReviewStatus,
    TaskFamily,
)
from discovery.problems.evidence import EvidenceSpan, FieldConfidence


class MathematicalObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    object_type: str
    role: str | None = None
    representation: str | None = None
    notes: str | None = None


class ScaleParameter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    meaning: str
    symbol: str | None = None
    regime: str | None = None


class ComplexityClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: str
    claim: str
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    field_confidence: list[FieldConfidence] = Field(default_factory=list)


class ScientificMethod(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    method_type: str | None = None
    role: str | None = None
    approximation: bool | None = None


class ProblemInstance(BaseModel):
    """
    A structured representation of a computational problem evidenced by
    a scientific work.

    The paper/work is evidence for the problem representation; it is not
    itself the core research object.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)

    # Source identity
    source_work_id: str
    source_version_id: str | None = None

    # Human-readable interpretation
    natural_language_statement: str
    task_family: TaskFamily

    # Computational contract
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    objective: str | None = None
    constraints: list[str] = Field(default_factory=list)

    # Computational setting
    state_space: str | None = None
    access_model: str | None = None
    data_model: str | None = None

    # Mathematical structure
    mathematical_objects: list[MathematicalObject] = Field(default_factory=list)
    operators: list[str] = Field(default_factory=list)
    equations: list[str] = Field(default_factory=list)
    structural_properties: list[str] = Field(default_factory=list)

    # Algorithmic structure
    algorithmic_operations: list[str] = Field(default_factory=list)
    known_methods: list[ScientificMethod] = Field(default_factory=list)
    classical_baselines: list[ScientificMethod] = Field(default_factory=list)

    # Scaling and complexity
    scale_parameters: list[ScaleParameter] = Field(default_factory=list)
    complexity_claims: list[ComplexityClaim] = Field(default_factory=list)
    reported_bottlenecks: list[str] = Field(default_factory=list)

    # Scientific assumptions
    assumptions: list[str] = Field(default_factory=list)
    approximations: list[str] = Field(default_factory=list)

    # Cross-domain structural descriptors
    stochasticity: str | None = None
    symmetry: list[str] = Field(default_factory=list)
    sparsity: str | None = None
    locality: str | None = None
    graph_structure: str | None = None
    dimensionality: str | None = None
    conditioning: str | None = None

    # Evidence and provenance
    evidence: list[Evidence] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    field_confidence: list[FieldConfidence] = Field(default_factory=list)

    extraction_method: ExtractionMethod
    extractor: str
    extractor_version: str | None = None
    extraction_notes: str | None = None

    confidence: float = Field(ge=0.0, le=1.0)
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED

    # Annotation/model uncertainty should survive rather than be hidden.
    unresolved_questions: list[str] = Field(default_factory=list)
