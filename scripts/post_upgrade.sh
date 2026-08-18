#!/usr/bin/env bash
set -euo pipefail

rm -rf src/scientific_discovery.egg-info
find src tests -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

python -m pip install -e '.[dev]'
pytest -q
ruff check .
mypy src
bash scripts/smoke_test.sh

printf '\nv0.2 upgrade validation passed.\n'
