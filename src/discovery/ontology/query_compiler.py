from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.retrieval.models import QueryClause, QueryPlan
from discovery.storage.models import ConceptRow, TermRow

_TERM_PRIORITY = {
    "canonical": 1.5,
    "preferred": 1.5,
    "synonym": 1.4,
    "historical": 1.3,
    "abbreviation": 1.25,
    "search_phrase": 1.2,
    "narrower": 0.9,
    "broader": 0.7,
    "related": 0.5,
}


def _quote(term: str) -> str:
    cleaned = re.sub(r"\s+", " ", term.strip()).replace('"', "")
    if " " in cleaned or any(ch in cleaned for ch in "()[]{}"):
        return f'"{cleaned}"'
    return cleaned


class OntologyQueryCompiler:
    """Compile seed/native terminology into transparent high-recall lexical plans."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def compile_concept(self, concept_id: str, *, max_terms: int = 24) -> QueryPlan:
        concept = self.session.get(ConceptRow, concept_id)
        if concept is None:
            raise KeyError(f"unknown concept: {concept_id}")
        terms = list(
            self.session.scalars(
                select(TermRow).where(TermRow.concept_id == concept_id).order_by(TermRow.id)
            )
        )
        candidates: list[QueryClause] = [
            QueryClause(
                text=concept.canonical_concept,
                source="concept.canonical_concept",
                concept_id=concept_id,
                term_type="canonical",
                weight=_TERM_PRIORITY["canonical"],
            )
        ]
        seen = {concept.canonical_concept.casefold()}
        for term in terms:
            key = term.term.casefold().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            candidates.append(
                QueryClause(
                    text=term.term,
                    source="term",
                    concept_id=concept_id,
                    term_type=term.term_type,
                    weight=_TERM_PRIORITY.get(term.term_type, 0.8),
                )
            )
        candidates.sort(key=lambda item: (-item.weight, item.text.casefold()))
        selected = candidates[:max_terms]
        rendered = " OR ".join(_quote(item.text) for item in selected)
        return QueryPlan(
            id=stable_id("query-plan", f"concept:{concept_id}:{rendered}"),
            name=f"concept:{concept_id}",
            clauses=selected,
            rendered_query=rendered,
            concept_ids=[concept_id],
            discipline_ids=[concept.discipline_id] if concept.discipline_id else [],
            notes=[
                "Lexical high-recall plan compiled without quantum-relevance filtering.",
                "Seed terms retain scaffold status; native vocabulary releases should "
                "supersede/enrich them.",
            ],
        )
