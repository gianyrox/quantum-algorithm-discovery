from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from discovery.ontology.gaps import UnknownVocabularyCandidate


class VocabularyFeedbackStatus(StrEnum):
    CANDIDATE = "candidate"
    ACCEPT_RETRIEVAL_TERM = "accept_retrieval_term"
    MAP_EXISTING_CONCEPT = "map_existing_concept"
    NEW_CONCEPT_CANDIDATE = "new_concept_candidate"
    REJECT_AMBIGUOUS = "reject_ambiguous"
    REJECT_NOISE = "reject_noise"


class VocabularyFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    term: str
    status: VocabularyFeedbackStatus = VocabularyFeedbackStatus.CANDIDATE
    concept_id: str | None = None
    reviewer: str | None = None
    rationale: str | None = None
    retrieval_only: bool = True


def make_feedback(candidate: UnknownVocabularyCandidate) -> VocabularyFeedback:
    return VocabularyFeedback(candidate_id=candidate.id, term=candidate.term)
