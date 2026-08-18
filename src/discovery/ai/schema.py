from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AlgorithmProposal(BaseModel):
    """A hypothesis generated for evaluation, never a validated algorithm by construction."""

    model_config = ConfigDict(extra="forbid")

    id: str
    target_problem_family_id: str
    title: str
    hypothesis: str
    proposed_primitives: list[str] = Field(default_factory=list)
    construction_steps: list[str] = Field(default_factory=list)
    required_assumptions: list[str] = Field(default_factory=list)
    access_model: str | None = None
    predicted_complexity: str | None = None
    classical_baseline: str | None = None
    possible_advantage: str | None = None
    likely_failure_modes: list[str] = Field(default_factory=list)
    dequantization_checks: list[str] = Field(default_factory=list)
    proof_obligations: list[str] = Field(default_factory=list)
    status: str = "hypothesis"


class ProposalEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    representational_validity: str = "unresolved"
    complexity_validity: str = "unresolved"
    classical_baseline_result: str = "unresolved"
    dequantization_result: str = "unresolved"
    simulation_result: str = "unresolved"
    proof_status: str = "unresolved"
    conclusions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
