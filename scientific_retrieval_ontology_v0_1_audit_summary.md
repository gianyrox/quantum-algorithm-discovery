# Scientific Retrieval Ontology v0.1 — Audit Summary

## Bottom line

The uploaded package is structurally clean and useful as a breadth-first disciplinary scaffold, but it is not yet a production retrieval ontology. The main limitation is semantic depth rather than file integrity.

## Core findings

- Structural integrity: all eight CSV/JSONL dataset pairs match exactly; no orphan discipline/concept references or hierarchy-level errors were found.
- Concepts: 2,706 total; 2,595 (95.9%) are scaffold-derived, leaving 111 independently defined/non-scaffold concepts.
- Redundancy: 415 C-records duplicate a CF leaf anchor in the same discipline; 419 normalized canonical-name groups are duplicated.
- Terms: 7,149 rows; 7,009 (98.0%) are deterministic scaffold/query-template rows; only 140 are non-template lexical enrichments.
- Semantic graph: 30 relationship rows; 53 concepts (2.0%) participate.
- Named objects: 81 model/equation/method/algorithm records; 19 of 23 ANZSRC divisions have none.
- Empty overlays: 5 of 11 direct overlay nodes have zero concepts: OV-COMPLEX, OV-SCISCI, OV-UNCONV, OV-ALIFE, OV-QBIO.
- Coverage: 23 partial, 6 shallow, 0 strong.

## Recommendation

Run another Deep Research task, but make it a **native ontology/source registry research task**: identify authoritative machine-accessible vocabularies, ontologies, thesauri, classifications, standards, and terminology datasets for every scaffold discipline, including versions, APIs/downloads, identifiers, licensing, update cadence, synonym/relationship/deprecation coverage, and mappings to discipline IDs. Then ingest those sources programmatically before a massive paper harvest.

The Excel workbook contains the full audit, issue register, concept-level flags, duplicate analysis, term analysis, ambiguity records, source gaps, recommended v0.2 schema, next-research plan, and all raw input tables.
