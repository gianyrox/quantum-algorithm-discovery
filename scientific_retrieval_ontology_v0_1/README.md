# scientific_retrieval_ontology_v0_1

Generated: 2026-08-15

## Reconstruction status

This release was regenerated from the completed report and its cited/source scaffold after the original transient sandbox files were no longer present. It reproduces the reported schemas, row counts, complete ANZSRC hierarchy, overlay identifiers, cited examples, and deterministic retrieval expansions. It is **not guaranteed to be byte-for-byte identical** to the original transient archive. No new Deep Research run was launched.

## Scope

The package is a breadth-first scientific-literature retrieval ontology baseline. It separates:

1. a disciplinary coverage scaffold;
2. field-native and named concept records;
3. independent cross-domain, mathematical, scientific-discovery, measurement, complex-systems, unconventional-computation, artificial-life, quantum, and quantum-biology overlays;
4. retrieval terms, ambiguity controls, and conservative semantic relationships.

It does not perform cross-disciplinary hypothesis generation or assert that similarly named mechanisms are equivalent across fields.

## Record counts

| Record family | Records |
|---|---:|
| `DISCIPLINES` | 2,215 |
| `CONCEPTS` | 2,706 |
| `TERMS` | 7,149 |
| `MODELS_EQUATIONS_METHODS` | 81 |
| `RELATIONSHIPS` | 30 |
| `SEED_SOURCES` | 34 |
| `COVERAGE` | 29 |
| `ANZSRC_DIVISION_COUNTS` | 23 |

The `DISCIPLINES` table contains one synthetic root, 23 ANZSRC Divisions, 213 Groups, 1,967 Fields, and 11 independent retrieval overlays: 2,215 records total.

The `CONCEPTS` table contains 1,967 ANZSRC leaf-field retrieval anchors plus 739 field-native, named, and independent-overlay concepts: 2,706 records total.

## Files

Each record family is supplied as UTF-8 CSV and newline-delimited JSON (`.jsonl`).

- `DISCIPLINES.csv`
- `DISCIPLINES.jsonl`
- `CONCEPTS.csv`
- `CONCEPTS.jsonl`
- `TERMS.csv`
- `TERMS.jsonl`
- `MODELS_EQUATIONS_METHODS.csv`
- `MODELS_EQUATIONS_METHODS.jsonl`
- `RELATIONSHIPS.csv`
- `RELATIONSHIPS.jsonl`
- `SEED_SOURCES.csv`
- `SEED_SOURCES.jsonl`
- `COVERAGE.csv`
- `COVERAGE.jsonl`
- `ANZSRC_DIVISION_COUNTS.csv`
- `ANZSRC_DIVISION_COUNTS.jsonl`
- `README.md`

## Schemas

- **DISCIPLINES**: `discipline_id | name | parent_id | level | description`
- **CONCEPTS**: `concept_id | discipline_id | canonical_concept | concept_type | short_definition`
- **TERMS**: `concept_id | term | term_type | context`
- **MODELS_EQUATIONS_METHODS**: `concept_id | name | type | discipline | related_concepts`
- **RELATIONSHIPS**: `source_concept_id | relationship | target_concept_id`
- **SEED_SOURCES**: `discipline_or_concept | source | year | DOI_or_URL | role`
- **COVERAGE**: `discipline | coverage_status | missing_branches | newly_discovered_branches`
- **ANZSRC_DIVISION_COUNTS**: `division_code | division | groups | fields`

## Provenance and construction

- The disciplinary backbone is ANZSRC 2020 Fields of Research, represented as `ANZ-<code>` identifiers.
- The reconstruction preserves the report’s 23 Division / 213 Group / 1,967 Field distribution and its eleven explicit overlay nodes.
- Every ANZSRC leaf has a `CF-<six-digit-code>` concept retrieval anchor.
- Independent and named concept records use `C000001` through `C000739`.
- Ambiguity records are contextual. An exclusion for one disciplinary query may be a target term in another discipline.
- Relationships are deliberately sparse and do not encode speculative cross-domain analogies.

## Validation

