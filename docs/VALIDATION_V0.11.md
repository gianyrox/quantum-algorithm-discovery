# v0.11 validation

The v0.11 validation target is both software correctness and boundary correctness.

Required checks:

```bash
pytest -q
ruff check .
mypy src
bash scripts/smoke_v011.sh
```

Boundary-specific tests verify:

- legacy single-citation feed402 responses normalize correctly;
- explicit `result_index` grounding is honored;
- unknown feed402 rights do not grant actions;
- offline fixtures are allowed but direct external providers are rejected;
- a gateway retrieval persists the raw feed402 envelope against its `RetrievalRun`;
- a campaign links those retrieval envelopes to its `CampaignRun`;
- strict gateway mode rejects a successful paid response without canonical feed402 citation/receipt evidence.

Real Campaign 001 is the final v0.11 acceptance test. It should record the gateway manifest fingerprint and coverage context and complete without a direct-provider fallback.
