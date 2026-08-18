from discovery.problems.enums import ExtractionMethod, TaskFamily
from discovery.problems.evidence import EvidenceSpan
from discovery.problems.quality import assess_problem_quality
from discovery.problems.schema import MathematicalObject, ProblemInstance


def test_problem_quality_keeps_missing_fields_visible() -> None:
    problem = ProblemInstance(
        id="p1",
        source_work_id="w1",
        natural_language_statement="Minimize the energy.",
        task_family=TaskFamily.OPTIMIZATION,
        objective="minimize energy",
        inputs=["configuration"],
        outputs=["minimum-energy configuration"],
        mathematical_objects=[MathematicalObject(name="energy", object_type="objective")],
        algorithmic_operations=["objective evaluation"],
        evidence_spans=[
            EvidenceSpan(field="objective", text="minimize energy", confidence=0.9),
            EvidenceSpan(field="inputs", text="configuration", confidence=0.8),
        ],
        extraction_method=ExtractionMethod.HUMAN,
        extractor="test",
        confidence=0.9,
    )
    report = assess_problem_quality(problem)
    assert report.completeness > 0.4
    assert report.evidence_coverage > 0.0
    assert "access_model" in report.missing_high_value_fields
