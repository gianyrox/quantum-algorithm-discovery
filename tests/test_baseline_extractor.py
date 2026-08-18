from discovery.documents.parsers import PlainTextParser
from discovery.problems.baseline_extractor import TransparentBaselineProblemExtractor
from discovery.problems.enums import TaskFamily


def test_baseline_extractor_is_low_confidence_and_transparent() -> None:
    document = PlainTextParser().parse(
        work_id="w",
        asset_id="a",
        content=(
            b"We estimate an eigenvalue of a sparse matrix using repeated "
            b"matrix-vector operations."
        ),
    )
    problems = TransparentBaselineProblemExtractor().extract(document)
    assert problems
    assert any(problem.task_family == TaskFamily.EIGENPROBLEM for problem in problems)
    assert all(problem.confidence <= 0.55 for problem in problems)
    assert all(problem.unresolved_questions for problem in problems)
