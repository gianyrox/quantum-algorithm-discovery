from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MathSimilarityExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left_expression_id: str
    right_expression_id: str
    expected_relation: str
    expected_similar: bool
    discipline_left: str | None = None
    discipline_right: str | None = None
    notes: str | None = None


class MathSimilarityEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(ge=0, le=1)
    accuracy: float = Field(ge=0, le=1)
    precision: float = Field(ge=0, le=1)
    recall: float = Field(ge=0, le=1)
    evaluated: int = Field(ge=0)


def evaluate_scores(
    examples: list[MathSimilarityExample],
    scores: dict[tuple[str, str], float],
    *,
    threshold: float,
) -> MathSimilarityEvaluation:
    tp = fp = tn = fn = 0
    for example in examples:
        score = scores.get((example.left_expression_id, example.right_expression_id), 0.0)
        predicted = score >= threshold
        if predicted and example.expected_similar:
            tp += 1
        elif predicted:
            fp += 1
        elif example.expected_similar:
            fn += 1
        else:
            tn += 1
    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    accuracy = (tp + tn) / total if total else 0.0
    return MathSimilarityEvaluation(
        threshold=threshold,
        accuracy=round(accuracy, 6),
        precision=round(precision, 6),
        recall=round(recall, 6),
        evaluated=total,
    )
