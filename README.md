# Quantum Algorithm Discovery

Active pilot research project on AI-guided quantum algorithm discovery.

`scientific-discovery` is the research engine used to retrieve scientific work, extract computational problem structure, compare recurring structures across disciplines, and later evaluate those structures against quantum algorithms.

## Research objective

The engine searches science broadly and field-natively, constructs an auditable corpus, represents the computational problems evidenced by scientific objects, and searches for recurring structures across weakly connected disciplines. Only afterward are reviewed structures compared with known quantum algorithms and primitives.

A paper is evidence, not the central research object. The main derived research object is `ProblemInstance`.

## Four separate searches

The system deliberately keeps four stages separate:

1. **Scientific retrieval** — high-recall, field-native retrieval using native terminology, synonyms, historical terminology, provider federation, citation expansion, and audited saturation.
2. **Problem-structure extraction** — determine what computational problem a work is solving: inputs, outputs, objective, constraints, mathematical objects, operations, access model, scaling, assumptions, and bottlenecks.
3. **Cross-domain structural search** — identify high computational/mathematical similarity across low lexical similarity, low citation connectivity, and different disciplines.
4. **Quantum target search** — compare reviewed problem families with known quantum algorithms and primitives while independently checking access assumptions, classical baselines, input/output cost, state preparation, readout, dequantization, resources, and end-to-end feasibility.

Quantum relevance does not bias construction of the general scientific corpus.

## Current experiment

**Campaign 001 — Cross-Disciplinary Pilot**

Status: active.

The pilot uses 24 frozen works across eight sampling strata. It is quantum-blind. The current run tests retrieval provenance, identity resolution, asset discovery, document acquisition, problem extraction, mathematical representation, and structural comparison.

Failures are recorded before repair unless they block the experiment.

## v0.11 gateway-first research boundary

v0.11 makes `x402-research-gateway` the canonical boundary for **all production external scientific acquisition**. `scientific-discovery` no longer chooses between local direct-provider clients and the gateway during normal research execution.

```text
scientific-discovery
        |
        | feed402/0.3
        v
x402-research-gateway
        |
        v
scientific providers / vocabularies / object repositories
```

Every paid gateway result is parsed as feed402 before downstream scientific interpretation. Retrieval envelopes are persisted immutably and linked to `RetrievalRun`; campaigns link those same records to `CampaignRun` and record the gateway manifest fingerprint, protocol version, coverage context, citation count, and lineage count. Unknown rights remain not granted.

Legacy direct OpenAlex/Crossref/Europe PMC/arXiv adapters remain temporarily for parity tests only. They are not exposed by the v0.11 CLI and the default runtime factory blocks direct execution.

See `docs/ADR-001-GATEWAY-FIRST-RESEARCH.md`, `docs/GATEWAY_FIRST_V0.11.md`, and `docs/ROADMAP.md`.

## v0.10 scientific structure discovery engine

v0.10 combines the planned v0.5-v0.10 pre-quantum milestones into one integrated research engine. The active v0.10 pipeline ends at cross-disciplinary structural candidates, problem families, audited coverage, and retrieval feedback. It does **not** use quantum relevance to shape retrieval or discovery. Preexisting quantum modules remain only for backward compatibility and later separately researched work.

Major v0.10 capabilities include document references/citation mentions, evidence-grounded problem extraction, extractor ensembles and quality metrics, mathematical fingerprints and similarity, multi-view problem similarity, family/candidate discovery, historical terminology, stratified coverage, audited saturation, active retrieval, reproducibility manifests, and iterative feedback.

Useful commands:

```bash
discovery structure cascade
discovery structure problem-quality path/to/problem.json
discovery structure math-compare left.json right.json
discovery structure discover problems.jsonl --discipline-map disciplines.json
discovery structure coverage coverage_records.jsonl
discovery structure prioritize retrieval_scopes.jsonl
```

Validation:

```bash
pytest -q
ruff check .
mypy src
bash scripts/smoke_v011.sh
```

See `docs/ARCHITECTURE_V0.10.md` and `docs/PREQUANTUM_ENGINE_V0.10.md`.

## Historical v0.4 real-data execution engine

v0.4 turns the v0.3 architecture into a resumable real-data execution layer.

### Retrieval and provider boundary

- Gateway mode consumed the `x402-research-gateway` capability contract for normalized federated search, identity evidence, citations, assets, integrity, signed-cursor harvest, sync metadata, and coverage reporting.
- v0.4 also supplied first-party direct adapters for OpenAlex, Crossref, Europe PMC, and arXiv. v0.11 retires those as active acquisition paths and keeps them temporarily only for migration/parity testing.
- `ResilientHttpClient` centralizes bounded retries, rate-limit backoff, URL-secret redaction, request fingerprints, response hashes, and request audit records.
- Parallel direct federation preserves provider rank and raw records; reciprocal-rank fusion is a presentation rank and never an identity merge.
- Deep provider harvesting and gateway signed-cursor harvesting persist checkpoints and resume without replaying completed pages.

### Canonical corpus and evidence

- `Work -> WorkVersion -> Asset -> Document -> ProblemInstance` is now an enforced operational path for canonical processing.
- DOI, PMID, PMCID, arXiv, OpenAlex, and other provider identifiers remain explicit aliases rather than becoming canonical identity by string coincidence.
- Provider identity assertions are stored as evidence. Only explicit strong identity relations are eligible for automatic alias attachment; fuzzy `possible_same_work` evidence remains reviewable evidence.
- Citation assertions whose endpoints are not yet canonical works remain external-identifier relations and can be materialized later. They are not written into the canonical citation table prematurely.
- Integrity assertions are first-class and absence of an integrity notice is treated as unknown, never as clearance.

