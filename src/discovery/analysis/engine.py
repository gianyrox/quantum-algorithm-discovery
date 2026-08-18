from __future__ import annotations

from datetime import UTC, datetime
from itertools import combinations
from uuid import uuid4

from sqlalchemy.orm import Session

from discovery.analysis.embeddings import EmbeddingProvider
from discovery.analysis.features import hybrid_similarity
from discovery.analysis.similarity import SimilarityEvidence
from discovery.problems.schema import ProblemInstance
from discovery.storage.models import ProblemSimilarityRow, SimilarityRunRow


class SimilarityEngine:
    def __init__(self, session: Session) -> None:
        self.session = session

    def compare_all(
        self,
        problems: list[ProblemInstance],
        *,
        embedding_provider: EmbeddingProvider | None = None,
        citation_connectivity: dict[tuple[str, str], float] | None = None,
    ) -> tuple[str, dict[tuple[str, str], SimilarityEvidence]]:
        run_id = str(uuid4())
        method = "structural+lexical"
        vectors: dict[str, list[float]] = {}
        if embedding_provider is not None:
            method += "+semantic"
            texts = [problem.natural_language_statement for problem in problems]
            embedded = embedding_provider.embed(texts)
            vectors = {
                problem.id: vector
                for problem, vector in zip(problems, embedded, strict=True)
            }
        self.session.add(
            SimilarityRunRow(
                id=run_id,
                method=method,
                parameters_json={
                    "problem_count": len(problems),
                    "embedding_provider": getattr(embedding_provider, "name", None),
                },
                created_at=datetime.now(UTC),
            )
        )
        results: dict[tuple[str, str], SimilarityEvidence] = {}
        connectivity = citation_connectivity or {}
        for left, right in combinations(problems, 2):
            key = (left.id, right.id)
            reverse = (right.id, left.id)
            citation_score = connectivity.get(key, connectivity.get(reverse, 0.0))
            evidence = hybrid_similarity(
                left,
                right,
                left_embedding=vectors.get(left.id),
                right_embedding=vectors.get(right.id),
                citation_connectivity=citation_score,
            )
            results[key] = evidence
            self.session.add(
                ProblemSimilarityRow(
                    run_id=run_id,
                    problem_a_id=left.id,
                    problem_b_id=right.id,
                    score=evidence.structural_score(),
                    evidence_json=evidence.model_dump(mode="json"),
                )
            )
        self.session.flush()
        return run_id, results
