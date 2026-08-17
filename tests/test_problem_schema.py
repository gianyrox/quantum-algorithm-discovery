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
