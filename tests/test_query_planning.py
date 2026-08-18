from discovery.retrieval.models import QueryClause, QueryPlan
from discovery.retrieval.planning import batch_query_plan


def test_query_plan_batches_without_quantum_filtering() -> None:
    plan = QueryPlan(
        id="p",
        name="test",
        clauses=[QueryClause(text=f"term {i}", source="test") for i in range(10)],
        rendered_query="unused",
    )
    batch = batch_query_plan(plan, terms_per_query=4, result_limit=20)
    assert len(batch.queries) == 3
    assert batch.queries[0].limit == 20
    assert all("quantum" not in query.text.casefold() for query in batch.queries)
