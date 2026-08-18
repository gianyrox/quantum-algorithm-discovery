#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${TMPDIR:-/tmp}/scientific_discovery_smoke.db"
rm -f "$DB_PATH"
DB_URL="sqlite:///$DB_PATH"
CLI=(python -m discovery.cli)

"${CLI[@]}" validate-problem data/examples/problem.example.json
"${CLI[@]}" db init --database "$DB_URL"
"${CLI[@]}" ontology import-seed scientific_retrieval_ontology_v0_1 --database "$DB_URL" >/dev/null
"${CLI[@]}" ontology stats --database "$DB_URL"
"${CLI[@]}" ontology plan CF-300101 --database "$DB_URL" >/dev/null
"${CLI[@]}" corpus add-problem data/examples/problem.example.json --database "$DB_URL"
"${CLI[@]}" db info --database "$DB_URL"

printf 'scientific-discovery smoke test passed\n'
