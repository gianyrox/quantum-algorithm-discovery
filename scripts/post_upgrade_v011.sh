#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m pip uninstall -y scientific-discovery >/dev/null 2>&1 || true
python -m pip install -e '.[dev]'

python - <<'PY'
from importlib.metadata import version
import discovery

installed = version("scientific-discovery")
expected = "0.11.0"
print(f"scientific-discovery package metadata: {installed}")
print(f"scientific-discovery module version: {discovery.__version__}")
if installed != expected or discovery.__version__ != expected:
    raise SystemExit(
        f"version mismatch: installed={installed} module={discovery.__version__} expected={expected}"
    )
PY

pytest -q
ruff check .
mypy src
bash scripts/smoke_v011.sh

printf '\nv0.11 gateway-first scientific discovery validation passed.\n'
