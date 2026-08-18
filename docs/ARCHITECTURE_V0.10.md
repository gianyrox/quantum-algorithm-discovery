# Scientific Discovery v0.10 Architecture

v0.10 is the complete pre-quantum scientific structure discovery engine. Its active research pipeline ends at reviewed cross-disciplinary structure hypotheses and retrieval feedback. Existing quantum modules from earlier versions remain import-compatible, but v0.10 neither calls them nor uses quantum relevance to shape scientific retrieval, extraction, similarity, clustering, or stopping decisions.

## Research pipeline

```text
native vocabularies + scientific source registry
                |
                v
field-native retrieval language
                |
                v
controlled-vocabulary / lexical / historical retrieval
                |
                v
provider federation + canonical Work identity
                |
                +--> citation expansion
                +--> unknown-vocabulary feedback
                |
                v
rights-aware Asset acquisition
                |
                v
ParsedDocument
  |- sections and hierarchy
  |- equations
  |- figures
  |- tables
  |- references
  `- citation mentions
                |
                v
DocumentIntelligence
                |
                v
0..N ProblemInstance objects
  |- computational contract
  |- mathematical objects and operators
  |- methods and baselines
  |- scale and complexity claims
  |- evidence spans and field confidence
  `- unresolved questions
                |
                v
MathematicalFingerprint + structural signatures
                |
                v
MultiViewSimilarity
                |
                v
ProblemFamily + cross-domain relation hypotheses
                |
                v
stratified coverage + audited saturation
                |
                v
active retrieval priority + feedback decision
                |
                `------------> next retrieval iteration
```

## Architectural invariants

1. Papers remain evidence; `ProblemInstance` is the primary derived computational research object.
2. Retrieval does not search for quantum relevance.
3. Native vocabularies are preserved as native structures. Query compiler artifacts are not ontology truth.
4. Multiple mathematical views coexist; no normalized representation is treated as uniquely correct.
5. Similarity is multi-view and explainable. One embedding never decides structural equivalence.
6. Cross-domain matches are hypotheses requiring review, not proof of equivalence or independent rediscovery.
7. Absence of retrieval is not evidence of absence. Coverage is stratified by field, time, language, provider, document type, and access.
8. Saturation requires marginal novelty to stabilize and coverage strata to be stable.
9. Unknown corpus language feeds a reviewable retrieval-vocabulary loop; it does not silently mutate authoritative ontologies.
10. Every experiment can be pinned by a `ResearchManifest` describing corpus, ontology, extractor, normalization, embedding, similarity, clustering, and source-code versions.

## Persistence added in revision 0004

- `document_intelligence`
- `problem_quality`
- `math_fingerprint`
- `structural_similarity`
- `cross_domain_relation`
- `discovery_iteration`
- `retrieval_feedback`
- `research_manifest`

These tables are additive to the canonical work/document/problem schema built in revisions 0001-0003.
