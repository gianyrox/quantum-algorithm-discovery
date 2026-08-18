from __future__ import annotations

from contextlib import AbstractContextManager
from enum import StrEnum
from types import TracebackType

import httpx
from pydantic import BaseModel, ConfigDict, Field

from discovery.retrieval.direct import (
    ArxivProvider,
    CrossrefProvider,
    EuropePMCProvider,
    FederatedDirectProvider,
    OpenAlexProvider,
)
from discovery.retrieval.gateway import GatewayProvider
from discovery.retrieval.http import RequestObserver, RetryPolicy
from discovery.retrieval.provider import ResearchProvider


class ProviderMode(StrEnum):
    GATEWAY = "gateway"
    DIRECT = "direct"


class DirectProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: list[str] = Field(
        default_factory=lambda: ["openalex", "crossref", "europe_pmc", "arxiv"]
    )
    openalex_api_key: str | None = None
    contact_email: str | None = None
    max_workers: int = Field(default=4, ge=1, le=32)


class ManagedResearchProvider(AbstractContextManager[ResearchProvider]):
    """Own provider clients created by the runtime factory and close them safely."""

    def __init__(self, provider: ResearchProvider, closers: list[object]) -> None:
        self.provider = provider
        self._closers = closers

    def __enter__(self) -> ResearchProvider:
        return self.provider

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        for item in reversed(self._closers):
            close = getattr(item, "close", None)
            if callable(close):
                close()
        return None


def create_direct_provider(
    config: DirectProviderConfig | None = None,
    *,
    retry_policy: RetryPolicy | None = None,
    observer: RequestObserver | None = None,
) -> ManagedResearchProvider:
    resolved = config or DirectProviderConfig()
    names = set(resolved.providers)
    unknown = names - {"openalex", "crossref", "europe_pmc", "arxiv"}
    if unknown:
        raise ValueError(f"unsupported direct providers: {sorted(unknown)}")
    providers: list[ResearchProvider] = []
    closers: list[object] = []
    if "openalex" in names:
        openalex_provider = OpenAlexProvider(
            api_key=resolved.openalex_api_key,
            mailto=resolved.contact_email,
            retry_policy=retry_policy,
            observer=observer,
        )
        providers.append(openalex_provider)
        closers.append(openalex_provider)
    if "crossref" in names:
        crossref_provider = CrossrefProvider(
            mailto=resolved.contact_email,
            retry_policy=retry_policy,
            observer=observer,
        )
        providers.append(crossref_provider)
        closers.append(crossref_provider)
    if "europe_pmc" in names:
        europe_pmc_provider = EuropePMCProvider(
            email=resolved.contact_email,
            retry_policy=retry_policy,
            observer=observer,
        )
        providers.append(europe_pmc_provider)
        closers.append(europe_pmc_provider)
    if "arxiv" in names:
        arxiv_provider = ArxivProvider(retry_policy=retry_policy, observer=observer)
        providers.append(arxiv_provider)
        closers.append(arxiv_provider)
    if not providers:
        raise ValueError("at least one direct provider must be selected")
    if len(providers) == 1:
        return ManagedResearchProvider(providers[0], closers)
    federation = FederatedDirectProvider(providers, max_workers=resolved.max_workers)
    return ManagedResearchProvider(federation, closers)


def create_gateway_provider(
    base_url: str,
    *,
    timeout_seconds: float = 30.0,
    retry_policy: RetryPolicy | None = None,
    observer: RequestObserver | None = None,
    client: httpx.Client | None = None,
) -> ManagedResearchProvider:
    provider = GatewayProvider(
        base_url,
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
        observer=observer,
        client=client,
    )
    return ManagedResearchProvider(provider, [provider])
