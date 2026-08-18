#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

DB_PATH="${TMPDIR:-/tmp}/scientific_discovery_v03_smoke.db"
MIGRATION_DB="${TMPDIR:-/tmp}/scientific_discovery_v03_migration.db"
SCHEMA_DIR="${TMPDIR:-/tmp}/scientific_discovery_v03_schemas"
rm -f "$DB_PATH" "$MIGRATION_DB"
rm -rf "$SCHEMA_DIR"
DB_URL="sqlite:///$DB_PATH"
CLI=(python -m discovery.cli)

"${CLI[@]}" validate-problem data/examples/problem.example.json
"${CLI[@]}" db init --database "$DB_URL"
"${CLI[@]}" ontology import-seed scientific_retrieval_ontology_v0_1 --database "$DB_URL" >/dev/null
"${CLI[@]}" ontology stats --database "$DB_URL"
"${CLI[@]}" ontology plan CF-300101 --database "$DB_URL" >/dev/null
"${CLI[@]}" retrieval batch CF-300101 --database "$DB_URL" >/dev/null
"${CLI[@]}" process-file smoke-work smoke-asset latex data/examples/document.example.tex --database "$DB_URL"
"${CLI[@]}" analysis run --database "$DB_URL"
"${CLI[@]}" quantum catalog-import data/examples/quantum_catalog.example.json --database "$DB_URL"
"${CLI[@]}" quantum screen data/examples/quantum_catalog.example.json --database "$DB_URL" >/dev/null
"${CLI[@]}" coverage snapshot --database "$DB_URL" >/dev/null
"${CLI[@]}" generate-schemas --output-dir "$SCHEMA_DIR" >/dev/null
"${CLI[@]}" db info --database "$DB_URL"

DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic upgrade head
REVISION="$(DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic current 2>/dev/null)"
case "$REVISION" in
  *0002*) ;;
  *) echo "expected alembic revision 0002, got: $REVISION" >&2; exit 1 ;;
esac

printf 'scientific-discovery v0.3 smoke test passed\n'
