# Operations v0.4

## Local validation

```bash
python -m pip install -e '.[dev]'
pytest -q
ruff check .
mypy src
bash scripts/smoke_v04.sh
```

## Environment

Important variables:

- `DISCOVERY_DATABASE_URL`
- `DISCOVERY_GATEWAY_URL`
- `DISCOVERY_GATEWAY_TIMEOUT`
- `DISCOVERY_ONTOLOGY_SEED`
- `DISCOVERY_OBJECT_STORE`
- `DISCOVERY_CONTACT_EMAIL`
- `DISCOVERY_DIRECT_PROVIDERS`
- `OPENALEX_API_KEY`

Do not put credentials in committed configuration. Request audit redacts known credential-like query parameters, but configuration hygiene remains required.

## Database migrations

```bash
alembic upgrade head
alembic current
```

v0.4 head is revision `0003`.

## Suggested operational sequence

```text
1. initialize DB
2. import ontology/native vocabulary releases
3. snapshot gateway/provider capabilities
4. create research campaign
5. execute retrieval/deep harvest
6. inspect coverage/saturation/provider failures
7. resolve selected identities and integrity signals
8. discover rights-bearing assets
9. enqueue permitted structured assets
10. run local worker
11. inspect ProblemInstance/math extraction
12. export reproducible corpus snapshot
13. run structural analysis/evaluation
```

## Resumption

- Query-batch harvests persist query checkpoints.
- Direct deep harvest persists provider cursor/offset checkpoints.
- Gateway harvest persists signed cursor checkpoints.
- Processing jobs preserve attempts and retry state.
- Campaign runs preserve success/failure and result summaries.

Re-running a completed stage should not silently duplicate the scientific object.

## Observability

```bash
discovery doctor
discovery coverage snapshot
discovery coverage operations
discovery queue stats
```

Provider HTTP audit rows preserve final status and response hashes. Retaining raw response bodies is optional and uses the content-addressed object store.

## Corpus export

```bash
discovery corpus export data/exports/corpus.jsonl
```

The export is an analysis/reproducibility snapshot, not a substitute for source-specific redistribution rights. Content assets are not automatically bundled into an export.
