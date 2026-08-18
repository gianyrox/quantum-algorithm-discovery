from __future__ import annotations

import httpx

from discovery.retrieval.gateway import GatewayProvider


def test_gateway_uses_well_known_manifest_and_parses_operational_endpoints() -> None:
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        requested.append(path)
        if path == "/.well-known/feed402.json":
            return httpx.Response(
                200,
                json={
                    "spec": "feed402/0.3",
                    "operations": [
                        {
                            "id": "crossref-search",
                            "path": "/research/crossref/search",
                            "method": "GET",
                            "capabilities": ["search"],
                        }
                    ],
                },
                request=request,
            )
        if path == "/research/resolve":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "relations": [
                            {
                                "subject": "10.1/a",
                                "relation": "same_work",
                                "object": "W123",
                                "provider": "openalex",
                            }
                        ]
                    }
                },
                request=request,
            )
        if path == "/research/integrity":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "relations": [
                            {
                                "subject": "10.1/a",
                                "relation": "retracted_by",
                                "object": "10.1/retraction",
                                "provider": "crossref",
                            }
                        ]
                    }
                },
                request=request,
            )
        if path == "/research/sync":
            return httpx.Response(
                200,
                json={
                    "providers": [
                        {
                            "provider": "crossref",
                            "status": "production",
                            "capabilities": ["search", "fetch"],
                        }
                    ]
                },
                request=request,
            )
        if path == "/research/coverage":
            return httpx.Response(
                200,
                json={"data": {"field": "math", "gaps": [{"dimension": "language"}]}},
                request=request,
            )
        if path == "/research/harvest":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "provider": "crossref",
                        "records": [{"doi": "10.1/a"}],
                        "next_cursor": "cursor-2",
                        "exhausted": False,
                    }
                },
                request=request,
            )
        return httpx.Response(404, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://gateway.test")
    gateway = GatewayProvider("https://gateway.test", client=client, strict_feed402=False)
    manifest = gateway.manifest()
    assert manifest.spec == "feed402/0.3"
    assert manifest.operations_for("search")[0].operation_id == "crossref-search"
    assert gateway.resolve_identity("10.1/a").assertions[0].relation_type == "same_work"
    assert gateway.integrity("10.1/a").assertions[0].relation_type == "retracted_by"
    assert gateway.sync_status().providers[0].provider == "crossref"
    assert gateway.coverage_report(field="math").gaps[0]["dimension"] == "language"
    page = gateway.harvest_page({"provider": "crossref"})
    assert page.cursor == "cursor-2"
    assert page.records[0]["doi"] == "10.1/a"
    assert requested[0] == "/.well-known/feed402.json"
