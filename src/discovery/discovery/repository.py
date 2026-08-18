from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.discovery.schema import CrossDomainCandidate
from discovery.problems.family import ProblemFamily
from discovery.storage.models import (
    CandidateEvidenceRow,
    CandidateRow,
    ProblemFamilyMemberRow,
    ProblemFamilyRow,
)


class DiscoveryRepository:
    """Persistence for hypothesis-level discovery objects.

    Candidate and family records remain hypotheses. Persisting them does not
    promote them to validated equivalences or scientific findings.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_candidate(self, candidate: CrossDomainCandidate) -> CandidateRow:
        row = self.session.get(CandidateRow, candidate.id)
        payload = candidate.model_dump(mode="json")
        if row is None:
            row = CandidateRow(
                id=candidate.id,
                candidate_type="cross_domain_problem_pair",
                title=f"{candidate.problem_a_id} ↔ {candidate.problem_b_id}",
                status=candidate.review_status,
                score=candidate.candidate_score,
                payload_json=payload,
            )
        else:
            row.status = candidate.review_status
            row.score = candidate.candidate_score
            row.payload_json = payload
        self.session.add(row)
        self.session.flush()

        existing = list(
            self.session.scalars(
                select(CandidateEvidenceRow).where(
                    CandidateEvidenceRow.candidate_id == candidate.id
                )
            )
        )
        existing_values = {
            str(item.evidence_json.get("text", "")) for item in existing
        }
        for evidence in candidate.evidence:
            if evidence in existing_values:
                continue
            self.session.add(
                CandidateEvidenceRow(
                    candidate_id=candidate.id,
                    evidence_type="generation_note",
                    evidence_json={"text": evidence},
                )
            )
        self.session.flush()
        return row

    def upsert_family(self, family: ProblemFamily) -> ProblemFamilyRow:
        row = self.session.get(ProblemFamilyRow, family.id)
        payload = family.model_dump(mode="json")
        if row is None:
            row = ProblemFamilyRow(
                id=family.id,
                name=family.name,
                description=family.description,
                status=family.status,
                payload_json=payload,
            )
        else:
            row.name = family.name
            row.description = family.description
            row.status = family.status
            row.payload_json = payload
        self.session.add(row)
        self.session.flush()

        for problem_id in family.problem_ids:
            member = self.session.scalar(
                select(ProblemFamilyMemberRow).where(
                    ProblemFamilyMemberRow.family_id == family.id,
                    ProblemFamilyMemberRow.problem_id == problem_id,
                )
            )
            if member is None:
                self.session.add(
                    ProblemFamilyMemberRow(
                        family_id=family.id,
                        problem_id=problem_id,
                        membership_score=None,
                        evidence_json={"status": "candidate"},
                    )
                )
        self.session.flush()
        return row
