# Scientific Discovery

Computational research infrastructure for discovering recurring scientific problem structures across disciplines and evaluating their relationship to quantum computation.

## Research objective

The long-term objective is to discover recurring computational and mathematical problem structures across scientific fields, then determine which structures:

- map to known quantum algorithms;
- represent underexplored applications of known quantum primitives;
- expose structural gaps in existing quantum algorithm families;
- may motivate new quantum algorithms.

The project deliberately does not begin by searching science for things that look quantum.

Scientific problem structure is discovered first.

Quantum relevance is evaluated afterward.

## Core research object

The scientific work is evidence.

The principal research object is currently `ProblemInstance`.

A `ProblemInstance` represents computational structure including:

- task family;
- inputs;
- outputs;
- objective;
- constraints;
- state space;
- access model;
- mathematical objects;
- operators;
- equations;
- structural properties;
- algorithmic operations;
- known methods;
- classical baselines;
- scale parameters;
- complexity claims;
- reported bottlenecks;
- assumptions;
- approximations;
- evidence;
- provenance;
- uncertainty.

## Current milestone

**v0.1 — Scientific Problem Representation Core**

Current work focuses on:

1. defining `ProblemInstance`;
2. preserving source evidence and provenance;
3. constructing a cross-disciplinary annotation benchmark;
4. testing whether computational structure can be represented consistently across fields;
5. refining the schema from actual scientific examples rather than designing it entirely in the abstract.

## Planned research pipeline

The intended pipeline is:

1. Scientific source discovery.
2. Scholarly identity and provenance.
3. Scientific work retrieval.
4. `ProblemInstance` extraction.
5. Mathematical structure extraction.
6. Cross-disciplinary structural comparison.
7. Problem-family discovery.
8. Quantum algorithm and primitive mapping.
9. Classical and dequantization validation.
10. AI-guided investigation of high-value structural gaps.

## Repository boundary

Generic provider infrastructure belongs in:

- `feed402`
- `x402-research-gateway`

This repository owns downstream scientific representation and discovery.

It should not duplicate provider payments, API routing, or generic source normalization except for temporary development fixtures.

## Project layout

    src/discovery/
        core/
        evaluation/
        problems/

    docs/
        RESEARCH_CHARTER.md
        ANNOTATION_PROTOCOL_V0.1.md

    schemas/
        problem-instance.schema.json
        problem-annotation.schema.json

    data/
        examples/
        seed/

    tests/

    runs/

## Setup

From the repository root:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[dev]'

## Validate the example problem

    discovery validate-problem data/examples/problem.example.json

## Run tests

    pytest -q
    ruff check .
    mypy src

## Research documentation

Read:

- `docs/RESEARCH_CHARTER.md`
- `docs/ANNOTATION_PROTOCOL_V0.1.md`

## Existing research inputs

The repository also preserves prior scientific retrieval ontology and research/audit artifacts.

These artifacts are seed research inputs.

They should retain provenance and version history and should not automatically be treated as authoritative scientific truth.

## Immediate next milestone

The next milestone is a deliberately cross-disciplinary pilot benchmark.

We will annotate real scientific works from substantially different fields and use those annotations to determine where the current `ProblemInstance` representation succeeds, fails, or encodes the wrong distinctions.
