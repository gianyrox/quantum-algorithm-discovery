from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.ai.schema import AlgorithmProposal, ProposalEvaluation
from discovery.core.ids import stable_id
from discovery.storage.models import AlgorithmProposalRow, ProposalEvaluationRow


class AlgorithmProposalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, proposal: AlgorithmProposal) -> AlgorithmProposalRow:
        row = self.session.get(AlgorithmProposalRow, proposal.id)
        if row is None:
            row = AlgorithmProposalRow(
                id=proposal.id,
                target_problem_family_id=proposal.target_problem_family_id,
                status=proposal.status,
                title=proposal.title,
                payload_json=proposal.model_dump(mode="json"),
                created_at=datetime.now(UTC),
            )
        else:
            row.status = proposal.status
            row.title = proposal.title
            row.payload_json = proposal.model_dump(mode="json")
        self.session.add(row)
        self.session.flush()
        return row

    def add_evaluation(
        self,
        evaluation: ProposalEvaluation,
        *,
        evaluator: str,
    ) -> ProposalEvaluationRow:
        evaluation_id = stable_id(
            "proposal-evaluation",
            f"{evaluation.proposal_id}:{evaluator}:{evaluation.model_dump_json()}",
        )
        row = ProposalEvaluationRow(
            id=evaluation_id,
            proposal_id=evaluation.proposal_id,
            evaluator=evaluator,
            payload_json=evaluation.model_dump(mode="json"),
            created_at=datetime.now(UTC),
        )
        self.session.merge(row)
        self.session.flush()
        return row

    def list_for_family(self, family_id: str) -> list[AlgorithmProposal]:
        rows = self.session.scalars(
            select(AlgorithmProposalRow)
            .where(AlgorithmProposalRow.target_problem_family_id == family_id)
            .order_by(AlgorithmProposalRow.created_at)
        )
        return [AlgorithmProposal.model_validate(row.payload_json) for row in rows]
