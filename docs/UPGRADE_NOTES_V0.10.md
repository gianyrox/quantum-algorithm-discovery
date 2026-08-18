# Upgrade Notes: v0.4 -> v0.10

v0.10 combines the planned v0.5-v0.10 pre-quantum milestones into one release.

## Added

- document references, citation mentions, and document-intelligence summaries;
- problem field evidence spans, field confidence, extraction ensembles, quality reports, and extraction evaluation;
- shallow LaTeX parsing, mathematical fingerprints, mathematical similarity and benchmark objects;
- multi-view problem similarity, structural family construction, relation hypotheses, cross-domain ranking, and local structural signature indexing;
- stratified coverage, audited saturation, active retrieval priority, retrieval feedback, historical vocabulary support, and explicit vocabulary-feedback states;
- high-recall retrieval cascade and adaptive retrieval budget objects;
- reproducibility manifests;
- iterative pre-quantum analysis orchestration;
- Alembic revision `0004` and eight new research tables;
- `discovery structure` CLI commands;
- generated schemas for all new public Pydantic research objects.

## Compatibility

All new fields on existing public Pydantic models have defaults. Existing v0.4 data remains readable. Revision 0004 is additive. Existing quantum modules are retained for backward compatibility but are not part of the v0.10 scientific structure discovery pipeline.
