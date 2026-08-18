# Development Guide v0.2

## Install

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[dev]'

## Validate

    pytest -q
    ruff check .
    mypy src

## Initialize local database

    discovery db init
    discovery db info

The default database is `data/scientific_discovery.db`.

## Import the v0.1 ontology seed

    discovery ontology import-seed scientific_retrieval_ontology_v0_1
    discovery ontology stats

The import is idempotent. Imported concepts are marked `seed`/`scaffold` rather than authoritative.

## Compile a transparent retrieval plan

    discovery ontology plan <CONCEPT_ID>

or print only the rendered query:

    discovery retrieval plan <CONCEPT_ID>

## Store a manually annotated problem

    discovery corpus add-problem data/examples/problem.example.json

## Gateway search

Set a gateway URL only when a gateway instance is available:

    export DISCOVERY_GATEWAY_URL=http://localhost:8080
    discovery retrieval gateway-search "rare event sampling"

Gateway calls are never made by tests.

## Migrations

For existing local databases use Alembic:

    alembic upgrade head

`discovery db init` remains convenient for new disposable development databases.
