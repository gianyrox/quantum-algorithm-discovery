# Scientific Discovery roadmap

## Current sequence

```text
v0.10  PRE-QUANTUM STRUCTURE ENGINE                 COMPLETE
  |
v0.11  GATEWAY-FIRST / FEED402 RESEARCH BOUNDARY   CURRENT
  |
v0.12  REAL-CORPUS BENCHMARK + FAILURE REPAIR
  |
v0.13  MEDIUM-SCALE CROSS-DISCIPLINARY CAMPAIGNS
  |
v0.14  VALIDATED PROBLEM FAMILIES + CANDIDATE DISCOVERY
  |
freeze pre-quantum discovery system
  |
separate quantum mapping and algorithm-discovery research
```

## v0.11 exit criteria

- gateway/feed402 is the only production external-research boundary;
- direct provider paths are absent from the active CLI and blocked by the default runtime factory;
- feed402 citations, rights, assets, execution provenance, receipt, and lineage parse natively;
- every gateway retrieval envelope is persisted and linked to `RetrievalRun`;
- campaign retrieval envelopes are linked to `CampaignRun`;
- campaign results record gateway URL, feed402 spec, manifest fingerprint, coverage context, and provenance counts;
- migration reaches Alembic `0005`;
- Campaign 001 runs through the gateway with no direct-provider fallback.

## After v0.11

### v0.12 — benchmark and repair

Run a deliberately diverse pilot corpus, manually inspect retrieval/parsing/problem/math failures, create benchmark annotations and known similar/dissimilar pairs, then improve the weakest components.

### v0.13 — medium campaigns

Scale from tens/hundreds of works to hundreds/thousands across intentionally different disciplines. Tune retrieval budgets, saturation, historical coverage, unknown-vocabulary feedback, and extraction reliability.

### v0.14 — candidate discovery

Construct and review recurring `ProblemFamily` objects and cross-domain relation hypotheses. Measure whether high structural similarity survives low lexical similarity and low citation connectivity.

### Later — quantum stage

Only after the pre-quantum system is frozen do reviewed problem structures enter quantum mapping. Quantum applicability, advantage, dequantization, access models, state preparation, readout, classical baselines, and hardware/resource constraints remain separate questions.

## Operating loop

`RUN -> MEASURE -> FIX -> RERUN`

Roadmap progress belongs in versioned docs, campaign manifests/results, benchmark artifacts, and issue tracking when a repository issue tracker is available. Chat transcripts are supporting research history, not the canonical project tracker.