### Documents, rights, and execution

- Asset locations do not imply permission. Automated acquisition requires explicit machine-readable TDM permission, and raw retention additionally requires explicit retention permission.
- Structured assets are ranked ahead of PDFs when rights and availability permit: JATS/XML, TEI, TeX/source, HTML, then plain text.
- Acquired bytes can be retained in the content-addressed object store with an acquisition audit row and checksum.
- A durable local processing queue supports idempotent jobs, retry state, priorities, and single-process execution without pretending SQLite is a distributed queue.
- Durable research campaigns preserve search intent, provider scope, run status, query results, and optional identity/integrity enrichment.

### Scientific analysis layers

The v0.3 analysis layers remain available:

- native and seed ontology ingestion and transparent query compilation;
- structured document parsing and math extraction;
- `ProblemInstance` extraction and structural signatures;
- deterministic local embedding and exact vector-search baselines;
- hybrid similarity, clustering, citation graph statistics, and cross-domain candidates;
- problem families, review events, evaluation, and coverage snapshots;
- versioned quantum catalog import, structural screening, and explicit advantage/dequantization checks;
- AI algorithm-proposal interfaces whose outputs remain hypotheses until independently evaluated.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Validate

```bash
pytest -q
ruff check .
mypy src
bash scripts/smoke_v010.sh
bash scripts/smoke_v011.sh
```

The v0.11 smoke test verifies the gateway/feed402 boundary, schema generation, and Alembic migration through revision `0005`. The v0.10 smoke test remains as historical validation of the pre-quantum structure engine.

## Initialize database and ontology

```bash
discovery db init
discovery ontology import-seed scientific_retrieval_ontology_v0_1
discovery ontology stats
```

## Inspect retrieval language

```bash
discovery ontology plan <CONCEPT_ID>
discovery retrieval batch <CONCEPT_ID>
```

The ontology remains retrieval language and scientific metadata; query compiler templates are execution artifacts, not authoritative scientific concepts.

## Gateway retrieval

```bash
export DISCOVERY_GATEWAY_URL=https://your-gateway.example
export DISCOVERY_GATEWAY_STRICT_FEED402=true

discovery provider gateway-manifest
discovery provider gateway-sync
discovery provider gateway-coverage --field physics
discovery provider resolve 10.1000/example
discovery provider integrity 10.1000/example
# Any newly advertised capability can be driven generically:
discovery provider invoke <operation-id> payload.json
```

Gateway payment/challenge handling is deployment-specific. Scientific Discovery does not embed wallet custody into the scientific analysis layer. Deployment-specific headers may be injected through `DISCOVERY_GATEWAY_HEADERS_JSON`, and library callers may provide a custom `httpx.Client` at the gateway boundary.

A resumable gateway harvest accepts a JSON request payload:

```bash
discovery retrieval gateway-harvest harvest.json --pages 100
```

## Durable campaigns

Create a broad retrieval campaign without quantum filtering:

```bash
CAMPAIGN_ID=$(discovery campaign create concept CF-300101 \
  --providers openalex,crossref,europe_pmc,arxiv \
  --limit 100)

discovery campaign run "$CAMPAIGN_ID"
```

The provider list is a gateway scope, not a request to instantiate local provider clients. Campaigns may also request gateway identity and integrity enrichment. A campaign records what was attempted even when an external capability fails.

## Canonical local processing

Import a canonical work, then process supplied content through the enforced path:

```bash
discovery corpus import-work data/examples/work.example.json

discovery documents process-canonical \
  smoke-work \
  data/examples/asset.example.json \
  latex \
  data/examples/document.example.tex
```

For discovered retrievable assets with explicit rights, enqueue processing:

```bash
discovery queue enqueue <WORK_ID> asset_acquisition --asset <ASSET_ID>
discovery queue work-once
discovery queue stats
```

## Corpus snapshots and observability

```bash
discovery corpus export data/exports/corpus.jsonl
discovery coverage snapshot
discovery coverage operations
```

The operational snapshot reports provider requests/failures, assets, documents, canonical and unresolved citation evidence, identity/integrity assertions, asset acquisitions, and pending/failed jobs.

## Quantum screening

The software does not fabricate a quantum literature catalog. Import a separately researched catalog and screen only after scientific problem extraction:

```bash
discovery quantum catalog-import path/to/catalog.json
discovery quantum screen path/to/catalog.json
```

Structural compatibility is not quantum advantage. Matches remain unresolved until access model, classical baseline, data movement, complexity, resource, dequantization, and end-to-end checks are addressed.

## Documentation

- `docs/ADR-001-GATEWAY-FIRST-RESEARCH.md`
- `docs/ROADMAP.md`
- `docs/GATEWAY_FIRST_V0.11.md`
- `docs/VALIDATION_V0.11.md`
- `docs/UPGRADE_NOTES_V0.11.md`
- `docs/RESEARCH_CHARTER.md`
- `docs/ANNOTATION_PROTOCOL_V0.1.md`
- `docs/BENCHMARK_DESIGN_V0.1.md`
- `docs/ARCHITECTURE_V0.4.md`
- `docs/REAL_DATA_EXECUTION_V0.4.md`
- `docs/PROVIDER_BOUNDARY_V0.4.md`
- `docs/OPERATIONS_V0.4.md`
- `docs/LIMITS_V0.4.md`
- `docs/UPGRADE_NOTES_V0.4.md`
