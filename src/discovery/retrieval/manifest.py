from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GatewayOperation(BaseModel):
    model_config = ConfigDict(extra="allow")

    operation_id: str
    capability: str
    path: str
    method: str = "POST"
    tier: str | None = None
    pagination_model: str | None = None
    identifier_schemes: list[str] = Field(default_factory=list)
    content_types: list[str] = Field(default_factory=list)
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] = Field(default_factory=dict)


class GatewayManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    spec: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    operations: list[GatewayOperation] = Field(default_factory=list)
    provenance_level: int | None = None
    raw: dict[str, object] = Field(default_factory=dict)

    def operations_for(self, capability: str) -> list[GatewayOperation]:
        return [item for item in self.operations if item.capability == capability]


def parse_gateway_manifest(payload: Mapping[str, Any]) -> GatewayManifest:
    operations_obj = payload.get("operations", [])
    operations: list[GatewayOperation] = []
    if isinstance(operations_obj, list):
        for value in operations_obj:
            if not isinstance(value, Mapping):
                continue
            operation_id = value.get("operation_id")
            capability = value.get("capability")
            path = value.get("path")
            if not all(isinstance(item, str) and item for item in (operation_id, capability, path)):
                continue
            operations.append(GatewayOperation.model_validate(dict(value)))
    caps_obj = payload.get("capabilities", [])
    capabilities = [str(item) for item in caps_obj] if isinstance(caps_obj, list) else []
    level = payload.get("provenance_level")
    return GatewayManifest(
        spec=payload.get("spec") if isinstance(payload.get("spec"), str) else None,
        capabilities=capabilities,
        operations=operations,
        provenance_level=level if isinstance(level, int) else None,
        raw=dict(payload),
    )
