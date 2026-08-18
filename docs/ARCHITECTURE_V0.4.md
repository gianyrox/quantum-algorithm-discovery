# Scientific Discovery Architecture v0.4

## Stable center

The stable center is a canonical, provenance-bearing research corpus rather than any particular provider, embedding model, graph engine, or database deployment.

```text
provider registry / native vocabulary
        |
        v
transparent QueryPlan + campaign intent
        |
        v
gateway federation OR direct provider adapters
        |
        v
request audit + raw response + retrieval run
        |
        v
identity evidence -> Work -> WorkVersion
        |                  |
        |                  +-> citations / relations / integrity
        v
rights-bearing Asset -> acquired bytes -> ParsedDocument
        |
        v
MathExpression + ProblemInstance
        |
        v
structural views + lexical/semantic/citation views
        |
        v
CrossDomainCandidate -> reviewed ProblemFamily
        |
        v
quantum target screening -> advantage/dequantization checks
        |
        v
reviewed research gap -> algorithm hypothesis/evaluation
```

## Provider boundary

`x402-research-gateway` owns source-specific access/normalization and exposes provider capabilities. Scientific Discovery consumes that interface but also has direct adapters for operational independence, single-provider bulk-like paging, fixtures, and cases where forcing local ingestion through a payment hop would be counterproductive.

Provider data is never trusted merely because two providers agree. Raw records, provider rank, provider assertions, and request provenance remain inspectable.

## Canonical identity

The corpus distinguishes:

- a scientific `Work`;
- provider or repository versions of that work;
- manifestations/assets carrying content;
- external identifiers used to find evidence about the work.

Exact identifiers and provider-published relations can connect these layers. Fuzzy title/author similarity may create review evidence but must not silently merge works.

## Durable execution

There are three complementary durable units:

1. `RetrievalRun` records one executed query/response.
2. `ProviderHarvestCheckpoint` records a cursor/offset page and makes large harvests resumable.
3. `ResearchCampaign` records scientific search intent and one or more campaign runs.

Document work enters a separate idempotent `ProcessingJob` queue. SQLite is intentionally treated as a single-worker local queue. PostgreSQL can later add transactional multi-worker claiming without changing the job record model.

## Rights and raw bytes

Asset discovery and asset acquisition are separate operations. A discovered URL is not permission. Automated acquisition requires explicit TDM permission; persistent raw storage also requires explicit retention permission.

Large and raw bytes live behind the `ObjectStore` contract. The default local implementation is content-addressed and immutable by digest.

## Deliberate non-choices

v0.4 still does not require Kafka, Kubernetes, microservices, Neo4j, a remote ANN database, or one mandatory embedding model. The research abstractions should survive later scaling choices.
