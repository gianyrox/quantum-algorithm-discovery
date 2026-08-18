# Search Method v0.3

## Search 1: scientific retrieval

Input: a discipline, concept, or field-native retrieval target.

The ontology layer compiles transparent lexical clauses with source concept, term type, weight, and provenance. Modes are `precision`, `balanced`, and `high_recall`. Historical terms can be included explicitly. Related-concept traversal is opt-in and auditable.

Long OR plans are split into bounded `QueryBatch` queries. Each query is a separate `RetrievalRun`. This makes provider differences, failures, costs, and marginal recall measurable rather than hidden in one giant request.

Gateway federation may combine providers, but provider rank/raw records remain distinct. Works are deduplicated conservatively by exact identifiers. Similar title evidence is only `possible_same_work`.

Citation expansion and asset discovery are optional retrieval stages. Empty provider results, unsupported capabilities, and failures must remain distinguishable. Saturation stopping is optional and empirical: the engine records marginal new unique works for each bounded query and can stop only under an explicit configured policy.

## Search 2: computational problem extraction

The system asks: **what computational problem is this work actually solving?**

`ProblemInstance` preserves task, inputs, outputs, objectives, constraints, state/access/data models, mathematical objects, operators, equations, structural properties, algorithmic operations, known methods, classical baselines, scale parameters, complexity claims, bottlenecks, assumptions, approximations, evidence, confidence, and unresolved questions.

The included keyword extractor is intentionally a low-confidence baseline used to exercise pipelines. Human annotations are the initial gold standard.

## Search 3: cross-domain structural discovery

Problems are compared with multiple separable channels: lexical, semantic, task, mathematical, operator, constraint, topology, stochastic, complexity, method, and citation connectivity.

A particularly interesting candidate has:

- high structural similarity;
- different disciplines;
- low lexical similarity;
- low citation connectivity.

That pattern is a candidate for review, not proof of equivalence or independent discovery.

## Search 4: quantum target search

Only reviewed scientific structures enter quantum screening. A structural match is separately evaluated for representation, access model, state preparation, data loading, readout, classical baseline strength, dequantization, end-to-end complexity, and hardware/noise assumptions.

Possible outputs remain A established, B domain transfer, C structural extension, D algorithmic gap, E negative, or U unresolved. The baseline matcher deliberately produces unresolved results until evidence supports a stronger category.
