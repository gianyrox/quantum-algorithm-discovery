from discovery.analysis.vector_index import BruteForceVectorIndex


def test_brute_force_vector_index() -> None:
    index = BruteForceVectorIndex()
    index.add("a", [1.0, 0.0])
    index.add("b", [0.0, 1.0])
    hits = index.search([1.0, 0.0], k=1)
    assert hits[0].object_id == "a"
