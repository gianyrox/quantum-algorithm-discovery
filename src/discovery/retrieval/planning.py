from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from discovery.core.ids import stable_id
from discovery.retrieval.models import QueryClause, QueryPlan, SearchQuery


class QueryBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    plan_id: str
    queries: list[SearchQuery]
    rationale: list[str] = Field(default_factory=list)


def _render(clauses: list[QueryClause]) -> str:
    rendered: list[str] = []
    for clause in clauses:
        text = clause.text.strip().replace('"', "")
        rendered.append(f'"{text}"' if " " in text else text)
    return " OR ".join(rendered)


def batch_query_plan(
    plan: QueryPlan,
    *,
    terms_per_query: int = 8,
    result_limit: int = 50,
    providers: list[str] | None = None,
    max_cost_usd: float | None = None,
) -> QueryBatch:
    """Split a transparent high-recall plan into bounded provider queries.

    Multiple smaller queries are easier to replay and audit than one huge OR
    expression, and avoid provider-specific query-length limits.
    """
    if terms_per_query < 1:
        raise ValueError("terms_per_query must be positive")
    queries: list[SearchQuery] = []
    for start in range(0, len(plan.clauses), terms_per_query):
        clauses = plan.clauses[start : start + terms_per_query]
        queries.append(
            SearchQuery(
                text=_render(clauses),
                limit=result_limit,
                providers=providers or [],
                max_cost_usd=max_cost_usd,
                filters={"query_plan_id": plan.id, "batch_offset": start},
            )
        )
    signature = "|".join(query.text for query in queries)
    return QueryBatch(
        id=stable_id("query-batch", f"{plan.id}:{signature}"),
        plan_id=plan.id,
        queries=queries,
        rationale=[
            "Queries are split for provider portability and reproducible high-recall retrieval.",
            "No quantum relevance filter is applied during scientific corpus retrieval.",
        ],
    )
