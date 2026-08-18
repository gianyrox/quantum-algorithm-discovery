from __future__ import annotations

import hashlib
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field


class StructuralSignature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str
    tokens: list[str] = Field(default_factory=list)


class SignatureNeighbor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str
    shared_buckets: int = Field(ge=1)


class StructuralSignatureIndex:
    """Small deterministic LSH-like candidate generator for local experiments."""

    def __init__(self, bands: int = 8) -> None:
        self.bands = max(1, bands)
        self._buckets: dict[str, set[str]] = defaultdict(set)
        self._object_buckets: dict[str, set[str]] = defaultdict(set)

    def _keys(self, signature: StructuralSignature) -> list[str]:
        normalized = sorted(set(token.casefold() for token in signature.tokens))
        if not normalized:
            return []
        keys: list[str] = []
        for band in range(self.bands):
            selected = normalized[band :: self.bands] or normalized
            payload = f"{band}:" + "|".join(selected)
            keys.append(hashlib.sha1(payload.encode()).hexdigest()[:16])
        return keys

    def add(self, signature: StructuralSignature) -> None:
        for key in self._keys(signature):
            self._buckets[key].add(signature.object_id)
            self._object_buckets[signature.object_id].add(key)

    def neighbors(
        self, object_id: str, *, minimum_shared_buckets: int = 1
    ) -> list[SignatureNeighbor]:
        counts: dict[str, int] = defaultdict(int)
        for key in self._object_buckets.get(object_id, set()):
            for candidate in self._buckets[key]:
                if candidate != object_id:
                    counts[candidate] += 1
        result = [
            SignatureNeighbor(object_id=item, shared_buckets=count)
            for item, count in counts.items()
            if count >= minimum_shared_buckets
        ]
        return sorted(result, key=lambda item: (-item.shared_buckets, item.object_id))
