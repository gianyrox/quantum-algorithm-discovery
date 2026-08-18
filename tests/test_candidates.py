from discovery.analysis.candidates import generate_cross_domain_candidates
from discovery.analysis.similarity import SimilarityEvidence
from discovery.problems.enums import ExtractionMethod, TaskFamily
from discovery.problems.schema import ProblemInstance


def _problem(problem_id: str, work_id: str) -> ProblemInstance:
    return ProblemInstance(
        id=problem_id,
        source_work_id=work_id,
        natural_language_statement="Solve the dominant spectral mode.",
        task_family=TaskFamily.EIGENPROBLEM,
        operators=["matrix multiplication"],
        structural_properties=["sparse"],
        extraction_method=ExtractionMethod.HUMAN,
        extractor="human",
        confidence=1.0,
    )


def test_cross_domain_candidate_requires_different_fields() -> None:
    problems = {"a": _problem("a", "wa"), "b": _problem("b", "wb")}
    evidence = SimilarityEvidence(
        task=1, operator=1, topology=1, lexical=0.1, citation_connectivity=0
    )
    candidates = generate_cross_domain_candidates(
        problems,
        {("a", "b"): evidence},
        {"a": "ecology", "b": "physics"},
    )
    assert len(candidates) == 1
    assert candidates[0].field_a != candidates[0].field_b