- Expected row counts: passed.
- CSV and JSONL schema/order checks: passed.
- Discipline parent references: passed.
- Concept-to-discipline references: passed.
- Term, model/method, and relationship concept references: passed.
- ANZSRC Division/Group/Field count checks: passed.

### Data-file SHA-256 checksums

| File | Rows | Bytes | SHA-256 |
|---|---:|---:|---|
| `ANZSRC_DIVISION_COUNTS.csv` | 23 | 786 | `64ef2e219854c8394122ca37842b104e8531523250867f8b176e15704f10ede3` |
| `ANZSRC_DIVISION_COUNTS.jsonl` | 23 | 1,914 | `4d6d743c6cc64826a82dca26f1cdce953d7fd7093c664dbf7e6d466e3362f71b` |
| `CONCEPTS.csv` | 2,706 | 352,036 | `caa28aa699325fd3d21abfa2293e23a7ae5da6e52649abfc5c0ec44890a18a51` |
| `CONCEPTS.jsonl` | 2,706 | 608,417 | `d5f0f6018ac9f3efb91f0c62701e723b2f593195a354472267cac5659c8a5300` |
| `COVERAGE.csv` | 29 | 7,601 | `3c8c111f937d2d0b430f2c60965f96d3d7c72ca028540598f5fe90e33abdddd3` |
| `COVERAGE.jsonl` | 29 | 10,013 | `638f1073e2dbd7db538b8115bd4fe3421cbb94c5c15e8c00ab868589b6eb924c` |
| `DISCIPLINES.csv` | 2,215 | 209,651 | `f0e8719170cbaac5f704ca81d99b452ef874ae18210ebf44ba4b6a2c36c69851` |
| `DISCIPLINES.jsonl` | 2,215 | 357,601 | `8406cdaef0ca5809aa8431c699e0f12dc033933793e2426b880192dee830c379` |
| `MODELS_EQUATIONS_METHODS.csv` | 81 | 8,350 | `c3e63368bfdfc476abc46fe1bca81cffb410a2f67d178247e048602f63afa8b2` |
| `MODELS_EQUATIONS_METHODS.jsonl` | 81 | 14,052 | `4c2f79298f0141a549d4f0953d1eb2881b66a1e3f7b053e1e7479d4e81978aa2` |
| `RELATIONSHIPS.csv` | 30 | 933 | `e20a9d319b4dc6e84d8f98436ca6f4ad219c8628189462ed960bcfecd9121e9c` |
| `RELATIONSHIPS.jsonl` | 30 | 2,774 | `01d67f4fbfae47b45cfd9fca482714ca12bf554c769a6b47f1d661ecf7ccf7d5` |
| `SEED_SOURCES.csv` | 34 | 5,383 | `179fa76bb6ae60b8530e364650193c2471ccba8805195f260a6de1284f3acfa2` |
| `SEED_SOURCES.jsonl` | 34 | 7,759 | `709776fcb3f589139314f8212e0ada50856da129f5d8676d6206c0f97cb96c7c` |
| `TERMS.csv` | 7,149 | 656,139 | `7ad7ade2f8511a5d12e2721f763b8be39622f990f11a2c29b52d6ee71af353af` |
| `TERMS.jsonl` | 7,149 | 1,025,103 | `2ec3c1c94e9e20b548b34f687d94b9e2214d7fb0d3b4d90619d5ad14c3771588` |

## Important limitations

- `partial` and `shallow` coverage statuses are continuation markers, not completion claims.
- The ANZSRC hierarchy is a coverage scaffold. Many native disciplinary vocabularies are polyhierarchies or graphs and should not be flattened into a single-parent tree.
- A production release should add source vocabulary identifiers, source versions, preferred/non-preferred status, deprecation status, language, validity dates, provenance, and licensing metadata.
- Licensed standards and commercial vocabularies may be referenced or mapped but not necessarily redistributed verbatim.

## Primary continuation points

Machine-ingest complete native taxonomies; add historical/deprecated terminology; expand named model, equation, instrument, assay, task, dataset, and method dictionaries; build field-conditioned ambiguity templates; and evaluate recall empirically against stratified known-paper sets.
