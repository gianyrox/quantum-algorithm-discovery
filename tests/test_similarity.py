from __future__ import annotations

from discovery.analysis.similarity import baseline_problem_similarity
from discovery.discovery.ranking import cross_domain_candidate_score


def test_structural_similarity_is_explicit_baseline(example_problem) -> None:
    evidence = baseline_problem_similarity(example_problem, example_problem)
    assert evidence.task == 1.0
    assert evidence.operator == 1.0
    assert evidence.structural_score() > 0.5
    score = cross_domain_candidate_score(evidence, different_disciplines=True)
    assert 0 <= score <= 1
