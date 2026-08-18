from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GatewayOperation(BaseModel):
    model_config = ConfigDict(extra="allow")

    operation_id: str
    capability: str = "unknown"
    capabilities: list[str] = Field(default_factory=list)
    path: str
    method: str = "POST"
    tier: str | None = None
    pagination_model: str | None = None
    identifier_schemes: list[str] = Field(default_factory=list)
    content_types: list[str] = Field(default_factory=list)
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] = Field(default_factory=dict)

    def supports(self, capability: str) -> bool:
        return self.capability == capability or capability in self.capabilities


class GatewayManifest(BaseModel):
    model_config = ConfigDict(extra="allow")

    spec: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    operations: list[GatewayOperation] = Field(default_factory=list)
    provenance_level: int | None = None
    raw: dict[str, object] = Field(default_factory=dict)

    def operations_for(self, capability: str) -> list[GatewayOperation]:
        return [item for item in self.operations if item.supports(capability)]


def _manifest_root(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("feed402", "manifest", "data"):
        value = payload.get(key)
        if isinstance(value, Mapping) and (
            "operations" in value or "capabilities" in value or "spec" in value
        ):
            return value
    return payload


def parse_gateway_manifest(payload: Mapping[str, Any]) -> GatewayManifest:
    root = _manifest_root(payload)
    operations_obj = root.get("operations", [])
    operations: list[GatewayOperation] = []
    if isinstance(operations_obj, list):
        for value in operations_obj:
            if not isinstance(value, Mapping):
                continue
            operation_id = value.get("operation_id", value.get("id", value.get("name")))
            path = value.get("path", value.get("url"))
            raw_caps = value.get("capabilities", [])
            capabilities = [str(item) for item in raw_caps] if isinstance(raw_caps, list) else []
            raw_capability = value.get("capability")
            capability = (
                raw_capability
                if isinstance(raw_capability, str) and raw_capability
                else capabilities[0]
                if capabilities
                else "unknown"
            )
            if not (
                isinstance(operation_id, str)
                and operation_id
                and isinstance(path, str)
                and path
            ):
                continue
            normalized = dict(value)
            normalized["operation_id"] = operation_id
            normalized["path"] = path
            normalized["capability"] = capability
            normalized["capabilities"] = capabilities
            operations.append(GatewayOperation.model_validate(normalized))
    caps_obj = root.get("capabilities", [])
    capabilities = [str(item) for item in caps_obj] if isinstance(caps_obj, list) else []
    level = root.get("provenance_level")
    return GatewayManifest(
        spec=root.get("spec") if isinstance(root.get("spec"), str) else None,
        capabilities=capabilities,
        operations=operations,
        provenance_level=level if isinstance(level, int) else None,
        raw=dict(payload),
    )
