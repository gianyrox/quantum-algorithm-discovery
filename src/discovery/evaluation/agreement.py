from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.problems.schema import ProblemInstance


class AnnotationAgreement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_family_agreement: float = Field(ge=0, le=1)
    operation_jaccard: float = Field(ge=0, le=1)
    structure_jaccard: float = Field(ge=0, le=1)


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def pairwise_agreement(left: ProblemInstance, right: ProblemInstance) -> AnnotationAgreement:
    return AnnotationAgreement(
        task_family_agreement=1.0 if left.task_family == right.task_family else 0.0,
        operation_jaccard=_jaccard(
            {item.casefold() for item in left.algorithmic_operations},
            {item.casefold() for item in right.algorithmic_operations},
        ),
        structure_jaccard=_jaccard(
            {item.casefold() for item in left.structural_properties},
            {item.casefold() for item in right.structural_properties},
        ),
    )
