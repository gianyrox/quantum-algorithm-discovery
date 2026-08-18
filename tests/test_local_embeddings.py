from discovery.analysis.local_embeddings import HashingEmbeddingProvider, cosine_similarity


def test_hashing_embeddings_are_deterministic() -> None:
    provider = HashingEmbeddingProvider(dimensions=64)
    first = provider.embed(["sparse matrix eigenvalue"])[0]
    second = provider.embed(["sparse matrix eigenvalue"])[0]
    assert first == second
    assert len(first) == 64
    assert cosine_similarity(first, second) == 1.0
