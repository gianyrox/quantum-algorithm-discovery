# Problem Extraction v0.10

## Target object

A `ProblemInstance` answers: **what computational problem is this work actually solving?** A work may contain zero, one, or many problem instances.

High-value fields include inputs, outputs, objective, constraints, state space, access model, data model, mathematical objects, operators, equations, structural properties, algorithmic operations, known methods, classical baselines, scale parameters, complexity claims, bottlenecks, assumptions, approximations, stochasticity, symmetry, sparsity, locality, graph structure, dimensionality, and conditioning.

## Evidence

v0.10 adds `EvidenceSpan` for field-specific evidence. An extraction can therefore say not just that a paper supports a `ProblemInstance`, but which document section and character span supports an objective, input, constraint, bottleneck, or other field. `FieldConfidence` lets extractors expose uncertainty field by field instead of hiding it behind one global score.

## Ensembles

`ProblemExtractorEnsemble` preserves extractor disagreement. The first baseline remains a transparent keyword/rule extractor; future local or remote LLM extractors can implement the same `ProblemExtractor` protocol. Ensemble outputs do not automatically become truth through voting.

## Evaluation

Evaluation includes task-family agreement and set-based precision/recall for algorithmic operations and structural properties. `ProblemQualityReport` separately measures completeness and evidence coverage. These metrics must be stratified by discipline and document type when enough benchmark data exists.

## Annotation target

The existing benchmark design remains: deliberately diverse scientific works, human annotations, zero-to-many problems per work, and iterative schema revision when fields are missing, ambiguous, conflated, or unnecessary.
