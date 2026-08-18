# v0.4 Limits and Scientific Guardrails

v0.4 aggressively builds execution software without pretending the scientific research is already solved.

## Retrieval limits

- Four direct scholarly adapters are not complete coverage of science.
- Provider metadata, pagination, availability, and policies change; provider-specific contract monitoring remains necessary.
- Gateway paid endpoints may require an external x402-capable payment environment. Scientific Discovery does not custody a wallet.
- A zero-result provider response is not evidence that a field has no relevant work.
- Saturation is an audited stopping heuristic, not mathematical proof of corpus completeness.

## Identity and evidence limits

- Provider identity assertions can be wrong or incomplete.
- Fuzzy similarity never auto-merges works.
- Citation endpoints that cannot yet be resolved remain external assertions rather than fabricated canonical edges.
- Absence of an integrity assertion is unknown, not safe/clean.

## Rights limits

- Open access, retrievability, metadata licensing, redistribution, TDM, model training, and retention are separate permissions.
- Unknown permission is not permission.
- Direct adapters deliberately default content-use rights to unknown unless explicit machine-readable evidence is available.

## Extraction limits

- The transparent `ProblemInstance` extractor remains a plumbing/evaluation baseline.
- Parsed mathematical syntax is not yet semantic mathematical equivalence.
- Hashing embeddings and current similarity weights are baselines, not scientific conclusions.
- Tables, figures, diagrams, chemistry structures, and difficult PDF layouts still need richer extraction paths.

## Discovery limits

- Structural similarity is not computational equivalence.
- Computational equivalence is not quantum applicability.
- Quantum applicability is not quantum advantage.
- Asymptotic speedup is not end-to-end usefulness.
- Cross-domain candidates require historical/citation/domain review before being treated as independent rediscovery or transferable structure.

## Scale limits

The architecture can migrate toward PostgreSQL, external object storage, ANN indexes, and distributed workers, but v0.4 intentionally does not require them. Large-scale ingestion should follow measured retrieval and extraction evaluation rather than precede it.
