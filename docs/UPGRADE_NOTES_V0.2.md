# v0.2 Upgrade Notes

This upgrade turns the v0.1 problem-schema prototype into a complete research-engine skeleton with executable storage, ontology ingestion, retrieval, structural analysis, quantum target representation, evaluation, and experiment tracking.

## Added

- SQLAlchemy canonical research database and Alembic baseline migration.
- Work/WorkVersion/identifier/asset/citation/retrieval/provenance persistence.
- Idempotent importer for the existing ontology v0.1 CSV package.
- Transparent high-recall ontology query compiler.
- Provider-neutral retrieval models and interfaces.
- `x402-research-gateway` client boundary plus offline fixture provider.
- Structured document models and parser registry.
- Multi-view mathematics models.
- Problem-family model and extractor protocol.
- Transparent cross-domain structural-similarity baseline.
- Cross-domain candidate scoring.
- Quantum primitive/algorithm/match schemas and conservative structural screen.
- Extraction evaluation metrics.
- Experiment tracking.
- CLI groups for database, ontology, corpus, retrieval, analysis, quantum, and experiments.

## Preserved

The existing `ProblemInstance`, benchmark schemas, validation commands, research charter, annotation protocol, benchmark design, ontology package, and research reports remain compatible.

## Deliberately not implemented yet

- production full-text parsers;
- LLM extraction;
- embeddings or a fixed embedding provider;
- a vector database;
- a graph database;
- large-scale corpus harvesting;
- automatic quantum-advantage claims;
- algorithm generation agents.

The interfaces and persistence points for these are present. Their implementations should be driven by benchmark evidence and by the evolving gateway capabilities.
