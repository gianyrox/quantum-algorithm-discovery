from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    """Runtime settings with conservative local defaults."""

    model_config = ConfigDict(extra="forbid")

    database_url: str = "sqlite:///data/scientific_discovery.db"
    gateway_url: str | None = None
    gateway_timeout_seconds: float = Field(default=30.0, gt=0)
    ontology_seed_path: Path = Path("scientific_retrieval_ontology_v0_1")

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_url=os.getenv(
                "DISCOVERY_DATABASE_URL", "sqlite:///data/scientific_discovery.db"
            ),
            gateway_url=os.getenv("DISCOVERY_GATEWAY_URL") or None,
            gateway_timeout_seconds=float(os.getenv("DISCOVERY_GATEWAY_TIMEOUT", "30")),
            ontology_seed_path=Path(
                os.getenv("DISCOVERY_ONTOLOGY_SEED", "scientific_retrieval_ontology_v0_1")
            ),
        )
