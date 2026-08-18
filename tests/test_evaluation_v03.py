from discovery.evaluation.agreement import pairwise_agreement
from discovery.evaluation.completeness import problem_completeness
from discovery.evaluation.retrieval import RetrievalJudgment, evaluate_ranking


def test_retrieval_metrics(example_problem) -> None:
    metrics = evaluate_ranking(
        ["a", "b", "c"],
        [RetrievalJudgment(query_id="q", work_id="b", relevance=3)],
        k=3,
    )
    assert metrics.recall_at_k == 1.0
    assert metrics.reciprocal_rank == 0.5


def test_problem_completeness_and_agreement(example_problem) -> None:
    completeness = problem_completeness(example_problem)
    assert 0 <= completeness.score <= 1
    agreement = pairwise_agreement(example_problem, example_problem)
    assert agreement.task_family_agreement == 1
    assert agreement.operation_jaccard == 1
