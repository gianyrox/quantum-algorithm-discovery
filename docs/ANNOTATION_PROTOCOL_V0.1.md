# Problem Annotation Protocol v0.1

## Objective

Given a scientific work, identify and represent the computational problem or problems that the work actually addresses.

Do not merely summarize the paper.

The goal is to recover computational and mathematical structure in a form that can eventually be compared across disciplines.

## Unit of annotation

One scientific work may contain:

- zero computational problems;
- one computational problem;
- several distinct computational problems.

Each materially distinct problem should become a separate `ProblemInstance`.

A paper is evidence for a problem representation. The paper itself is not the problem representation.

## Step 1 — Identify the task

Ask:

> What must actually be computed, inferred, searched, simulated, optimized, estimated, predicted, classified, or controlled?

Assign the closest `task_family`.

Use `other` when a genuine computational problem exists but the current vocabulary does not fit.

Use `unknown` when the available evidence is insufficient.

Do not force every work into an existing category.

## Step 2 — Identify inputs

Record the information available to the solver.

Examples include:

- graphs;
- matrices;
- tensors;
- observations;
- time series;
- molecular configurations;
- probability distributions;
- differential equations;
- boundary conditions;
- experimental measurements;
- initial states;
- control parameters.

Do not infer an input that is unsupported by the work.

## Step 3 — Identify outputs

Record what the computation is expected to produce.

Examples include:

- an optimum;
- a configuration;
- an estimator;
- a probability;
- a trajectory;
- a classification;
- a control policy;
- an eigenvalue;
- an eigenvector;
- a simulated state;
- a reconstructed signal;
- a posterior distribution.

## Step 4 — Identify objective and constraints

Where relevant, separate:

- objective;
- hard constraints;
- soft constraints;
- penalties;
- regularizers;
- physical constraints;
- modeling assumptions.

Do not combine assumptions and constraints merely because both restrict the problem.

## Step 5 — Identify the state space and access model

Ask:

- What space does the problem live in?
- How is the input accessed?
- Is the full object explicitly available?
- Is access local, oracle-like, sampled, streamed, sparse, or implicit?
- Does the algorithm operate on raw observations or a transformed representation?

These distinctions will later matter for quantum-algorithm analysis.

## Step 6 — Identify mathematical structure

Record explicit mathematical objects such as:

- vectors;
- matrices;
- tensors;
- graphs;
- operators;
- Hamiltonians;
- differential equations;
- probability distributions;
- stochastic processes;
- manifolds;
- optimization landscapes;
- kernels;
- Markov chains;
- dynamical systems.

Prefer explicit source evidence over annotator inference.

## Step 7 — Identify operators and equations

Record important equations or operators that define the computational structure.

Examples include:

- matrix-vector multiplication;
- Laplacian operators;
- integral operators;
- transition operators;
- Hamiltonians;
- gradient operators;
- eigenvalue equations;
- differential equations.

Preserve the original mathematical statement when possible.

## Step 8 — Identify structural properties

Record properties that may influence algorithm design.

Examples include:

- sparsity;
- locality;
- symmetry;
- low rank;
- graph topology;
- conservation laws;
- convexity;
- non-convexity;
- multimodality;
- high dimensionality;
- ill conditioning;
- stochasticity;
- periodicity.

Do not claim a property unless supported by evidence or clearly marked as an inference.

## Step 9 — Identify algorithmic operations

Record recurring computational operations required by the problem or method.

Examples include:

- matrix-vector multiplication;
- sorting;
- graph traversal;
- numerical integration;
- sampling;
- gradient evaluation;
- linear solving;
- eigenvalue estimation;
- dynamic programming;
- message passing;
- optimization updates;
- Monte Carlo simulation.

These operations may later be more useful for cross-domain comparison than field-specific terminology.

## Step 10 — Identify known methods and baselines

Separate:

- method used in the work;
- alternative methods discussed;
- approximation methods;
- classical baselines;
- comparison methods.

Do not label something a baseline unless the source or annotation evidence supports that interpretation.

## Step 11 — Identify scale parameters

Record variables controlling computational size.

Examples include:

- number of vertices;
- number of particles;
- matrix dimension;
- number of samples;
- sequence length;
- time horizon;
- number of variables;
- grid resolution;
- state-space dimension.

Where the work uses a mathematical symbol, preserve it.

## Step 12 — Identify complexity claims

Record explicit claims about:

- time complexity;
- space complexity;
- query complexity;
- convergence;
- approximation error;
- sample complexity;
- scaling behavior.

Preserve assumptions associated with the claim.

Do not invent asymptotic complexity from runtime plots.

## Step 13 — Identify computational bottlenecks

Ask:

> What part of the problem becomes computationally difficult as scale increases?

Examples include:

- combinatorial search;
- matrix factorization;
- repeated simulation;
- rare-event sampling;
- memory consumption;
- long mixing time;
- ill conditioning;
- high-dimensional integration;
- exponential state spaces.

Distinguish reported bottlenecks from annotator hypotheses.

## Step 14 — Record assumptions and approximations

Preserve assumptions that materially affect the computational problem.

Examples include:

- independence assumptions;
- sparsity assumptions;
- equilibrium assumptions;
- smoothness;
- locality;
- Gaussian noise;
- stationarity;
- perturbative regimes;
- finite-size approximations.

Approximation methods should be represented separately when possible.

## Step 15 — Record evidence

Every non-obvious interpretation should eventually point to source evidence.

Preferred evidence locations include:

- abstract;
- introduction;
- methods;
- results;
- equation;
- figure;
- table;
- appendix;
- supplement.

The benchmark should make it possible to audit why an annotation exists.

## Step 16 — Preserve uncertainty

If the work does not make something clear, use:

- `null`;
- an empty collection;
- `unknown`;
- `unresolved_questions`.

Do not manufacture certainty merely to fill every schema field.

## Multiple computational problems

If a paper contains several genuinely different computational tasks, create several `ProblemInstance` records.

For example, one work may contain:

1. parameter estimation;
2. simulation;
3. optimization of an intervention.

These should not automatically be collapsed into one problem.

## Distinguish scientific domain from computational structure

Domain terminology is evidence and context, but it should not determine computational classification.

For example, the following could potentially share computational structure despite belonging to different fields:

- ecological equilibrium estimation;
- neural attractor analysis;
- chemical reaction-network steady states;
- economic equilibrium computation.

The annotation should preserve the domain while representing the computational structure independently.

## Annotation principle

The benchmark should measure extraction of computational structure, not fluency of scientific summarization.

## Current status

This is version 0.1.

The protocol is expected to change after annotation of the first deliberately cross-disciplinary pilot set.
