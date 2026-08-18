# Operational Research Engine v0.3

## What can run now

- import the v0.1 ontology scaffold idempotently;
- import native OBO, SKOS RDF/XML, and normalized JSONL vocabulary records by release without strengthening native relations;
- compile individual concepts, concept sets, or discipline subtrees into query plans;
- split plans into replayable query batches;
- discover gateway feed402 operations;
- run federated gateway search and persist retrieval runs/hits/works;
- resume completed query batches without re-running completed queries;
- record per-query saturation observations and optionally stop on audited low novelty;
- optionally collect citations and asset locations through provider capabilities;
- rights-check, optionally retain, and parse discovered assets;
- parse local plain text, HTML, JATS, TEI, and LaTeX;
- extract equation occurrences and conservative mathematical features;
- run a transparent ProblemInstance extraction baseline;
- persist problems both as full payloads and normalized evidence/math/method relations;
- persist cross-domain candidates and candidate family membership as hypotheses;
- create deterministic offline semantic baselines and exact vector searches;
- calculate structural similarity, clustering inputs, co-citation, and bibliographic coupling;
- generate cross-domain candidates under explicit thresholds;
- mine observed corpus vocabulary missing from the known ontology vocabulary;
- import a versioned quantum catalog and screen problems without claiming advantage;
- calculate benchmark retrieval/extraction/agreement/completeness metrics;
- record coverage snapshots, experiments, and human review events.

## Rights boundary

Asset location is not permission. `decide_asset_action()` returns allowed only when an asset is retrievable and the requested right is explicitly `allowed`. The rights-aware fetcher requires explicit TDM permission and can separately require retention permission.

## Resumability

`ResearchHarvestEngine` checkpoints each query in a query batch. Re-running the same deterministic batch recovers completed query work rather than paying/retrieving it again. Provider-native deep cursors remain an upstream gateway concern; this layer handles downstream batch resumability. Optional saturation stopping records retrieved count, newly discovered unique works, cumulative works, and novelty rate for each processed query so the stopping decision is inspectable rather than implicit.
