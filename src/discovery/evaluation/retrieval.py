from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field


class RetrievalJudgment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    work_id: str
    relevance: int = Field(ge=0, le=3)


class RetrievalMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    precision_at_k: float = Field(ge=0, le=1)
    recall_at_k: float = Field(ge=0, le=1)
    reciprocal_rank: float = Field(ge=0, le=1)
    ndcg_at_k: float = Field(ge=0, le=1)
    retrieved: int = Field(ge=0)
    relevant_total: int = Field(ge=0)


def evaluate_ranking(
    ranked_work_ids: list[str],
    judgments: list[RetrievalJudgment],
    *,
    k: int = 20,
) -> RetrievalMetrics:
    relevance = {item.work_id: item.relevance for item in judgments}
    relevant_total = sum(1 for value in relevance.values() if value > 0)
    top = ranked_work_ids[:k]
    hits = [relevance.get(work_id, 0) for work_id in top]
    relevant_retrieved = sum(1 for value in hits if value > 0)
    precision = relevant_retrieved / len(top) if top else 0.0
    recall = relevant_retrieved / relevant_total if relevant_total else 0.0
    reciprocal_rank = 0.0
    for rank, value in enumerate(hits, start=1):
        if value > 0:
            reciprocal_rank = 1.0 / rank
            break

    def dcg(values: list[int]) -> float:
        return float(
            sum(
                (2**value - 1) / math.log2(rank + 1)
                for rank, value in enumerate(values, start=1)
            )
        )

    ideal = sorted(relevance.values(), reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    ndcg = dcg(hits) / ideal_dcg if ideal_dcg else 0.0
    return RetrievalMetrics(
        precision_at_k=precision,
        recall_at_k=recall,
        reciprocal_rank=reciprocal_rank,
        ndcg_at_k=ndcg,
        retrieved=len(top),
        relevant_total=relevant_total,
    )
