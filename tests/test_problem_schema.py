import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from discovery.problems.schema import ProblemInstance


def test_example_problem_validates() -> None:
    path = Path("data/examples/problem.example.json")
    payload = json.loads(path.read_text(encoding="utf-8"))

    problem = ProblemInstance.model_validate(payload)

    assert problem.id == "problem-example-001"
    assert problem.task_family.value == "eigenproblem"
    assert problem.confidence == 1.0


def test_confidence_cannot_exceed_one() -> None:
    path = Path("data/examples/problem.example.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["confidence"] = 1.5

    with pytest.raises(ValidationError):
        ProblemInstance.model_validate(payload)


def test_unknown_fields_are_rejected() -> None:
    path = Path("data/examples/problem.example.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["magic_untracked_field"] = True

    with pytest.raises(ValidationError):
        ProblemInstance.model_validate(payload)


def test_problem_repository_normalizes_evidence_math_and_methods(tmp_path) -> None:
    from discovery.core.evidence import Evidence
    from discovery.problems.enums import EvidenceKind, ExtractionMethod, TaskFamily
    from discovery.problems.schema import MathematicalObject, ScientificMethod
    from discovery.storage.database import (
        create_database_engine,
        init_db,
        make_session_factory,
        session_scope,
    )
    from discovery.storage.models import ProblemEvidenceRow, ProblemMathRow, ProblemMethodRow
    from discovery.storage.repositories import ProblemRepository

    engine = create_database_engine(f"sqlite:///{tmp_path / 'problem-normalized.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    problem = ProblemInstance(
        id="normalized-problem",
        source_work_id="work-1",
        natural_language_statement="Solve a sparse linear system.",
        task_family=TaskFamily.LINEAR_SYSTEM,
        mathematical_objects=[MathematicalObject(name="A", object_type="matrix")],
        known_methods=[ScientificMethod(name="CG", method_type="iterative")],
        evidence=[Evidence(kind=EvidenceKind.OTHER, source_identifier="source")],
        extraction_method=ExtractionMethod.HUMAN,
        extractor="test",
        confidence=1.0,
    )
    with session_scope(factory) as session:
        repository = ProblemRepository(session)
        repository.upsert(problem)
        repository.upsert(problem)
        assert session.query(ProblemEvidenceRow).count() == 1
        assert session.query(ProblemMathRow).count() == 1
        assert session.query(ProblemMethodRow).count() == 1
