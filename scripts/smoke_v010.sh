#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

DB_PATH="${TMPDIR:-/tmp}/scientific_discovery_v010_smoke.db"
MIGRATION_DB="${TMPDIR:-/tmp}/scientific_discovery_v010_migration.db"
SCHEMA_DIR="${TMPDIR:-/tmp}/scientific_discovery_v010_schemas"
rm -f "$DB_PATH" "$MIGRATION_DB"
rm -rf "$SCHEMA_DIR"

python - <<'PY'
from discovery.analysis.cross_domain import rank_cross_domain_candidates
from discovery.analysis.discovery_loop import discover_structure
from discovery.coverage.active import ActiveRetrievalPlanner
from discovery.coverage.feedback import FeedbackLoop
from discovery.coverage.saturation import DiscoveryYield
from discovery.coverage.strata import build_coverage_report
from discovery.documents.intelligence import analyze_document
from discovery.documents.schema import DocumentSection, EquationOccurrence, ParsedDocument
from discovery.mathematics.schema import MathExpression
from discovery.mathematics.similarity import compare_fingerprints
from discovery.mathematics.structural import fingerprint_expression
from discovery.problems.enums import ExtractionMethod, TaskFamily
from discovery.problems.quality import assess_problem_quality
from discovery.problems.schema import MathematicalObject, ProblemInstance
from discovery.reproducibility.manifest import ResearchManifest, SoftwareComponent
from discovery.retrieval.cascade import default_high_recall_cascade


def problem(identifier: str, work: str, statement: str) -> ProblemInstance:
    return ProblemInstance(
        id=identifier,
        source_work_id=work,
        natural_language_statement=statement,
        task_family=TaskFamily.OPTIMIZATION,
        objective="minimize cost",
        mathematical_objects=[MathematicalObject(name="matrix", object_type="matrix")],
        operators=["matrix multiply"],
        algorithmic_operations=["iteration"],
        structural_properties=["sparse"],
        extraction_method=ExtractionMethod.HUMAN,
        extractor="v010-smoke",
        confidence=1.0,
    )


doc = ParsedDocument(
    work_id="w1",
    asset_id="a1",
    source_format="tex",
    parser="smoke",
    sections=[DocumentSection(id="s1", order=0, text="We solve a sparse optimization problem using an iterative algorithm.")],
    equations=[EquationOccurrence(id="e1", section_id="s1", latex="x+y=z")],
)
intel = analyze_document(doc)
assert intel.section_count == 1
p1 = problem("p1", "w1", "Minimize lattice energy")
p2 = problem("p2", "w2", "Find a minimum-cost ecological allocation")
assert assess_problem_quality(p1).completeness > 0
structure = discover_structure([p1, p2])
assert structure.pair_count == 1
candidates = rank_cross_domain_candidates(
    structure.similarities,
    {"p1": "physics", "p2": "ecology"},
    minimum_score=0.1,
)
assert candidates
left = fingerprint_expression(MathExpression(id="m1", work_id="w1", latex="x+y=z"))
right = fingerprint_expression(MathExpression(id="m2", work_id="w2", latex="a+b=c"))
math_similarity = compare_fingerprints(left, right)
assert math_similarity.relation_match == 1
coverage = build_coverage_report([
    {"discipline": "physics", "year": 1995, "provider": "openalex"},
    {"discipline": "ecology", "year": 2025, "provider": "crossref"},
])
assert coverage.total_works == 2
priorities = ActiveRetrievalPlanner().prioritize([
    {"scope_id": "history-gap", "coverage_gap": 0.8, "historical_gap": 0.9, "uncertainty": 0.7, "novelty": 0.4}
])
feedback = FeedbackLoop().decide(
    [DiscoveryYield(iteration=1, retrieved=100, new_works=20)],
    priorities,
    strata_stable=False,
)
assert feedback.action.value != "saturated"
assert len(default_high_recall_cascade().steps) >= 5
manifest = ResearchManifest(
    id="smoke-manifest",
    corpus_release="smoke",
    extractor=SoftwareComponent(name="human", version="1"),
)
assert len(manifest.fingerprint()) == 64
print("v0.10 pre-quantum analysis smoke passed")
PY

python -m discovery.cli generate-schemas --output-dir "$SCHEMA_DIR" >/dev/null
SCHEMA_COUNT="$(find "$SCHEMA_DIR" -name '*.schema.json' | wc -l | tr -d ' ')"
if [[ "$SCHEMA_COUNT" -lt 100 ]]; then
  echo "expected at least 100 schemas, got $SCHEMA_COUNT" >&2
  exit 1
fi

DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic upgrade head
REVISION="$(DISCOVERY_DATABASE_URL="sqlite:///$MIGRATION_DB" alembic current 2>/dev/null)"
case "$REVISION" in
  *0004*) ;;
  *) echo "expected alembic revision 0004, got: $REVISION" >&2; exit 1 ;;
esac

printf 'scientific-discovery v0.10 pre-quantum structure discovery smoke test passed\n'
