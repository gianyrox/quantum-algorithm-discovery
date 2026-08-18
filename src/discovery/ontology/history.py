from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HistoricalTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    term: str
    vocabulary: str
    source_release: str
    valid_from: str | None = None
    valid_until: str | None = None
    introduced_in: str | None = None
    deprecated_in: str | None = None
    superseded_by: list[str] = Field(default_factory=list)
    predecessor: list[str] = Field(default_factory=list)
    successor: list[str] = Field(default_factory=list)
    historical_aliases: list[str] = Field(default_factory=list)


class HistoricalVocabularyIndex:
    """Release-aware retrieval helper; successor does not imply equivalence."""

    def __init__(self, terms: list[HistoricalTerm]) -> None:
        self.terms = list(terms)
        self._by_release: dict[tuple[str, str], list[HistoricalTerm]] = {}
        for item in self.terms:
            self._by_release.setdefault((item.vocabulary, item.source_release), []).append(item)

    def releases(self, vocabulary: str) -> list[str]:
        return sorted({item.source_release for item in self.terms if item.vocabulary == vocabulary})

    def search(self, query: str, *, vocabulary: str | None = None) -> list[HistoricalTerm]:
        needle = query.casefold()
        result = []
        for item in self.terms:
            if vocabulary is not None and item.vocabulary != vocabulary:
                continue
            forms = [item.term, *item.historical_aliases]
            if any(needle in form.casefold() for form in forms):
                result.append(item)
        return sorted(result, key=lambda item: (item.vocabulary, item.source_release, item.term))

    def release(self, vocabulary: str, source_release: str) -> list[HistoricalTerm]:
        return list(self._by_release.get((vocabulary, source_release), []))
