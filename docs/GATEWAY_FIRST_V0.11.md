# Gateway-first research execution — v0.11

v0.11 changes the acquisition boundary, not the scientific objective.

## Canonical path

```text
query plan / campaign
        v
GatewayProvider
        v
x402-research-gateway
        v
feed402 envelope
        v
Feed402EnvelopeRow
        v
canonical Work / Asset / citation evidence
        v
document + problem + math + structural discovery
```

The gateway manifest is capability discovery. Scientific Discovery does not assume a particular provider is present; campaign provider scopes are requests to the gateway, and gateway coverage reports make missing source coverage explicit.

For gateway capabilities that do not yet have a dedicated Scientific Discovery adapter (for example a newly added vocabulary or scientific-object operation), `discovery provider invoke <operation-id> payload.json` executes the manifest-advertised operation and still persists the returned feed402 envelope. This keeps new gateway capabilities usable without reintroducing direct provider clients.

## feed402 persistence

A paid retrieval response is parsed as feed402 before it is accepted. The raw envelope is stored in `feed402_envelope` with:

- operation;
- feed402 spec;
- merchant;
- acquisition timestamp;
- retrieval-run and optional campaign-run linkage;
- execution request ID;
- query fingerprint;
- upstream response hash when published;
- citation count;
- lineage-step count;
- the immutable raw envelope.

The canonical scientific models remain derived views. They do not replace the acquisition evidence.

## Rights

feed402 permissions are three-state: allowed, denied, unknown. Scientific Discovery treats unknown and absence as not granted. Metadata rights and content rights stay separate. A discoverable/retrievable asset still requires an explicit permission decision before automated acquisition/retention.

## Gateway-free exceptions

There is no production direct-provider fallback. The only exceptions are:

- deterministic offline fixtures/replays used by tests and reproducibility workflows;
- actual transfer of a large provider-hosted bulk artifact after the gateway has described that artifact/source through sync or asset discovery. The gateway-issued provenance remains the controlling acquisition record.

## Payment transport

Scientific Discovery does not custody provider API keys or provider-specific credentials. Gateway-level HTTP headers can be injected with `DISCOVERY_GATEWAY_HEADERS_JSON`, and a custom `httpx.Client` can be supplied by library callers when a deployment needs an x402 payment/auth transport. Payment execution is a gateway-transport concern; scientific interpretation starts only after a valid feed402 response returns.

## Environment

```bash
export DISCOVERY_GATEWAY_URL=https://your-gateway.example
export DISCOVERY_GATEWAY_STRICT_FEED402=true
# Optional deployment-specific gateway headers:
export DISCOVERY_GATEWAY_HEADERS_JSON='{}'
```

## First campaign

```bash
CAMPAIGN_ID=$(discovery campaign create query \
  "spectral inverse problems" \
  --providers openalex,crossref,europe_pmc,arxiv \
  --limit 50)

discovery campaign run "$CAMPAIGN_ID"
```

The `--providers` list is now gateway scope, not a request to instantiate local provider clients.
