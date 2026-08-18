from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.problems.schema import ProblemInstance


class ProblemCompleteness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: str
    filled_fields: int = Field(ge=0)
    expected_fields: int = Field(ge=1)
    score: float = Field(ge=0, le=1)
    missing_high_value_fields: list[str] = Field(default_factory=list)


def problem_completeness(problem: ProblemInstance) -> ProblemCompleteness:
    fields: dict[str, object] = {
        "inputs": problem.inputs,
        "outputs": problem.outputs,
        "objective": problem.objective,
        "constraints": problem.constraints,
        "state_space": problem.state_space,
        "access_model": problem.access_model,
        "data_model": problem.data_model,
        "mathematical_objects": problem.mathematical_objects,
        "operators": problem.operators,
        "algorithmic_operations": problem.algorithmic_operations,
        "known_methods": problem.known_methods,
        "classical_baselines": problem.classical_baselines,
        "scale_parameters": problem.scale_parameters,
        "reported_bottlenecks": problem.reported_bottlenecks,
        "assumptions": problem.assumptions,
        "evidence": problem.evidence,
    }
    filled = sum(bool(value) for value in fields.values())
    missing = [name for name, value in fields.items() if not value]
    return ProblemCompleteness(
        problem_id=problem.id,
        filled_fields=filled,
        expected_fields=len(fields),
        score=filled / len(fields),
        missing_high_value_fields=missing,
    )
