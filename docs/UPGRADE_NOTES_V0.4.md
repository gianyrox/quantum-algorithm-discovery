# Upgrade Notes v0.4

## Headline

v0.4 adds the real-data execution layer on top of the validated v0.3 research architecture.

## Major additions

- resilient HTTP execution with retry/rate-limit handling and redacted request audits;
- direct OpenAlex, Crossref, Europe PMC, and arXiv adapters;
- client-side direct federation with provider provenance preserved;
- provider-native resumable deep harvest;
- gateway manifest, sync, coverage, identity, integrity, and signed-cursor harvest operations;
- provider capability snapshots;
- identity assertion ingestion with conservative alias attachment;
- integrity assertion persistence;
- citation-edge staging until canonical endpoints exist;
- canonical `Work -> Asset -> Document -> ProblemInstance` processing;
- rights-aware asset selection/acquisition with content-addressed storage;
- durable research campaigns;
- durable local processing queue and worker;
- deterministic corpus export;
- expanded operational coverage metrics;
- Alembic revision `0003`;
- v0.4 smoke test and post-upgrade validation script.

## Compatibility

The v0.3 `process-file` path remains for backward compatibility and fixtures, but new real-data workflows should use canonical processing.

Existing v0.1 ontology data remains a seed scaffold. v0.4 does not reinterpret generated seed terms as authoritative native vocabulary.

## Validation target

`bash scripts/post_upgrade_v04.sh` installs the editable package and runs package-version validation, the complete test suite, Ruff, strict mypy, and the canonical v0.4 smoke test.
