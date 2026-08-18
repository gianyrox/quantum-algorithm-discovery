#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

DB_PATH="${TMPDIR:-/tmp}/scientific_discovery_v04_smoke.db"
MIGRATION_DB="${TMPDIR:-/tmp}/scientific_discovery_v04_migration.db"
SCHEMA_DIR="${TMPDIR:-/tmp}/scientific_discovery_v04_schemas"
EXPORT_PATH="${TMPDIR:-/tmp}/scientific_discovery_v04_corpus.jsonl"
rm -f "$DB_PATH" "$MIGRATION_DB" "$EXPORT_PATH"
rm -rf "$SCHEMA_DIR"
DB_URL="sqlite:///$DB_PATH"
CLI=(python -m discovery.cli)

"${CLI[@]}" validate-problem data/examples/problem.example.json
"${CLI[@]}" db init --database "$DB_URL"
"${CLI[@]}" ontology import-seed scientific_retrieval_ontology_v0_1 --database "$DB_URL" >/dev/null
"${CLI[@]}" ontology stats --database "$DB_URL"
"${CLI[@]}" ontology plan CF-300101 --database "$DB_URL" >/dev/null
"${CLI[@]}" retrieval batch CF-300101 --database "$DB_URL" >/dev/null

WORK_ID="$("${CLI[@]}" corpus import-work data/examples/work.example.json --database "$DB_URL")"
case "$WORK_ID" in
  *smoke-work*) ;;
  *) echo "unexpected canonical work id: $WORK_ID" >&2; exit 1 ;;
esac

"${CLI[@]}" documents process-canonical \
  smoke-work \
  data/examples/asset.example.json \
  latex \
  data/examples/document.example.tex \
  --database "$DB_URL"
"${CLI[@]}" analysis run --database "$DB_URL"
"${CLI[@]}" quantum catalog-import \
  data/examples/quantum_catalog.example.json \
  --database "$DB_URL"
"${CLI[@]}" quantum screen \
  data/examples/quantum_catalog.example.json \
  --database "$DB_URL" >/dev/null
"${CLI[@]}" coverage snapshot --database "$DB_URL" >/dev/null
"${CLI[@]}" coverage operations --database "$DB_URL"
"${CLI[@]}" corpus export "$EXPORT_PATH" --database "$DB_URL" >/dev/null
"${CLI[@]}" generate-schemas --output-dir "$SCHEMA_DIR" >/dev/null
"${CLI[@]}" db info --database "$DB_URL"

COUNTS="$(DB_URL="$DB_URL" python - <<'PY'
import os
from sqlalchemy import func, select
from discovery.storage.database import create_database_engine, make_session_factory, session_scope
from discovery.storage.models import AssetRow, DocumentRow, ProblemInstanceRow, WorkRow

engine = create_database_engine(os.environ["DB_URL"])
factory = make_session_factory(engine)
with session_scope(factory) as session:
    counts = [
        int(session.scalar(select(func.count()).select_from(WorkRow)) or 0),
        int(session.scalar(select(func.count()).select_from(AssetRow)) or 0),
        int(session.scalar(select(func.count()).select_from(DocumentRow)) or 0),
        int(session.scalar(select(func.count()).select_from(ProblemInstanceRow)) or 0),
    ]
print(" ".join(map(str, counts)))
PY
)"
read -r WORKS ASSETS DOCUMENTS PROBLEMS <<<"$COUNTS"
if [[ "$WORKS" -lt 1 || "$ASSETS" -lt 1 || "$DOCUMENTS" -lt 1 || "$PROBLEMS" -lt 1 ]]; then
  echo "canonical smoke counts failed: $COUNTS" >&2
  exit 1
fi

DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic upgrade head
REVISION="$(DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic current 2>/dev/null)"
case "$REVISION" in
  *0003*) ;;
  *) echo "expected alembic revision 0003, got: $REVISION" >&2; exit 1 ;;
esac

printf 'scientific-discovery v0.4 canonical real-data smoke test passed\n'
