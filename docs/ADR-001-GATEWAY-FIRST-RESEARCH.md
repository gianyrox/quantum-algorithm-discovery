# ADR-001: Gateway-first external research acquisition

**Status:** Accepted  
**Milestone:** v0.11  
**Protocol boundary:** feed402/0.3

## Decision

All external scientific knowledge acquisition for Scientific Discovery originates through `x402-research-gateway` and is represented at the acquisition boundary with feed402 provenance.

```text
scientific-discovery
        |
        | feed402/0.3
        v
x402-research-gateway
        |
        v
scientific providers, vocabularies, object databases, and repositories
```

`scientific-discovery` owns scientific analysis: corpus construction after acquisition, document intelligence, `ProblemInstance` extraction, mathematical representation, structural similarity, ProblemFamilies, discovery evaluation, and eventually the separate quantum-mapping stage.

`x402-research-gateway` owns external-source access: provider adapters, source capabilities, provider-specific request semantics, identity/citation/integrity access, asset discovery, rights assertions, synchronization metadata, and source-coverage observability.

feed402 is the contract that carries citations, rights, assets, execution provenance, receipts, and derivation lineage across the boundary.

## Hard rules

1. Production research execution may not instantiate direct scholarly-provider clients as an alternative acquisition path.
2. Successful paid gateway responses are rejected in strict mode when they are not valid feed402 responses with citations and a receipt.
3. Every gateway response that participates in retrieval is persisted before downstream scientific interpretation and linked to its `RetrievalRun`.
4. Campaigns link those immutable envelopes to `CampaignRun` and preserve manifest fingerprint, feed402 version, citation counts, lineage counts, and gateway coverage context.
5. Unknown or absent feed402 permissions grant nothing. Asset availability is not a rights grant.
6. Large bulk artifacts may be transferred directly from a provider only after gateway `/research/sync` or asset discovery identifies the location. The local ingestion record must remain linked to the gateway-issued source, release, rights, checksum/asset identity when available, and provenance metadata.
7. Offline deterministic fixtures/replays are allowed for tests and reproducibility. They are not external acquisition paths.
8. The pre-quantum discovery pipeline remains quantum-blind. Gateway adoption does not introduce quantum relevance into scientific retrieval.

## Legacy direct providers

The v0.4-v0.10 direct OpenAlex, Crossref, Europe PMC, and arXiv implementations remain temporarily in source for migration/parity tests. They are not exposed by the v0.11 CLI, and the runtime factory refuses to create them unless the caller explicitly opts into legacy-direct mode. They can be deleted after gateway parity is empirically demonstrated on real campaigns.

## Why

A single research boundary prevents duplicate provider logic from drifting between projects and gives every acquisition the same provenance, rights, capability, and lineage semantics. It also lets the gateway evolve independently as new providers and scientific object types are added while Scientific Discovery stays focused on the research problem.

## Consequences

The first real v0.11 campaigns are also integration tests of the gateway contract. Missing capabilities become observable gateway gaps rather than reasons to silently fall back to a direct provider. If a source is not yet accessible through the gateway, the correct response is to extend the gateway or record the coverage gap.
