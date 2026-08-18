#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

MIGRATION_DB="${TMPDIR:-/tmp}/scientific_discovery_v011_migration.db"
SCHEMA_DIR="${TMPDIR:-/tmp}/scientific_discovery_v011_schemas"
rm -f "$MIGRATION_DB"
rm -rf "$SCHEMA_DIR"

python - <<'PY'
import discovery
from discovery.retrieval.boundary import require_gateway_boundary
from discovery.retrieval.feed402 import Feed402Envelope, Feed402Rights
from discovery.retrieval.fixture import FixtureProvider

assert discovery.__version__ == "0.11.0"
require_gateway_boundary(FixtureProvider())
rights = Feed402Rights(redistribution="allowed")
assert rights.permits("redistribution")
assert not rights.permits("retention")
envelope = Feed402Envelope.from_mapping({
    "data": {"results": [{"title": "smoke"}]},
    "citation": [{
        "type": "source",
        "source_id": "smoke:1",
        "provider": "smoke",
        "retrieved_at": "2026-08-18T14:00:00Z",
    }],
    "receipt": {
        "tier": "query",
        "price_usd": 0.0,
        "tx": "stub",
        "paid_at": "2026-08-18T14:00:00Z",
    },
})
assert envelope.citation_for_result(0) is not None
print("v0.11 feed402 boundary smoke passed")
PY

python -m discovery.cli generate-schemas --output-dir "$SCHEMA_DIR" >/dev/null
SCHEMA_COUNT="$(find "$SCHEMA_DIR" -name '*.schema.json' | wc -l | tr -d ' ')"
if [[ "$SCHEMA_COUNT" -lt 110 ]]; then
  echo "expected at least 110 schemas, got $SCHEMA_COUNT" >&2
  exit 1
fi

DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic upgrade head
REVISION="$(DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic current 2>/dev/null)"
case "$REVISION" in
  *0005*) ;;
  *) echo "expected alembic revision 0005, got: $REVISION" >&2; exit 1 ;;
esac

python - <<'PY'
from sqlalchemy import create_engine, inspect
import os

path = os.environ.get("TMPDIR", "/tmp") + "/scientific_discovery_v011_migration.db"
engine = create_engine(f"sqlite:///{path}")
assert "feed402_envelope" in inspect(engine).get_table_names()
print("v0.11 feed402 persistence smoke passed")
PY

printf 'scientific-discovery v0.11 gateway-first smoke test passed\n'
