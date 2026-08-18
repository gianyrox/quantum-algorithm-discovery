from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    """Runtime settings with conservative local defaults."""

    model_config = ConfigDict(extra="forbid")

    database_url: str = "sqlite:///data/scientific_discovery.db"
    gateway_url: str | None = None
    gateway_timeout_seconds: float = Field(default=30.0, gt=0)
    gateway_headers: dict[str, str] = Field(default_factory=dict)
    gateway_strict_feed402: bool = True
    ontology_seed_path: Path = Path("scientific_retrieval_ontology_v0_1")
    object_store_path: Path = Path("data/objects")
    contact_email: str | None = None
    openalex_api_key: str | None = None
    direct_providers: list[str] = Field(
        default_factory=lambda: ["openalex", "crossref", "europe_pmc", "arxiv"]
    )

    @classmethod
    def from_env(cls) -> Settings:
        headers_raw = os.getenv("DISCOVERY_GATEWAY_HEADERS_JSON", "{}").strip() or "{}"
        headers_value = json.loads(headers_raw)
        if not isinstance(headers_value, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in headers_value.items()
        ):
            raise ValueError("DISCOVERY_GATEWAY_HEADERS_JSON must be a JSON object of strings")
        direct_raw = os.getenv(
            "DISCOVERY_DIRECT_PROVIDERS",
            "openalex,crossref,europe_pmc,arxiv",
        )
        return cls(
            database_url=os.getenv(
                "DISCOVERY_DATABASE_URL", "sqlite:///data/scientific_discovery.db"
            ),
            gateway_url=os.getenv("DISCOVERY_GATEWAY_URL") or None,
            gateway_timeout_seconds=float(os.getenv("DISCOVERY_GATEWAY_TIMEOUT", "30")),
            gateway_headers=headers_value,
            gateway_strict_feed402=os.getenv(
                "DISCOVERY_GATEWAY_STRICT_FEED402", "true"
            ).lower()
            not in {"0", "false", "no"},
            ontology_seed_path=Path(
                os.getenv("DISCOVERY_ONTOLOGY_SEED", "scientific_retrieval_ontology_v0_1")
            ),
            object_store_path=Path(os.getenv("DISCOVERY_OBJECT_STORE", "data/objects")),
            contact_email=os.getenv("DISCOVERY_CONTACT_EMAIL") or None,
            openalex_api_key=os.getenv("OPENALEX_API_KEY") or None,
            direct_providers=[item.strip() for item in direct_raw.split(",") if item.strip()],
        )
