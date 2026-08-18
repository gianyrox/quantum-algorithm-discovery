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
print(f"scientific-discovery package metadata: {installed}")
print(f"scientific-discovery module version: {discovery.__version__}")
if installed != discovery.__version__ or installed != "0.4.0":
    raise SystemExit(
        f"version mismatch: installed={installed} module={discovery.__version__} expected=0.4.0"
    )
PY

pytest -q
ruff check .
mypy src
bash scripts/smoke_v04.sh

printf '\nv0.4 real-data execution validation passed.\n'
