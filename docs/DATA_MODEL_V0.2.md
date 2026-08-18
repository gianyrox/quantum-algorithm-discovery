# Data Model v0.2

## Canonical identity

The storage layer separates a conceptual `Work` from `WorkVersion` and provider identifiers. This prevents preprints, revisions, publisher manifestations, and provider records from being destructively collapsed.

Core corpus tables include `work`, `work_version`, `work_identifier`, `author`, `organization`, `authorship`, `asset`, and `citation`.

## Provenance

Retrieval is persisted as `retrieval_run` plus ordered `retrieval_hit` rows. Provider rank, provider score, fused rank, raw record, and provenance are separate fields. A gateway failure is therefore not representable as an empty successful result without explicitly doing so upstream.

`provenance_assertion` is intentionally assertion-level: a normalized fact may keep the provider and evidence that asserted it.

## Scientific representation

`problem_instance` stores the full validated `ProblemInstance` JSON and indexes the most important selection fields. Mathematical and methodological entities have separate tables so later normalized objects can be linked to many problems.

## Discovery layer

Similarity runs are versioned separately from individual similarity edges. Problem families and candidates are persistent research objects rather than transient notebook output.

## Quantum layer

Quantum primitives, algorithms, and matches are independent of the general scientific corpus. This preserves the methodological rule that scientific structure is identified before quantum relevance is evaluated.

## Database strategy

SQLite is the default development database. The SQLAlchemy schema is written to remain portable to PostgreSQL. PostgreSQL/pgvector should be introduced only when corpus scale or vector retrieval makes it operationally necessary.
