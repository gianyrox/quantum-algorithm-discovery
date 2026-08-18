# Scientific Discovery

Research software for discovering recurring computational and mathematical problem structures across scientific disciplines and evaluating their relationship to quantum computation.

## Research objective

The project searches science broadly and field-natively, represents the computational problems evidenced by scientific works, and discovers recurring structures across weakly connected disciplines. Only afterward are those structures compared with known quantum algorithms and primitives.

The scientific work is evidence. The central derived research object is `ProblemInstance`.

## Search method

The engine separates four searches that must not be collapsed:

1. **Scientific retrieval** — high-recall, field-native retrieval using native terminology, synonyms, historical terms, provider federation, and citation expansion.
2. **Problem-structure extraction** — determine what computational problem a work is actually solving: inputs, outputs, objective, constraints, mathematical objects, operations, access model, scaling, and bottlenecks.
3. **Cross-domain structural search** — identify high structural similarity across low lexical similarity, low citation connectivity, and different disciplines.
4. **Quantum target search** — compare reviewed problem families with known quantum algorithms/primitives while separately checking access assumptions, classical baselines, data loading, readout, dequantization, resources, and end-to-end feasibility.

Quantum relevance does not bias construction of the general scientific corpus.

## v0.3 operational research engine

The repository now includes executable foundations for:

- `storage/` — relational canonical store, Alembic migrations, content-addressed local object store;
- `corpus/` — works, versions, identifiers, conservative identity evidence, assets, citations, provider-native research-object relations;
- `ontology/` — seed ingestion, native OBO/SKOS-RDF/XML/JSONL ingestion with release provenance, precision/balanced/high-recall compilation, discipline plans, related-concept expansion, unknown-vocabulary mining;
- `retrieval/` — gateway manifest discovery, query batching, federated search, replayable retrieval runs, resumable batch checkpoints, citation expansion, asset discovery, auditable saturation stopping, fixture and generic direct-provider boundaries;
- `documents/` — rights checks, rights-aware acquisition, content-addressed retention, plain-text/HTML/JATS/TEI/LaTeX parsers, sections, equations, figures, tables, document persistence;
- `mathematics/` — multi-view expressions, lexical alpha-normalization baseline, symbols/operators/features, persistence;
- `problems/` — `ProblemInstance`, structural signatures, human/LLM/rule contracts, transparent low-confidence extraction baseline, normalized evidence/math/method persistence;
- `analysis/` — deterministic local embeddings, exact vector search baseline, hybrid structural/lexical/semantic similarity, clustering, citation-graph statistics, co-citation and bibliographic coupling;
- `discovery/` — cross-domain candidate generation/ranking and candidate problem-family construction;
- `quantum/` — versioned catalog import, structural screening, explicit quantum-advantage checklist, negative/unresolved states;
- `evaluation/` — benchmark workflow, retrieval metrics, extraction metrics, annotation agreement, representation completeness;
- `observability/` — coverage snapshots and explicit gaps;
- `review/` — human review events;
- `experiments/` — reproducible experiment records;
- `pipeline/` — composable retrieval/document/problem/math/analysis/quantum facade;
- `ai/` — algorithm-hypothesis reasoner/evaluator interfaces and persisted proposal/evaluation lifecycle.

Generic provider transport and source-specific semantics remain primarily the responsibility of `feed402` and `x402-research-gateway`.

## Setup

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[dev]'

## Validate

    pytest -q
    ruff check .
    mypy src
    bash scripts/smoke_v03.sh

## Initialize database and ontology

    discovery db init
    discovery ontology import-seed scientific_retrieval_ontology_v0_1
    discovery ontology stats

## Inspect a transparent retrieval plan

    discovery ontology plan <CONCEPT_ID>
    discovery retrieval batch <CONCEPT_ID>

## Run an operational concept search

Set the gateway URL first:

    export DISCOVERY_GATEWAY_URL=https://your-gateway.example
    discovery search <CONCEPT_ID>

The search compiles the concept into bounded field-native queries, executes each query as a separate provenance-bearing retrieval run, persists canonical works, and can later expand citations/assets.

## Parse and structurally process a lawful local document

    discovery process-file example-work example-asset latex data/examples/document.example.tex

This parses the document, extracts mathematical occurrences, and runs the transparent low-confidence `ProblemInstance` baseline. Human benchmark annotations remain the scientific reference standard until better extractors are evaluated.

## Coverage

    discovery coverage snapshot

## Quantum screening

The software does not fabricate a quantum literature catalog. Import a separately researched catalog and screen only after problem extraction:

    discovery quantum catalog-import path/to/catalog.json
    discovery quantum screen path/to/catalog.json

Structural compatibility is not quantum advantage; every screening remains unresolved until the explicit validation checks are addressed.

## Documentation

- `docs/RESEARCH_CHARTER.md`
- `docs/ANNOTATION_PROTOCOL_V0.1.md`
- `docs/BENCHMARK_DESIGN_V0.1.md`
- `docs/ARCHITECTURE_V0.3.md`
- `docs/SEARCH_METHOD_V0.3.md`
- `docs/OPERATIONAL_RESEARCH_ENGINE_V0.3.md`
- `docs/LIMITS_V0.3.md`
- `docs/UPGRADE_NOTES_V0.3.md`
