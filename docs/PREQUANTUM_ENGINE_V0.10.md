# v0.10 Pre-Quantum Scientific Structure Discovery Engine

## Scope

This release combines the intended v0.5-v0.10 capability milestones into one integrated pre-quantum release. It builds the machinery needed to retrieve real scientific literature, preserve scientific documents, extract computational problems, represent mathematics, discover recurring structures, and iteratively improve retrieval coverage.

## v0.5 capability: scientific campaign execution

v0.4 already established direct and gateway provider execution, resumable harvesting, canonical works, assets, rights, identity evidence, integrity evidence, and durable jobs. v0.10 treats that as the corpus substrate and adds explicit high-recall cascade planning, adaptive retrieval budgets, discovery iterations, and versioned feedback decisions.

The default cascade is:

1. controlled vocabulary;
2. lexical synonyms/abbreviations/method and model names;
3. historical terminology;
4. backward/forward citation expansion;
5. semantic retrieval as an additional view;
6. provider-published related works.

Semantic retrieval does not replace field-native lexical retrieval.

## v0.6 capability: document intelligence

`ParsedDocument` now has explicit references, citation mentions, and metadata in addition to sections, equations, tables, and figures. `DocumentIntelligence` summarizes structure without flattening source content and identifies math-dense, likely-problem, and likely-method sections for downstream extractors.

Reference utilities conservatively recover DOI, PMID, and arXiv identifiers from reference text while preserving the original reference string.

## v0.7 capability: problem extraction and evaluation

`ProblemInstance` remains backward compatible while adding field-addressable `EvidenceSpan` and `FieldConfidence` records. `ProblemExtractorEnsemble` runs multiple extractors without collapsing disagreement into consensus. `ProblemQualityReport` measures field completeness and evidence coverage and keeps missing high-value fields visible.

Extraction evaluation supports task-family accuracy and precision/recall for operations and structural properties. The first production baseline remains intentionally transparent and low-confidence; scientific quality must be established empirically against human annotation.

## v0.8 capability: mathematical structure engine

The engine now supports:

- raw source, LaTeX, presentation/content MathML, semantic form, AST, operator graph, symbol grounding, alpha-normalized form, units and CAS variants;
- shallow deterministic LaTeX tokenization and relation-aware ASTs as one transparent baseline view;
- exact and alpha-normalized fingerprints;
- token multiset and operator signatures;
- multi-view mathematical similarity with explicit notes that resemblance is not proof of equivalence;
- a benchmark schema for calibrated mathematical-similarity evaluation.

The shallow parser is not a CAS and does not claim complete LaTeX semantics.

## v0.9 capability: cross-disciplinary structure discovery

`MultiViewSimilarity` keeps task, mathematical, operator, constraint, topology, stochastic, complexity, method, semantic, lexical, and citation views separable. Its aggregate score penalizes lexical and citation connectivity instead of treating them as structural evidence.

The release includes:

- pairwise structure discovery;
- a deterministic signature index for local candidate generation;
- configurable connected-component family construction;
- ranked cross-domain candidates;
- explicit relation hypotheses such as shared mathematical form, analogy, lexical resemblance, or unresolved;
- reviewable negative/rejection reasons.

Historical transmission and independent rediscovery are representable relation types but are never inferred automatically by the baseline classifier because those claims require external historical evidence.

## v0.10 capability: coverage and feedback

Coverage is stratified across discipline, decade, language, document type, provider, and access status. Stopping uses `DiscoveryYield`, which tracks new works, terminology, concepts, citation edges, and problem signatures.

`AuditedSaturationPolicy` requires both low recent novelty and stable coverage strata. `ActiveRetrievalPlanner` then allocates attention using uncertainty, novelty, coverage gap, historical gap, and provider disagreement. `FeedbackLoop` chooses among continuation, term expansion, citation expansion, provider expansion, historical targeting, gap review, and saturation.

No fixed corpus-size target is encoded into stopping logic.

## Reproducibility

`ResearchManifest` fingerprints the configuration of the derived research artifact, including corpus release, ontology releases, query-plan version, extractor, mathematical normalization, embedding model, similarity configuration, clustering configuration, and source-code revision.

This makes structural results comparable across reruns instead of allowing silent model or corpus drift.
