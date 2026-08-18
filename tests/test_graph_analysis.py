from discovery.analysis.graph import bibliographic_coupling, co_citation, directed_graph_stats


def test_graph_analysis_preserves_direction_and_shared_structure() -> None:
    edges = [("a", "x"), ("b", "x"), ("a", "y"), ("b", "y")]
    stats = directed_graph_stats(edges)
    assert stats.out_degree["a"] == 2
    assert stats.in_degree["x"] == 2
    assert bibliographic_coupling(edges)[("a", "b")] == 2
    assert co_citation(edges)[("x", "y")] == 2
