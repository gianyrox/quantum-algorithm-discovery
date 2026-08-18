from __future__ import annotations

import json
from pathlib import Path

import pytest

from discovery.problems.schema import ProblemInstance


@pytest.fixture
def example_problem() -> ProblemInstance:
    payload = json.loads(Path("data/examples/problem.example.json").read_text(encoding="utf-8"))
    return ProblemInstance.model_validate(payload)
