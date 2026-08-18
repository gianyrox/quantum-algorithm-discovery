from __future__ import annotations

import math
import re
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.documents.schema import ParsedDocument
from discovery.documents.text import document_text
from discovery.storage.models import TermRow, UnknownVocabularyCandidateRow

_STOP = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "were", "into",
    "using", "used", "use", "our", "their", "these", "those", "has", "have", "had", "not",
    "can", "may", "than", "such", "between", "through", "over", "under", "results", "method",
}


class UnknownVocabularyCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    term: str
    frequency: int = Field(ge=1)
    document_frequency: int = Field(ge=1)
    score: float = Field(ge=0)
    corpus_scope: str = "default"


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()


def _phrases(text: str, max_ngram: int) -> list[str]:
    tokens = [
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)
        if token.casefold() not in _STOP
    ]
    phrases: list[str] = []
    for size in range(1, max_ngram + 1):
        phrases.extend(
            " ".join(tokens[index : index + size])
            for index in range(len(tokens) - size + 1)
        )
    return phrases


class UnknownVocabularyMiner:
    """Corpus language minus known ontology language.

    This is a discovery queue, not an automatic ontology mutation mechanism.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def mine(
        self,
        documents: list[ParsedDocument],
        *,
        corpus_scope: str = "default",
        max_ngram: int = 3,
        minimum_document_frequency: int = 2,
        limit: int = 500,
    ) -> list[UnknownVocabularyCandidate]:
        known = {
            _normalize(term)
            for term in self.session.scalars(select(TermRow.term))
            if term.strip()
        }
        frequency: Counter[str] = Counter()
        document_frequency: Counter[str] = Counter()
        for document in documents:
            phrases = _phrases(document_text(document), max_ngram)
            frequency.update(phrases)
            document_frequency.update(set(phrases))
        candidates: list[UnknownVocabularyCandidate] = []
        total_docs = max(1, len(documents))
        for term, df in document_frequency.items():
            if df < minimum_document_frequency or term in known:
                continue
            tf = frequency[term]
            specificity = 1.0 + 0.25 * (term.count(" "))
            idf_like = math.log1p(total_docs / df)
            score = round(tf * specificity * idf_like, 6)
            candidate = UnknownVocabularyCandidate(
                id=stable_id("unknown-vocabulary", f"{corpus_scope}:{term}"),
                term=term,
                frequency=tf,
                document_frequency=df,
                score=score,
                corpus_scope=corpus_scope,
            )
            candidates.append(candidate)
        candidates.sort(key=lambda item: (-item.score, -item.document_frequency, item.term))
        selected = candidates[:limit]
        for item in selected:
            row = self.session.get(UnknownVocabularyCandidateRow, item.id)
            if row is None:
                row = UnknownVocabularyCandidateRow(
                    id=item.id,
                    term=item.term,
                    normalized_term=_normalize(item.term),
                    corpus_scope=corpus_scope,
                    frequency=item.frequency,
                    document_frequency=item.document_frequency,
                    score=item.score,
                    evidence_json={},
                )
            else:
                row.frequency = item.frequency
                row.document_frequency = item.document_frequency
                row.score = item.score
            self.session.add(row)
        self.session.flush()
        return selected
