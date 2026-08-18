from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GatewayBoundaryError(RuntimeError):
    pass


class ResearchBoundaryReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    boundary_kind: str
    gateway_required: bool
    accepted: bool
    reason: str


def inspect_research_boundary(
    provider: object,
    *,
    allow_fixture: bool = True,
) -> ResearchBoundaryReport:
    name = getattr(provider, "name", type(provider).__name__)
    boundary_kind = getattr(provider, "boundary_kind", "unknown")
    accepted = boundary_kind == "gateway" or (allow_fixture and boundary_kind == "fixture")
    if boundary_kind == "gateway":
        reason = "external scientific acquisition is routed through x402-research-gateway"
    elif allow_fixture and boundary_kind == "fixture":
        reason = "offline deterministic fixture is allowed for tests and replay only"
    else:
        reason = "external scientific acquisition must originate through x402-research-gateway"
    return ResearchBoundaryReport(
        provider=str(name),
        boundary_kind=str(boundary_kind),
        gateway_required=True,
        accepted=accepted,
        reason=reason,
    )


def require_gateway_boundary(
    provider: object,
    *,
    allow_fixture: bool = True,
) -> ResearchBoundaryReport:
    report = inspect_research_boundary(provider, allow_fixture=allow_fixture)
    if not report.accepted:
        raise GatewayBoundaryError(
            f"research boundary rejected provider {report.provider!r}: {report.reason}"
        )
    return report
