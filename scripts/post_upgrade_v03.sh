#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Keep source-tree metadata from confusing pip's editable-install discovery.
rm -rf src/scientific_discovery.egg-info
find src tests -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

# Remove an older editable distribution record if one exists, then install v0.3 cleanly.
python -m pip uninstall -y scientific-discovery >/dev/null 2>&1 || true
python -m pip install -e '.[dev]'

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

python - <<'PY'
from importlib.metadata import version
import discovery

package_version = version("scientific-discovery")
if package_version != discovery.__version__:
    raise SystemExit(
        f"version mismatch: metadata={package_version} import={discovery.__version__}"
    )
print(f"scientific-discovery version: {package_version}")
PY

pytest -q
ruff check .
mypy src
bash scripts/smoke_v03.sh

printf '\nv0.3 operational research engine validation passed.\n'
