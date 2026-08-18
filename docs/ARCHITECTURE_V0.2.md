# Scientific Discovery Architecture v0.2

## Purpose

This repository is the downstream research engine. `feed402` defines generic evidence/provenance/rights semantics, and `x402-research-gateway` supplies federated source access. This repository persists scientific objects and computes representations, similarities, families, quantum mappings, and discovery candidates.

## Boundary

The gateway owns provider transport, upstream normalization, source capability discovery, rights-aware location discovery, and provider-asserted relations.

Scientific Discovery owns persistent corpus identity, document parsing, problem representation, mathematics, cross-domain structure, evaluation, experiments, quantum target modeling, and derived research hypotheses.

## Layers

1. `storage` — canonical relational persistence and migrations.
2. `corpus` — works, versions, identifiers, authors, assets, citations, provenance.
3. `ontology` — seed/native vocabularies and transparent lexical query compilation.
4. `retrieval` — provider-independent queries, gateway boundary, retrieval runs and hits.
5. `documents` — parsed structured documents, sections, equations, figures, tables.
6. `problems` — `ProblemInstance`, extraction contracts, candidate `ProblemFamily` objects.
7. `mathematics` — multi-view expressions and mathematical structures.
8. `analysis` — transparent structural baselines, later embeddings/graphs/clustering.
9. `discovery` — cross-domain candidates and ranking.
10. `quantum` — primitives, algorithms, access/resource assumptions, structural matching.
11. `evaluation` — benchmark schemas and extraction metrics.
12. `experiments` — reproducible run configuration, metrics, artifacts.
13. `pipeline` — lightweight stage orchestration without committing to distributed infrastructure.
14. `ai` — interfaces and hypothesis schemas for later AI-guided algorithm discovery.

## Data flow

Scientific sources -> gateway/provider -> RetrievalRun -> Work/WorkVersion -> Asset/Document -> ProblemInstance + MathExpression -> similarities -> ProblemFamily -> cross-domain candidates -> quantum structural screen -> reviewed opportunities/gaps.

## Principles

- Provider disagreement survives normalization.
- Work identity is not guessed from title alone.
- Raw provider records are retained with normalized views.
- The ontology v0.1 package is a retrieval seed, not authoritative truth.
- Query generation is field-native and high recall before quantum relevance is considered.
- Structural resemblance is evidence for review, not proof of equivalence.
- Quantum compatibility is not quantum advantage.
- Negative results and unresolved uncertainty are first-class outputs.
- No provider-specific logic should leak into scientific representation modules.
- Do not commit to a vector database, graph database, or embedding model before benchmarks justify it.
