from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from discovery.problems.schema import ProblemInstance
from discovery.quantum.checks import QuantumAdvantageChecklist
from discovery.quantum.matching import baseline_quantum_match
from discovery.quantum.schema import QuantumAlgorithm, QuantumMatch
from discovery.storage.models import QuantumMatchRow, QuantumScreeningRunRow


class QuantumScreeningResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    matches: list[QuantumMatch]
    checklists: dict[str, QuantumAdvantageChecklist] = Field(default_factory=dict)


class QuantumScreeningService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def screen(
        self,
        problems: list[ProblemInstance],
        algorithms: list[QuantumAlgorithm],
    ) -> QuantumScreeningResult:
        run_id = str(uuid4())
        self.session.add(
            QuantumScreeningRunRow(
                id=run_id,
                method="baseline-structural-screen-v0.3",
                created_at=datetime.now(UTC),
                parameters_json={
                    "problem_count": len(problems),
                    "algorithm_count": len(algorithms),
                },
            )
        )
        matches: list[QuantumMatch] = []
        checklists: dict[str, QuantumAdvantageChecklist] = {}
        for problem in problems:
            for algorithm in algorithms:
                match = baseline_quantum_match(problem, algorithm)
                matches.append(match)
                checklist = QuantumAdvantageChecklist(
                    evidence=[
                        "Structural screening does not establish applicability or advantage.",
                        "Unresolved checks must be filled from literature review or experiment.",
                    ]
                )
                checklists[f"{problem.id}:{algorithm.id}"] = checklist
                existing = self.session.query(QuantumMatchRow).filter_by(
                    problem_id=problem.id, algorithm_id=algorithm.id
                ).one_or_none()
                if existing is None:
                    existing = QuantumMatchRow(
                        problem_id=problem.id,
                        algorithm_id=algorithm.id,
                        category=match.category.value,
                        compatibility_score=match.compatibility_score,
                        payload_json=match.model_dump(mode="json"),
                    )
                else:
                    existing.category = match.category.value
                    existing.compatibility_score = match.compatibility_score
                    existing.payload_json = match.model_dump(mode="json")
                self.session.add(existing)
        self.session.flush()
        return QuantumScreeningResult(run_id=run_id, matches=matches, checklists=checklists)
