# v0.11 upgrade notes

## Breaking execution change

Production external research is gateway-only. The active CLI no longer exposes direct provider search/deep-harvest commands, and `campaign run` no longer accepts `--mode direct`.

Old direct adapter source remains temporarily for parity tests. `create_direct_provider()` now rejects normal use unless `allow_legacy_direct=True` is explicitly supplied.

## New persistence

Alembic revision `0005` creates `feed402_envelope`. Retrieval envelopes are linked to `RetrievalRun`; campaign execution later links those rows to `CampaignRun` without duplicating the raw feed402 response.

## New models

v0.11 adds native feed402 models for structured rights, assets, citations, retrieval provenance, execution provenance, receipts, lineage, and envelopes, plus a research-boundary report.

## Configuration

New settings:

- `DISCOVERY_GATEWAY_HEADERS_JSON` — optional JSON object of deployment-specific gateway headers;
- `DISCOVERY_GATEWAY_STRICT_FEED402` — defaults to true.

Legacy direct-provider environment settings remain parseable during migration but are not used by the active v0.11 research path.

## Upgrade

Apply the overlay on top of the validated v0.10 tree, then run:

```bash
bash scripts/post_upgrade_v011.sh
```
