from __future__ import annotations

from discovery.retrieval.feed402 import Feed402Envelope, Feed402Rights


def _receipt() -> dict[str, object]:
    return {
        "tier": "query",
        "price_usd": 0.005,
        "tx": "stub",
        "paid_at": "2026-08-18T14:00:00Z",
    }


def test_feed402_normalizes_legacy_single_citation_and_result_grounding() -> None:
    envelope = Feed402Envelope.from_mapping(
        {
            "data": {"results": [{"title": "A"}]},
            "citation": {
                "type": "source",
                "source_id": "doi:10.1/a",
                "provider": "crossref",
                "retrieved_at": "2026-08-18T14:00:00Z",
            },
            "receipt": _receipt(),
        }
    )
    assert len(envelope.citation) == 1
    assert envelope.citation_for_result(0) is envelope.citation[0]


def test_feed402_result_index_overrides_ordinal_alignment() -> None:
    envelope = Feed402Envelope.from_mapping(
        {
            "data": {"results": [{"title": "A"}, {"title": "B"}]},
            "citation": [
                {
                    "type": "source",
                    "source_id": "b",
                    "provider": "provider-b",
                    "retrieved_at": "2026-08-18T14:00:00Z",
                    "result_index": [1],
                },
                {
                    "type": "source",
                    "source_id": "a",
                    "provider": "provider-a",
                    "retrieved_at": "2026-08-18T14:00:00Z",
                    "result_index": [0],
                },
            ],
            "receipt": _receipt(),
        }
    )
    assert envelope.citation_for_result(0).source_id == "a"  # type: ignore[union-attr]
    assert envelope.citation_for_result(1).source_id == "b"  # type: ignore[union-attr]


def test_feed402_rights_unknown_grants_nothing_and_asset_inherits_record_rights() -> None:
    rights = Feed402Rights(
        metadata={"license": "CC0", "status": "allowed"},
        redistribution="allowed",
        tdm="allowed",
        retention="unknown",
    )
    assert rights.permits("redistribution") is True
    assert rights.permits("tdm") is True
    assert rights.permits("retention") is False
    assert rights.permits("model_training") is False

    envelope = Feed402Envelope.from_mapping(
        {
            "data": {"record": {"title": "A"}},
            "citation": [
                {
                    "type": "source",
                    "source_id": "a",
                    "provider": "openalex",
                    "retrieved_at": "2026-08-18T14:00:00Z",
                    "rights": rights.model_dump(mode="json"),
                    "assets": [
                        {
                            "asset_id": "asset-a",
                            "representation": "pdf",
                            "canonical_url": "https://example.org/a.pdf",
                            "availability": "retrievable",
                        }
                    ],
                }
            ],
            "receipt": _receipt(),
        }
    )
    citation = envelope.citation[0]
    asset = citation.assets[0].to_asset(
        work_id="work-a",
        provider="openalex",
        inherited_rights=citation.rights,
    )
    assert asset.rights is not None
    assert asset.rights.redistribution == "allowed"
    assert asset.rights.retention == "unknown"
