from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.problems.schema import ProblemInstance


class SimilarityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lexical: float = Field(default=0.0, ge=0, le=1)
    semantic: float = Field(default=0.0, ge=0, le=1)
    task: float = Field(default=0.0, ge=0, le=1)
    mathematical: float = Field(default=0.0, ge=0, le=1)
    operator: float = Field(default=0.0, ge=0, le=1)
    constraint: float = Field(default=0.0, ge=0, le=1)
    topology: float = Field(default=0.0, ge=0, le=1)
    stochastic: float = Field(default=0.0, ge=0, le=1)
    complexity: float = Field(default=0.0, ge=0, le=1)
    method: float = Field(default=0.0, ge=0, le=1)
    citation_connectivity: float = Field(default=0.0, ge=0, le=1)
    notes: list[str] = Field(default_factory=list)

    def structural_score(self) -> float:
        weighted = (
            0.18 * self.task
            + 0.22 * self.mathematical
            + 0.18 * self.operator
            + 0.12 * self.constraint
            + 0.08 * self.topology
            + 0.08 * self.stochastic
            + 0.08 * self.complexity
            + 0.06 * self.method
        )
        return round(weighted, 6)


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def baseline_problem_similarity(a: ProblemInstance, b: ProblemInstance) -> SimilarityEvidence:
    math_a = {f"{obj.object_type}:{obj.name}".casefold() for obj in a.mathematical_objects}
    math_b = {f"{obj.object_type}:{obj.name}".casefold() for obj in b.mathematical_objects}
    operators_a = {item.casefold() for item in a.operators + a.algorithmic_operations}
    operators_b = {item.casefold() for item in b.operators + b.algorithmic_operations}
    constraints_a = {item.casefold() for item in a.constraints}
    constraints_b = {item.casefold() for item in b.constraints}
    methods_a = {item.name.casefold() for item in a.known_methods}
    methods_b = {item.name.casefold() for item in b.known_methods}
    structures_a = {item.casefold() for item in a.structural_properties}
    structures_b = {item.casefold() for item in b.structural_properties}

    stochastic = 0.0
    if a.stochasticity and b.stochasticity:
        stochastic = 1.0 if a.stochasticity.casefold() == b.stochasticity.casefold() else 0.0

    return SimilarityEvidence(
        task=1.0 if a.task_family == b.task_family else 0.0,
        mathematical=jaccard(math_a, math_b),
        operator=jaccard(operators_a, operators_b),
        constraint=jaccard(constraints_a, constraints_b),
        topology=jaccard(structures_a, structures_b),
        stochastic=stochastic,
        method=jaccard(methods_a, methods_b),
        notes=["Transparent set-overlap baseline; not a semantic-equivalence claim."],
    )
