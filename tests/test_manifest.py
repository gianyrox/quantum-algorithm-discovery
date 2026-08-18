from discovery.retrieval.manifest import parse_gateway_manifest


def test_manifest_parses_operations_and_capabilities() -> None:
    manifest = parse_gateway_manifest(
        {
            "spec": "feed402/0.3",
            "capabilities": ["search", "fetch"],
            "provenance_level": 2,
            "operations": [
                {
                    "operation_id": "crossref-search",
                    "capability": "search",
                    "path": "/research/crossref/search",
                    "pagination_model": "cursor",
                }
            ],
        }
    )
    assert manifest.spec == "feed402/0.3"
    assert manifest.operations_for("search")[0].operation_id == "crossref-search"
    assert manifest.provenance_level == 2
