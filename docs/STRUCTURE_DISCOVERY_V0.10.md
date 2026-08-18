# Structural Discovery v0.10

## Multi-view similarity

No single embedding is allowed to define structural similarity. v0.10 keeps separate signals for task family, mathematics, operators, constraints, topology, stochastic structure, complexity, method, semantic content, lexical overlap, and citation connectivity.

Lexical similarity and citation connectivity are useful context but are penalized when ranking surprising cross-domain structural candidates. The desired candidate regime is high structural resemblance with low lexical resemblance and weak citation connectivity across different disciplines.

## Mathematical similarity

Mathematical expressions receive fingerprints based on multiple views: exact source hash, alpha-normalized hash, token multiset, operator signature, relation type, tree depth, and extracted mathematical features. These signals support candidate generation; they are not formal equivalence proofs.

## Families

`ProblemFamily` membership is induced from a configurable similarity graph. Connected components are a baseline clustering method chosen for transparency and replaceability, not because they are assumed to be scientifically optimal.

## Cross-domain relations

The ontology of review outcomes distinguishes:

- equivalent formulation;
- shared mathematical form;
- shared mechanism;
- shared function with different mechanism;
- historical transmission;
- independent rediscovery;
- analogy;
- lexical resemblance;
- unresolved.

The baseline classifier only proposes conservative categories from similarity evidence. Historical transmission and independent rediscovery require literature-history evidence and review.

## Candidate generation at scale

`StructuralSignatureIndex` provides a deterministic local LSH-like candidate generator so experiments need not compute every pair. Large-scale ANN backends can be added behind this boundary later without changing the scientific result schema.
