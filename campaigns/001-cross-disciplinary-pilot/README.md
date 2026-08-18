# Campaign 001 — Cross-Disciplinary Pilot

Status: active.

## Purpose

Test the pre-quantum discovery pipeline on real cross-disciplinary literature. The pilot is for failure discovery and measurement, not quantum mapping.

## Sample

- 24 frozen works
- 8 sampling strata
- 3 works per stratum
- quantum-blind selection
- frozen selection file: `selected_works.json`
- source corpus snapshot: `corpus_snapshot.json`

Sampling strata:

- seismic inverse problems
- ecological dynamics
- genomics and sequence analysis
- fluid dynamics and PDE simulation
- operations research
- epidemiological inference
- materials microstructure
- econometrics

## Pipeline

```text
retrieval
-> provenance
-> identity
-> asset discovery
-> acquisition
-> documents
-> ProblemInstance extraction
-> mathematics
-> structural comparison
-> coverage and failure report
```

## Current findings

### C001-F001

Retrieval persistence encountered duplicate deterministic `Work.id` values. A local repository upsert fix was applied for the pilot. The transaction-state follow-up remains a v0.12 item unless it blocks the run.

### C001-F002

The first corpus snapshot contains 66 persisted works but 0 identifiers, 0 assets, and 0 citations. Federated retrieval currently persists usable work records without enough downstream identity or asset state.

### C001-F003

The durable queue can represent `identity_resolution` and `asset_discovery` jobs, but the local worker intentionally claims only `asset_acquisition`. Provider-side identity and asset stages therefore require gateway orchestration and are not executed by `queue work-once`.

The initial identity probe was not executed; it remained pending. This is an orchestration gap, not evidence that identity resolution itself failed.

## Current step

Resolve identity for one frozen work through the gateway boundary, then test rights-aware asset discovery before scaling acquisition across the frozen sample.

## Rules

- no quantum mapping during Campaign 001
- do not silently replace frozen works
- preserve retrieval and feed402 provenance
- preserve acquisition and parser failures
- do not fill unsupported scientific fields
- complete the first run before broad repair
