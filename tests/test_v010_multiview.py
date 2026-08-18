from discovery.analysis.cross_domain import rank_cross_domain_candidates
from discovery.analysis.discovery_loop import discover_structure
from discovery.analysis.multiview import compare_problems
from discovery.problems.enums import ExtractionMethod, TaskFamily
from discovery.problems.schema import MathematicalObject, ProblemInstance


def problem(identifier: str, statement: str, operator: str) -> ProblemInstance:
    return ProblemInstance(
        id=identifier,
        source_work_id=f"w-{identifier}",
        natural_language_statement=statement,
        task_family=TaskFamily.OPTIMIZATION,
        mathematical_objects=[MathematicalObject(name="matrix", object_type="matrix")],
        operators=[operator],
        algorithmic_operations=["iteration"],
        structural_properties=["sparse"],
        extraction_method=ExtractionMethod.HUMAN,
        extractor="test",
        confidence=1.0,
    )


def test_multiview_similarity_and_discovery() -> None:
    left = problem("p1", "Minimize lattice energy", "matrix multiply")
    right = problem("p2", "Find a low cost ecological allocation", "matrix multiply")
    similarity = compare_problems(left, right)
    assert similarity.structural_score > 0.4
    result = discover_structure([left, right])
    assert result.pair_count == 1
    assert len(result.families) == 1


def test_cross_domain_ranking_requires_different_disciplines() -> None:
    left = problem("p1", "Minimize lattice energy", "matrix multiply")
    right = problem("p2", "Find ecological optimum", "matrix multiply")
    similarity = compare_problems(left, right)
    candidates = rank_cross_domain_candidates(
        [similarity], {"p1": "physics", "p2": "ecology"}, minimum_score=0.1
    )
    assert len(candidates) == 1
    assert candidates[0].discipline_a == "physics"
