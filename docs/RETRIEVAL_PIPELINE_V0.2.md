# Retrieval Pipeline v0.2

## Four searches

The project uses four conceptually different searches.

1. Scientific retrieval: find the literature using field-native terminology and high recall.
2. Scientific problem extraction: determine what computational problem each work is actually solving.
3. Cross-domain structural search: find recurring computational/mathematical structures across weakly connected fields.
4. Quantum target search: evaluate whether discovered structures are covered by known quantum methods, transferable, structurally extensible, genuine algorithmic gaps, negative cases, or unresolved.

Quantum terms do not drive stage 1 unless the scientific field itself is quantum computing.

## Stage 1 query cascade

The intended retrieval cascade is controlled vocabulary -> lexical variants -> provider-native search -> federated search -> citation expansion -> field-aware reranking/relevance feedback -> audited stopping.

The v0.2 implementation provides the first transparent lexical query compiler from ontology concepts. It keeps every selected clause and term type in a `QueryPlan`, so retrieval is reproducible and reviewable.

Dense search and graph expansion are intentionally separate later stages rather than silently mixed into the initial query.

## Gateway boundary

`GatewayProvider` is the production-facing adapter for `x402-research-gateway`. It parses additive feed402/gateway fields without importing gateway implementation code.

`FixtureProvider` provides deterministic offline retrieval for tests and early benchmark work.

## Persistence

Every executable search creates a `RetrievalRun`, persists provider reports and raw hits, then upserts normalized works without discarding provider records.
