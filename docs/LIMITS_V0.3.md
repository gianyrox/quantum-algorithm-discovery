# v0.3 Limits and Intentionally Unfinished Work

v0.3 builds software architecture aggressively, but it does not pretend unvalidated science or unavailable infrastructure already exists.

## Not yet scientifically validated

- The transparent keyword `ProblemInstance` extractor is a plumbing/evaluation baseline, not a production scientific extractor.
- Hashing embeddings are deterministic offline baselines, not a claim about the best semantic representation.
- Structural similarity weights are starting hypotheses and must be benchmarked.
- Automatically clustered families and cross-domain candidates require human/domain review.
- Quantum structural matches remain unresolved until classical, access, dequantization, resource, and end-to-end checks are completed.

## Not yet supplied as research data

- No authoritative quantum algorithm catalog is fabricated by the software package.
- Generic OBO, SKOS RDF/XML, and normalized JSONL import is implemented, but source-specific download/version/licensing connectors still need to be added per native vocabulary.
- OWL/Turtle and source-specific semantics that exceed the normalized access surface must be preserved through future native-serialization adapters rather than approximated.
- Historical terminology depth depends on the source vocabularies actually imported.

## Scale deferred deliberately

- No mandatory ANN service yet; exact vector search is sufficient for pilots.
- No mandatory graph database yet; relational edges and exact graph routines are sufficient for pilots.
- No distributed scheduler or streaming bus yet.
- No 100k/100M paper bulk run should begin until retrieval and extraction evaluation gates are passing.

## Gateway dependency

Live federated retrieval requires a reachable `x402-research-gateway`. Offline fixtures and generic direct JSON-provider boundaries keep local development independent of gateway deployment.
