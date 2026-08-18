# Quantum Algorithm Discovery Research Charter

## Primary research question

What recurring computational and mathematical problem structures occur across scientific disciplines, and which of those structures represent plausible opportunities for quantum algorithms not adequately covered by existing computational methods?

## Research questions

### RQ1 — Recurring computational structures

What computational problem classes recur across otherwise disparate scientific disciplines?

### RQ2 — Vocabulary-independent similarity

Can computational similarities be detected when two fields use substantially different terminology?

### RQ3 — Mathematical recurrence

What mathematical structures recur across literatures that have weak semantic or citation connectivity?

### RQ4 — Known quantum mappings

Which recurring scientific problem structures map naturally to known quantum computational primitives or algorithms?

### RQ5 — Advantage validation

Which apparent quantum mappings survive scrutiny against:

- classical baselines;
- access-model assumptions;
- data-loading costs;
- state preparation;
- output/readout costs;
- dequantization;
- complexity assumptions;
- hardware and noise constraints?

### RQ6 — Structural gaps

Which scientifically important recurring computational structures are not adequately covered by known quantum algorithm families?

### RQ7 — Algorithm discovery

Can AI systematically propose, test, reject, refine, and eventually construct algorithmic approaches for high-value structural gaps?

## Core methodological principle

We do not search science for things that merely look quantum.

We first identify recurring computational and mathematical structures across science independently of quantum relevance.

Only afterward do we compare those structures with the quantum algorithmic landscape.

## Core research object

The primary research object is not the paper.

The paper is evidence.

The principal object is a structured representation of the computational or mathematical problem being addressed by the work.

Initially this object is called `ProblemInstance`.

## Important non-equivalences

The project must never silently assume:

- same vocabulary = same problem;
- mathematical resemblance = computational equivalence;
- representational compatibility = algorithm applicability;
- quantum algorithm applicability = quantum advantage;
- asymptotic quantum advantage = end-to-end advantage;
- interesting analogy = scientific discovery.

## Negative results

Negative findings are first-class research outputs.

Examples include:

- strong classical algorithms dominate;
- data-loading eliminates theoretical advantage;
- an apparent quantum advantage is dequantized;
- input-access assumptions are unrealistic;
- a structural analogy does not survive formalization;
- the problem is not computationally difficult in the relevant regime.

## Separation of infrastructure and research

`feed402` and `x402-research-gateway` provide generic research-source infrastructure.

This repository owns downstream scientific representation, analysis, and discovery.

Provider-specific transport, payments, API routing, and generic source access should not be duplicated here except where temporary fixtures are required for development.

## Long-term pipeline

The intended research pipeline is:

1. Discover and retrieve scientific sources.
2. Normalize scholarly identity and provenance.
3. Represent computational problems as `ProblemInstance` objects.
4. Extract mathematical and algorithmic structure.
5. Detect recurring problem structures across disciplines.
6. Form cross-domain `ProblemFamily` candidates.
7. Map those structures against known quantum algorithms and primitives.
8. Test apparent opportunities against classical baselines, access assumptions, dequantization, and end-to-end costs.
9. Identify unresolved structural gaps.
10. Use AI-assisted search to propose and evaluate algorithmic constructions for the strongest gaps.

## Current milestone

**Campaign 001 — Cross-Disciplinary Pilot**

The current goal is to test the pre-quantum pipeline on a frozen 24-work cross-disciplinary sample and record retrieval, identity, asset, parsing, problem-extraction, mathematics, and structural-comparison failures.

v0.11 is complete. v0.12 will use Campaign 001 results to define the benchmark and repair priorities.
