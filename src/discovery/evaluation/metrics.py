from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from discovery.problems.schema import ProblemInstance


class SetMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    precision: float
    recall: float
    f1: float


class ProblemExtractionMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_family_accuracy: float
    operations: SetMetrics
    structural_properties: SetMetrics
    mathematical_objects: SetMetrics


def _set_metrics(gold: set[str], predicted: set[str]) -> SetMetrics:
    if not predicted:
        precision = 1.0 if not gold else 0.0
    else:
        precision = len(gold & predicted) / len(predicted)
    recall = 1.0 if not gold else len(gold & predicted) / len(gold)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return SetMetrics(precision=precision, recall=recall, f1=f1)


def evaluate_problem(gold: ProblemInstance, predicted: ProblemInstance) -> ProblemExtractionMetrics:
    gold_math = {f"{item.object_type}:{item.name}".casefold() for item in gold.mathematical_objects}
    pred_math = {
        f"{item.object_type}:{item.name}".casefold() for item in predicted.mathematical_objects
    }
    return ProblemExtractionMetrics(
        task_family_accuracy=1.0 if gold.task_family == predicted.task_family else 0.0,
        operations=_set_metrics(
            {item.casefold() for item in gold.algorithmic_operations},
            {item.casefold() for item in predicted.algorithmic_operations},
        ),
        structural_properties=_set_metrics(
            {item.casefold() for item in gold.structural_properties},
            {item.casefold() for item in predicted.structural_properties},
        ),
        mathematical_objects=_set_metrics(gold_math, pred_math),
    )
