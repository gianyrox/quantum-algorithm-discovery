# Real-Data Execution v0.4

## Purpose

v0.4 is the transition from architecture-first development to auditable execution against real scientific infrastructure.

The goal of the retrieval layer is not “get some papers.” It is to construct a corpus whose coverage, identities, source assertions, request history, content rights, and stopping decisions can be inspected later.

## HTTP execution

`ResilientHttpClient` provides the common transport mechanics:

- bounded retry attempts;
- exponential delay with provider `Retry-After` support when numeric;
- explicit retryable status codes;
- redaction of known credential-like query fields;
- deterministic request fingerprints over the redacted request;
- response SHA-256 values;
- selected rate-limit/cache headers;
- final request audit callbacks.

Retries are transport mechanics only. The layer does not guess provider semantics.

## Direct providers

The first direct adapters are OpenAlex, Crossref, Europe PMC, and arXiv. Each normalizes enough metadata to produce a canonical-work candidate while preserving the raw provider record.

Direct federation executes providers independently and performs reciprocal-rank fusion only as a retrieval presentation rank. It does not merge identity.

Single-provider deep harvest uses each adapter's native pagination model and stores a `ProviderHarvestCheckpoint` for every page.

## Gateway execution

Gateway mode supports the observed operational surface for:

- manifest/capability discovery;
- federated search;
- identity-resolution evidence;
- citations;
- assets;
- integrity/update evidence;
- signed-cursor harvest;
- sync capability metadata;
- coverage/gap reports.

Gateway signed cursors are persisted client-side. Completed pages are not replayed on a resumed run, and previously canonicalized work IDs are recovered from retrieval hits.

## Identity and citations

Identity evidence is directional and provider-attributed. Strong provider assertions such as `same_work` may attach aliases when they do not conflict with existing canonical identity. Fuzzy possible matches remain evidence for review.

Citation edges need two canonical endpoints before they enter the canonical citation table. When an endpoint is still only an external identifier, the system preserves the provider assertion as a research-object relation. A later materialization pass can resolve it when the missing work enters the corpus.

## Integrity

Corrections, retractions, withdrawals, and related update assertions are stored by provider. Provider disagreement remains visible. No assertion is not equivalent to a clean bill of health.

## Asset processing

The preferred automatic processing order is structured source first:

1. JATS/XML;
2. TEI;
3. TeX/source;
4. HTML;
5. plain text;
6. PDF only when necessary and separately supported.

This order preserves sections, equations, references, tables, and other structure rather than flattening them early.

## Campaigns

A campaign stores scientific intent independently from one concrete query. It can be scoped to a concept, discipline, or raw query and records selected providers, result limits, optional gateway enrichment, and downstream queue behavior.

Campaign configuration is provenance. A failed provider call should leave an inspectable failed run rather than disappear from the research history.
