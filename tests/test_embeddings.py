from __future__ import annotations

from discovery.analysis.embeddings import EmbeddingRecord


def test_embedding_record_versions_representation() -> None:
    record = EmbeddingRecord(
        object_type="problem_instance",
        object_id="p1",
        provider="fixture",
        model="baseline",
        model_version="1",
        vector=[0.1, 0.2, 0.3],
    )
    assert record.dimensions == 3
