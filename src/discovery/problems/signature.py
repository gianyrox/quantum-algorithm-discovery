from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.problems.schema import ProblemInstance


class ProblemSignature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: str
    task_family: str
    mathematical_objects: list[str] = Field(default_factory=list)
    operators: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    structures: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    access_model: str | None = None
    stochasticity: str | None = None


def problem_signature(problem: ProblemInstance) -> ProblemSignature:
    return ProblemSignature(
        problem_id=problem.id,
        task_family=problem.task_family.value,
        mathematical_objects=sorted(
            {f"{item.object_type}:{item.name}".casefold() for item in problem.mathematical_objects}
        ),
        operators=sorted({item.casefold() for item in problem.operators}),
        operations=sorted({item.casefold() for item in problem.algorithmic_operations}),
        constraints=sorted({item.casefold() for item in problem.constraints}),
        structures=sorted({item.casefold() for item in problem.structural_properties}),
        methods=sorted({item.name.casefold() for item in problem.known_methods}),
        access_model=problem.access_model.casefold() if problem.access_model else None,
        stochasticity=problem.stochasticity.casefold() if problem.stochasticity else None,
    )
