# Scientific Discovery

Research software for discovering recurring computational and mathematical problem structures across scientific disciplines and evaluating their relationship to quantum computation.

## Research objective

The project first searches science broadly and field-natively, represents the computational problems evidenced by scientific works, and discovers recurring structures across weakly connected disciplines. Only afterward are those structures compared with known quantum algorithms and primitives.

The scientific work is evidence. The central derived research object is `ProblemInstance`.

## Search architecture

1. **Scientific retrieval** — high-recall, field-native literature search.
2. **Problem extraction** — identify the computational problem actually being solved.
3. **Cross-domain structural search** — compare mathematical objects, operations, constraints, state/access models, complexity, and bottlenecks across fields.
4. **Quantum target search** — determine whether the structure is established, transferable, extensible, a plausible algorithmic gap, negative, or unresolved.

Quantum relevance does not bias the general scientific corpus.

## v0.2 architecture

The repository now contains executable foundations for:

- `storage/` — canonical relational database and migrations;
- `corpus/` — works, versions, identifiers, assets, citations, provenance;
- `ontology/` — seed/native vocabulary ingestion and query compilation;
- `retrieval/` — gateway/fixture providers, query plans, retrieval runs;
- `documents/` — structured sections, equations, figures, tables;
- `problems/` — `ProblemInstance`, extraction contracts, problem families;
- `mathematics/` — multi-view mathematical expressions and structures;
- `analysis/` — transparent structural similarity and clustering baselines;
- `discovery/` — cross-domain candidate representation/ranking;
- `quantum/` — primitives, algorithms, assumptions, structural matching;
- `evaluation/` — benchmarks and extraction metrics;
- `experiments/` — reproducible experiment tracking;
- `pipeline/` — explicit staged orchestration;
- `ai/` — algorithm-proposal and evaluation contracts without coupling to one model provider.

Generic source transport remains the responsibility of `feed402` and `x402-research-gateway`.

## Setup

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[dev]'

## Validate

    pytest -q
    ruff check .
    mypy src

## Initialize the research database

    discovery db init
    discovery db info

## Import the existing ontology seed

    discovery ontology import-seed scientific_retrieval_ontology_v0_1
    discovery ontology stats

The seed is explicitly marked as scaffold data; later native vocabulary releases supersede or enrich it.

## Build a retrieval plan

    discovery ontology plan <CONCEPT_ID>

## Existing benchmark workflow

    discovery validate-problem data/examples/problem.example.json
    discovery validate-corpus data/benchmarks/problems-v0.1/corpus.json

## Documentation

- `docs/RESEARCH_CHARTER.md`
- `docs/ANNOTATION_PROTOCOL_V0.1.md`
- `docs/BENCHMARK_DESIGN_V0.1.md`
- `docs/ARCHITECTURE_V0.2.md`
- `docs/DATA_MODEL_V0.2.md`
- `docs/RETRIEVAL_PIPELINE_V0.2.md`
- `docs/DEVELOPMENT_V0.2.md`
- `docs/UPGRADE_NOTES_V0.2.md`
