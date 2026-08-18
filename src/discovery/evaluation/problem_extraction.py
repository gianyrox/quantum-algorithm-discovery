from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.problems.schema import ProblemInstance


class ExtractionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_family_accuracy: float = Field(ge=0, le=1)
    problem_count_error: int
    operation_precision: float = Field(ge=0, le=1)
    operation_recall: float = Field(ge=0, le=1)
    structure_precision: float = Field(ge=0, le=1)
    structure_recall: float = Field(ge=0, le=1)


def _pr(predicted: set[str], expected: set[str]) -> tuple[float, float]:
    if not predicted:
        precision = 1.0 if not expected else 0.0
    else:
        precision = len(predicted & expected) / len(predicted)
    recall = 1.0 if not expected else len(predicted & expected) / len(expected)
    return precision, recall


def evaluate_problem_pair(
    predicted: ProblemInstance, expected: ProblemInstance
) -> ExtractionEvaluation:
    pred_ops = {item.casefold() for item in predicted.algorithmic_operations}
    exp_ops = {item.casefold() for item in expected.algorithmic_operations}
    pred_struct = {item.casefold() for item in predicted.structural_properties}
    exp_struct = {item.casefold() for item in expected.structural_properties}
    op_p, op_r = _pr(pred_ops, exp_ops)
    st_p, st_r = _pr(pred_struct, exp_struct)
    return ExtractionEvaluation(
        task_family_accuracy=float(predicted.task_family == expected.task_family),
        problem_count_error=0,
        operation_precision=round(op_p, 6),
        operation_recall=round(op_r, 6),
        structure_precision=round(st_p, 6),
        structure_recall=round(st_r, 6),
    )
