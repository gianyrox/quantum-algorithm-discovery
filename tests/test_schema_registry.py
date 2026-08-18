from discovery.schema_registry import SCHEMA_MODELS


def test_schema_registry_contains_major_research_objects() -> None:
    for name in (
        "problem-instance",
        "query-batch",
        "quantum-catalog",
        "coverage-snapshot",
        "unknown-vocabulary-candidate",
    ):
        assert name in SCHEMA_MODELS
