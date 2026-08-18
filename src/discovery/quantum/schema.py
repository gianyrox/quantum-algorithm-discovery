from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QuantumOpportunityCategory(StrEnum):
    ESTABLISHED = "A_established"
    DOMAIN_TRANSFER = "B_domain_transfer"
    STRUCTURAL_EXTENSION = "C_structural_extension"
    ALGORITHMIC_GAP = "D_algorithmic_gap"
    NEGATIVE = "E_negative"
    UNRESOLVED = "U_unresolved"


class QuantumPrimitive(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    family: str
    input_models: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    required_structures: list[str] = Field(default_factory=list)
    resource_notes: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class QuantumAlgorithm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    family: str
    problem_classes: list[str] = Field(default_factory=list)
    input_model: str | None = None
    access_model: str | None = None
    output: str | None = None
    primitive_ids: list[str] = Field(default_factory=list)
    required_structures: list[str] = Field(default_factory=list)
    complexity: str | None = None
    query_complexity: str | None = None
    gate_complexity: str | None = None
    state_preparation: str | None = None
    data_loading: str | None = None
    readout: str | None = None
    resource_requirements: list[str] = Field(default_factory=list)
    classical_baselines: list[str] = Field(default_factory=list)
    advantage_claim: str | None = None
    proof_status: str | None = None
    hardware_assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    dequantizations: list[str] = Field(default_factory=list)
    no_go_results: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class QuantumMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: str
    algorithm_id: str
    category: QuantumOpportunityCategory = QuantumOpportunityCategory.UNRESOLVED
    representational_compatibility: float = Field(ge=0, le=1)
    access_model_compatibility: float = Field(ge=0, le=1)
    structural_compatibility: float = Field(ge=0, le=1)
    classical_baseline_strength: float | None = Field(default=None, ge=0, le=1)
    dequantization_risk: float | None = Field(default=None, ge=0, le=1)
    end_to_end_feasibility: float | None = Field(default=None, ge=0, le=1)
    notes: list[str] = Field(default_factory=list)

    @property
    def compatibility_score(self) -> float:
        return round(
            0.35 * self.representational_compatibility
            + 0.30 * self.access_model_compatibility
            + 0.35 * self.structural_compatibility,
            6,
        )
