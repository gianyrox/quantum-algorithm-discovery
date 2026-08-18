# Scientific Discovery Architecture v0.3

## System boundary

`feed402` defines portable citations, rights, capabilities, assets, execution provenance, and derivation lineage. `x402-research-gateway` owns source discovery, provider adapters, federated access, provider-native normalization, identity evidence, citation traversal, and rights-aware source locations.

Scientific Discovery is the persistent downstream research engine. It owns corpus construction, scientific-document representation, computational-problem extraction, mathematics, structural comparison, cross-domain discovery, evaluation, quantum target modeling, and AI-guided research hypotheses.

## End-to-end data path

    source registry / native vocabulary
        -> transparent QueryPlan
        -> bounded QueryBatch
        -> gateway/provider retrieval
        -> RetrievalRun + RetrievalHit + checkpoints
        -> Work / WorkVersion / identifiers / assets / citations
        -> lawful document bytes
        -> ParsedDocument
        -> MathExpression + ProblemInstance
        -> embeddings + structural features + citation graph
        -> similarities / clusters / CrossDomainCandidate / ProblemFamily
        -> quantum catalog screening
        -> explicit advantage checklist
        -> reviewed gaps
        -> algorithm proposals and evaluations

## Storage

The canonical relational model remains the stable center. Raw or large bytes are not forced into relational JSON: `LocalContentAddressedStore` establishes the content-addressed object-store contract for pilot work and can later be replaced by S3-compatible storage without changing scientific objects.

SQLite is the local default. SQLAlchemy keeps the schema PostgreSQL-ready; the `postgres` optional dependency supplies psycopg when needed.

## Deliberate non-choices

v0.3 still does not require Kafka, Kubernetes, microservices, Neo4j, an ANN server, or one mandatory embedding model. Pilot-scale exact baselines make representation and evaluation mistakes visible before infrastructure scale makes them expensive.
