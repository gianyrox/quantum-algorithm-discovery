from __future__ import annotations

from discovery.retrieval.gateway import GatewayProvider
from discovery.retrieval.models import SearchQuery


def test_gateway_parser_preserves_provider_and_ranks() -> None:
    envelope = {
        "data": {
            "results": [
                {
                    "provider": "crossref",
                    "provider_rank": 2,
                    "fused_rank": 1,
                    "provider_score": 0.8,
                    "raw_record": {
                        "doi": "10.1000/test",
                        "title": "A test work",
                        "publication_year": 2024,
                    },
                }
            ],
            "providers": [{"provider": "crossref", "status": "ok", "result_count": 1}],
        },
        "citation": [{"provider": "crossref"}],
    }
    response = GatewayProvider.parse_search_response(SearchQuery(text="test"), envelope)
    assert response.hits[0].provider == "crossref"
    assert response.hits[0].provider_rank == 2
    assert response.hits[0].fused_rank == 1
    assert response.hits[0].work is not None
    assert response.hits[0].work.title == "A test work"
    assert response.provider_reports[0].status == "ok"
