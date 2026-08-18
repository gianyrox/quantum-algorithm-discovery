from __future__ import annotations

from dataclasses import dataclass

from discovery.analysis.local_embeddings import cosine_similarity


@dataclass(frozen=True)
class VectorHit:
    object_id: str
    score: float


class BruteForceVectorIndex:
    """Exact local baseline before introducing an ANN service.

    This is intentionally simple and reproducible for pilot-scale corpora.
    """

    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}

    def add(self, object_id: str, vector: list[float]) -> None:
        self._vectors[object_id] = list(vector)

    def search(
        self,
        vector: list[float],
        *,
        k: int = 10,
        exclude_id: str | None = None,
    ) -> list[VectorHit]:
        hits = [
            VectorHit(object_id=object_id, score=cosine_similarity(vector, candidate))
            for object_id, candidate in self._vectors.items()
            if object_id != exclude_id
        ]
        hits.sort(key=lambda item: (-item.score, item.object_id))
        return hits[:k]
