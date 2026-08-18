from discovery.analysis.signature_index import StructuralSignature, StructuralSignatureIndex


def test_signature_index_generates_local_neighbors() -> None:
    index = StructuralSignatureIndex(bands=4)
    index.add(StructuralSignature(object_id="a", tokens=["matrix", "sparse", "optimization"]))
    index.add(StructuralSignature(object_id="b", tokens=["matrix", "sparse", "optimization"]))
    index.add(StructuralSignature(object_id="c", tokens=["graph", "sampling"]))
    neighbors = index.neighbors("a")
    assert neighbors[0].object_id == "b"
