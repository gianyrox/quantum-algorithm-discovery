from discovery.coverage.feedback import FeedbackAction
from discovery.coverage.saturation import DiscoveryYield
from discovery.documents.schema import DocumentSection, ParsedDocument
from discovery.execution.v010 import analyze_pre_quantum_corpus
from discovery.problems.enums import ExtractionMethod, TaskFamily
from discovery.problems.schema import ProblemInstance


def _problem(identifier: str) -> ProblemInstance:
    return ProblemInstance(
        id=identifier,
        source_work_id=f"w-{identifier}",
        natural_language_statement="Optimize a sparse system",
        task_family=TaskFamily.OPTIMIZATION,
        structural_properties=["sparse"],
        algorithmic_operations=["iteration"],
        extraction_method=ExtractionMethod.HUMAN,
        extractor="test",
        confidence=1.0,
    )


def test_prequantum_pipeline_integrates_discovery_and_feedback() -> None:
    document = ParsedDocument(
        work_id="w-p1",
        asset_id="a",
        source_format="txt",
        parser="test",
        sections=[DocumentSection(id="s", order=0, text="We solve an optimization problem.")],
    )
    result = analyze_pre_quantum_corpus(
        [document],
        [_problem("p1"), _problem("p2")],
        [{"discipline": "physics", "year": 2024, "provider": "openalex"}],
        [{"scope_id": "physics", "coverage_gap": 0.9, "uncertainty": 0.7, "novelty": 0.5}],
        [DiscoveryYield(iteration=1, retrieved=100, new_works=20)],
        strata_stable=False,
    )
    assert result.structure_discovery.problem_count == 2
    assert result.coverage.total_works == 1
    assert result.feedback.action in {FeedbackAction.CONTINUE, FeedbackAction.ADD_PROVIDER}
    assert any("pre-quantum" in note.casefold() for note in result.notes)
