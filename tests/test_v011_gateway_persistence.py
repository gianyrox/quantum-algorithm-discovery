from __future__ import annotations

import httpx
import pytest
from sqlalchemy import select

from discovery.execution.campaign import CampaignService
from discovery.execution.schema import CampaignConfig, CampaignScope
from discovery.retrieval.gateway import GatewayProtocolError, GatewayProvider
from discovery.retrieval.models import SearchQuery
from discovery.retrieval.service import RetrievalService
from discovery.storage.database import (
    create_database_engine,
    init_db,
    make_session_factory,
    session_scope,
)
from discovery.storage.models import Feed402EnvelopeRow


def _manifest() -> dict[str, object]:
    return {
        "spec": "feed402/0.3",
        "provenance_level": 2,
        "capabilities": ["search"],
        "operations": [
            {
                "operation_id": "federated-search",
                "capability": "search",
                "path": "/research/federated",
                "method": "POST",
                "tier": "query",
            }
        ],
    }


def _search_envelope() -> dict[str, object]:
    return {
        "data": {
            "results": [
                {
                    "provider": "openalex",
                    "provider_rank": 1,
                    "raw_record": {
                        "doi": "10.1000/gateway-first",
                        "title": "Gateway first science",
                        "publication_year": 2026,
                    },
                }
            ],
            "providers": [
                {"provider": "openalex", "status": "ok", "result_count": 1}
            ],
        },
        "citation": [
            {
                "type": "source",
                "source_id": "10.1000/gateway-first",
                "provider": "openalex",
                "retrieved_at": "2026-08-18T14:00:00Z",
                "result_index": [0],
                "rights": {
                    "metadata": {"license": "CC0", "status": "allowed"},
                    "redistribution": "allowed",
                    "tdm": "allowed",
                    "retention": "allowed",
                },
                "execution": {
                    "level": 2,
                    "request_id": "req-001",
                    "query_fingerprint": "hmac-sha256:query",
                    "provider_request_fingerprint": "hmac-sha256:upstream",
                    "response_sha256": "sha256:response",
                    "software": "x402-research-gateway",
                    "software_version": "0.1.0",
                    "git_commit": "8648ad0",
                },
            }
        ],
        "lineage": [
            {
                "step": 0,
                "derived_object": "federated-result-0",
                "sources": [0],
                "transformation": "federated-search",
                "software": "x402-research-gateway",
            }
        ],
        "receipt": {
            "tier": "query",
            "price_usd": 0.005,
            "tx": "stub",
            "paid_at": "2026-08-18T14:00:00Z",
        },
    }


def _gateway_client(*, missing_citation: bool = False) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/.well-known/feed402.json":
            return httpx.Response(200, json=_manifest(), request=request)
        if request.url.path == "/research/coverage":
            return httpx.Response(
                200,
                json={"data": {"fields": [], "gaps": []}},
                request=request,
            )
        if request.url.path == "/research/federated":
            payload = _search_envelope()
            if missing_citation:
                payload.pop("citation")
            return httpx.Response(200, json=payload, request=request)
        return httpx.Response(404, request=request)

    return httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://gateway.test",
    )


def test_retrieval_service_persists_feed402_envelope_at_acquisition_boundary(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'retrieval.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    client = _gateway_client()
    gateway = GatewayProvider("https://gateway.test", client=client)
    with session_scope(factory) as session:
        run_id, response = RetrievalService(session, gateway).execute_with_run(
            SearchQuery(text="spectral inverse problem", limit=10)
        )
        assert len(response.hits) == 1
        row = session.scalar(
            select(Feed402EnvelopeRow).where(
                Feed402EnvelopeRow.retrieval_run_id == run_id
            )
        )
        assert row is not None
        assert row.campaign_run_id is None
        assert row.operation == "federated-search"
        assert row.request_id == "req-001"
        assert row.citation_count == 1
        assert row.lineage_count == 1


def test_campaign_links_retrieval_feed402_envelope_to_campaign_run(tmp_path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'campaign.db'}")
    init_db(engine)
    factory = make_session_factory(engine)
    client = _gateway_client()
    gateway = GatewayProvider("https://gateway.test", client=client)
    with session_scope(factory) as session:
        campaign = CampaignService(session).create(
            CampaignConfig(
                scope_type=CampaignScope.QUERY,
                scope_id="cross disciplinary spectral problems",
                result_limit=10,
            )
        )
        result = CampaignService(session).run(campaign.id, gateway)
        assert result.status == "completed"
        assert result.research_boundary == "gateway"
        assert result.feed402_spec == "feed402/0.3"
        assert result.feed402_envelope_count == 1
        assert result.feed402_citation_count == 1
        assert result.feed402_lineage_steps == 1
        row = session.scalar(
            select(Feed402EnvelopeRow).where(
                Feed402EnvelopeRow.campaign_run_id == result.run_id
            )
        )
        assert row is not None
        assert row.retrieval_run_id is not None


def test_strict_gateway_rejects_paid_response_without_feed402_citation() -> None:
    client = _gateway_client(missing_citation=True)
    gateway = GatewayProvider("https://gateway.test", client=client)
    with pytest.raises(GatewayProtocolError):
        gateway.search(SearchQuery(text="missing provenance", limit=1))
