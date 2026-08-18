from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any
from uuid import NAMESPACE_URL, uuid5


def stable_id(namespace: str, value: str) -> str:
    """Return a reproducible UUID-like identifier for an external identity."""
    return str(uuid5(NAMESPACE_URL, f"scientific-discovery:{namespace}:{value.strip()}"))


def canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    """Stable hash for non-secret reproducibility metadata.

    Do not use this helper for sensitive queries or credentials. Those require a
    keyed/salted construction supplied by the caller or upstream protocol.
    """
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
