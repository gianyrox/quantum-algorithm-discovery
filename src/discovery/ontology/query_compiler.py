from __future__ import annotations

import re
from collections import deque
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from discovery.core.ids import stable_id
from discovery.retrieval.models import QueryClause, QueryPlan
from discovery.storage.models import ConceptRelationRow, ConceptRow, DisciplineRow, TermRow

_TERM_PRIORITY = {
    "canonical": 1.5,
    "preferred": 1.5,
    "synonym": 1.4,
    "historical": 1.3,
    "abbreviation": 1.25,
    "search_phrase": 1.0,
    "narrower": 0.9,
    "broader": 0.7,
    "related": 0.5,
}


class QueryMode(StrEnum):
    PRECISION = "precision"
    BALANCED = "balanced"
    HIGH_RECALL = "high_recall"


class QueryCompilerPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: QueryMode = QueryMode.HIGH_RECALL
    max_terms_per_concept: int = Field(default=24, ge=1, le=200)
    include_historical: bool = True
    include_related_concepts: bool = False
    related_relationships: list[str] = Field(
        default_factory=lambda: ["broader", "narrower", "related"]
    )
    max_related_concepts: int = Field(default=8, ge=0, le=100)


def _quote(term: str) -> str:
    cleaned = re.sub(r"\s+", " ", term.strip()).replace('"', "")
    if " " in cleaned or any(ch in cleaned for ch in "()[]{}"):
        return f'"{cleaned}"'
    return cleaned


class OntologyQueryCompiler:
    """Compile field-native terminology into transparent lexical retrieval plans.

    Quantum relevance is deliberately absent from this layer. Every clause keeps
    its source concept and term type so later retrieval evaluation can determine
    which vocabulary expansions improved or harmed recall.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def compile_concept(
        self,
        concept_id: str,
        *,
        max_terms: int = 24,
        policy: QueryCompilerPolicy | None = None,
    ) -> QueryPlan:
        resolved = policy or QueryCompilerPolicy(max_terms_per_concept=max_terms)
        return self.compile_concepts([concept_id], name=f"concept:{concept_id}", policy=resolved)

    def compile_concepts(
        self,
        concept_ids: list[str],
        *,
        name: str = "concept-set",
        policy: QueryCompilerPolicy | None = None,
    ) -> QueryPlan:
        resolved = policy or QueryCompilerPolicy()
        expanded_ids = list(dict.fromkeys(concept_ids))
        if resolved.include_related_concepts:
            expanded_ids.extend(self._related_concepts(expanded_ids, resolved))
            expanded_ids = list(dict.fromkeys(expanded_ids))

        clauses: list[QueryClause] = []
        discipline_ids: list[str] = []
        for concept_id in expanded_ids:
            concept = self.session.get(ConceptRow, concept_id)
            if concept is None:
                if concept_id in concept_ids:
                    raise KeyError(f"unknown concept: {concept_id}")
                continue
            if concept.discipline_id:
                discipline_ids.append(concept.discipline_id)
            clauses.extend(self._concept_clauses(concept, resolved))

        deduplicated: dict[str, QueryClause] = {}
        for clause in clauses:
            key = clause.text.casefold().strip()
            existing = deduplicated.get(key)
            if existing is None or clause.weight > existing.weight:
                deduplicated[key] = clause
        selected = sorted(
            deduplicated.values(), key=lambda item: (-item.weight, item.text.casefold())
        )
        rendered = " OR ".join(_quote(item.text) for item in selected)
        return QueryPlan(
            id=stable_id("query-plan", f"{name}:{resolved.mode.value}:{rendered}"),
            name=name,
            clauses=selected,
            rendered_query=rendered,
            concept_ids=expanded_ids,
            discipline_ids=sorted(set(discipline_ids)),
            notes=[
                f"Retrieval mode: {resolved.mode.value}.",
                "Field-native lexical plan compiled without quantum-relevance filtering.",
                "Seed/scaffold vocabulary remains provenance-tagged and should be evaluated "
                "empirically.",
            ],
        )

    def compile_discipline(
        self,
        discipline_id: str,
        *,
        max_concepts: int = 100,
        policy: QueryCompilerPolicy | None = None,
    ) -> QueryPlan:
        if self.session.get(DisciplineRow, discipline_id) is None:
            raise KeyError(f"unknown discipline: {discipline_id}")
        discipline_ids = self._discipline_descendants(discipline_id)
        concepts = list(
            self.session.scalars(
                select(ConceptRow)
                .where(ConceptRow.discipline_id.in_(discipline_ids))
                .order_by(ConceptRow.id)
                .limit(max_concepts)
            )
        )
        return self.compile_concepts(
            [item.id for item in concepts],
            name=f"discipline:{discipline_id}",
            policy=policy or QueryCompilerPolicy(max_terms_per_concept=8),
        )

    def _concept_clauses(
        self,
        concept: ConceptRow,
        policy: QueryCompilerPolicy,
    ) -> list[QueryClause]:
        terms = list(
            self.session.scalars(
                select(TermRow).where(TermRow.concept_id == concept.id).order_by(TermRow.id)
            )
        )
        candidates = [
            QueryClause(
                text=concept.canonical_concept,
                source="concept.canonical_concept",
                concept_id=concept.id,
                term_type="canonical",
                weight=_TERM_PRIORITY["canonical"],
            )
        ]
        seen = {concept.canonical_concept.casefold().strip()}
        for term in terms:
            if not self._term_allowed(term.term_type, policy):
                continue
            key = term.term.casefold().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            candidates.append(
                QueryClause(
                    text=term.term,
                    source="term",
                    concept_id=concept.id,
                    term_type=term.term_type,
                    weight=_TERM_PRIORITY.get(term.term_type, 0.8),
                )
            )
        candidates.sort(key=lambda item: (-item.weight, item.text.casefold()))
        return candidates[: policy.max_terms_per_concept]

    @staticmethod
    def _term_allowed(term_type: str, policy: QueryCompilerPolicy) -> bool:
        if term_type == "historical" and not policy.include_historical:
            return False
        if policy.mode == QueryMode.PRECISION:
            return term_type in {"preferred", "synonym", "abbreviation", "canonical"}
        if policy.mode == QueryMode.BALANCED:
            return term_type not in {"related", "broader"}
        return True

    def _related_concepts(
        self,
        concept_ids: list[str],
        policy: QueryCompilerPolicy,
    ) -> list[str]:
        if policy.max_related_concepts == 0:
            return []
        rows = list(
            self.session.scalars(
                select(ConceptRelationRow).where(
                    ConceptRelationRow.source_concept_id.in_(concept_ids),
                    ConceptRelationRow.relationship.in_(policy.related_relationships),
                )
            )
        )
        return [row.target_concept_id for row in rows[: policy.max_related_concepts]]

    def _discipline_descendants(self, discipline_id: str) -> list[str]:
        discovered: list[str] = []
        queue: deque[str] = deque([discipline_id])
        while queue:
            current = queue.popleft()
            if current in discovered:
                continue
            discovered.append(current)
            children = list(
                self.session.scalars(
                    select(DisciplineRow.id)
                    .where(DisciplineRow.parent_id == current)
                    .order_by(DisciplineRow.id)
                )
            )
            queue.extend(children)
        return discovered
