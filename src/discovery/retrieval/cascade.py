from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RetrievalStage(StrEnum):
    CONTROLLED_VOCABULARY = "controlled_vocabulary"
    LEXICAL = "lexical"
    HISTORICAL_TERMS = "historical_terms"
    CITATION_EXPANSION = "citation_expansion"
    SEMANTIC = "semantic"
    RELATED_WORKS = "related_works"


class RetrievalCascadeStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: RetrievalStage
    enabled: bool = True
    maximum_requests: int = Field(default=10, ge=0)
    reason: str


class RetrievalCascade(BaseModel):
    model_config = ConfigDict(extra="forbid")

    steps: list[RetrievalCascadeStep] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def default_high_recall_cascade() -> RetrievalCascade:
    return RetrievalCascade(
        steps=[
            RetrievalCascadeStep(
                stage=RetrievalStage.CONTROLLED_VOCABULARY,
                maximum_requests=20,
                reason="field-native canonical terms and published vocabulary structure",
            ),
            RetrievalCascadeStep(
                stage=RetrievalStage.LEXICAL,
                maximum_requests=20,
                reason="synonyms, abbreviations, model/method names, and disambiguated terms",
            ),
            RetrievalCascadeStep(
                stage=RetrievalStage.HISTORICAL_TERMS,
                maximum_requests=10,
                reason="recover literature indexed under superseded terminology",
            ),
            RetrievalCascadeStep(
                stage=RetrievalStage.CITATION_EXPANSION,
                maximum_requests=25,
                reason="recover lexically dissimilar works through explicit scholarly edges",
            ),
            RetrievalCascadeStep(
                stage=RetrievalStage.SEMANTIC,
                maximum_requests=15,
                reason="additional recall view; never replaces field-native lexical retrieval",
            ),
            RetrievalCascadeStep(
                stage=RetrievalStage.RELATED_WORKS,
                maximum_requests=10,
                reason="provider-published related-work signals as a final recall channel",
            ),
        ],
        notes=[
            "No quantum relevance filter is applied.",
            (
                "Stopping is governed by audited marginal novelty and coverage, "
                "not a fixed paper count."
            ),
        ],
    )
