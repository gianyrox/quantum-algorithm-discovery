# Cross-Disciplinary Problem Benchmark Design v0.1

## Purpose

The first benchmark is designed to test whether `ProblemInstance` can represent computational problems consistently across substantially different scientific disciplines.

This is not initially a quantum benchmark.

Quantum relevance must not be used as a paper-selection criterion.

## Pilot objective

The pilot should deliberately stress the representation.

We want papers that differ in:

- scientific vocabulary;
- mathematical language;
- data modality;
- scale;
- computational task;
- experimental versus theoretical setting;
- deterministic versus stochastic structure;
- continuous versus discrete structure;
- graph versus non-graph structure;
- optimization versus inference versus simulation versus other tasks.

## Initial pilot size

Target approximately 20 to 30 scientific works.

This is large enough to expose schema failures but small enough for careful human annotation.

The pilot is not intended to estimate population-level frequencies.

## Breadth-first selection

The pilot should span substantially different fields.

Initial target families include:

- mathematics and applied mathematics;
- theoretical or algorithmic computer science;
- physics;
- chemistry;
- materials science;
- molecular or systems biology;
- neuroscience;
- ecology;
- earth or climate science;
- astronomy;
- operations research;
- economics or quantitative social science;
- control or engineering.

These are sampling targets, not a final ontology of science.

## Selection independence from quantum computing

Do not preferentially select papers because:

- they mention quantum computing;
- their mathematical objects resemble known quantum algorithms;
- a quantum speedup is already known;
- they appear in quantum-adjacent fields.

The scientific benchmark should be constructed independently of the quantum target map.

## Desired computational diversity

Across the pilot, seek examples of:

- optimization;
- search;
- sampling;
- estimation;
- inference;
- simulation;
- control;
- inverse problems;
- eigenproblems;
- differential equations;
- stochastic processes;
- graph problems;
- rare-event problems;
- counting;
- integration;
- dynamical systems.

Do not force a quota when a field does not naturally provide one.

## Selection record

Every candidate work receives a `BenchmarkWork` record before annotation.

The selection record must preserve:

- source identity;
- field assignment;
- selection reason;
- selection method;
- availability;
- acceptance or rejection.

This allows the benchmark-construction process itself to be audited.

## Rejection

A candidate may be rejected because:

- the full scientific work cannot be accessed lawfully;
- the work contains no sufficiently identifiable computational problem;
- the work substantially duplicates an existing pilot example;
- the field assignment is inappropriate;
- the source is unsuitable for reliable annotation.

Rejection is preserved rather than deleting the candidate.

## Annotation independence

A paper's benchmark-selection metadata must not predetermine its `task_family`.

Annotators determine computational structure from the source evidence.

## Multiple problems per work

One selected work may produce zero, one, or several `ProblemInstance` annotations.

The benchmark must not require exactly one computational problem per paper.

## First evaluation question

The pilot should answer:

> What distinctions are missing, ambiguous, conflated, or unnecessary in `ProblemInstance` when it is applied to real scientific work across fields?

Schema revision is expected.

A schema change produced by evidence from the pilot is a successful research result, not a failure of the benchmark.

## Versioning

The initial pilot is benchmark version `0.1`.

Once the schema and annotation protocol stabilize, a later benchmark should separate:

- development data;
- held-out test data.

The first 20 to 30 works should primarily be treated as pilot/development material.
