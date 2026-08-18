from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class StoredObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    sha256: str
    size: int = Field(ge=0)
    path: str | None = None
    media_type: str | None = None


class ObjectStore(Protocol):
    def put(self, content: bytes, *, media_type: str | None = None) -> StoredObject: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


class LocalContentAddressedStore:
    """Pilot-scale object store with content-addressed immutable blobs."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, content: bytes, *, media_type: str | None = None) -> StoredObject:
        digest = hashlib.sha256(content).hexdigest()
        key = f"sha256/{digest[:2]}/{digest}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(content)
        return StoredObject(
            key=key,
            sha256=f"sha256:{digest}",
            size=len(content),
            path=str(path),
            media_type=media_type,
        )

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()
