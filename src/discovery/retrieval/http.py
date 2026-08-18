from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(default=4, ge=1, le=12)
    base_delay_seconds: float = Field(default=0.5, ge=0, le=60)
    max_delay_seconds: float = Field(default=8.0, ge=0, le=300)
    retry_statuses: set[int] = Field(
        default_factory=lambda: {408, 425, 429, 500, 502, 503, 504}
    )


class HttpCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    provider: str
    operation: str
    method: str
    url: str
    request_fingerprint: str
    started_at: datetime
    completed_at: datetime
    attempts: int = Field(ge=1)
    status_code: int | None = None
    response_sha256: str | None = None
    response_headers: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


RequestObserver = Callable[[HttpCallRecord, bytes | None], None]
SleepFunction = Callable[[float], None]

QueryParamPrimitive = str | int | float | bool | None
QueryParamValue = QueryParamPrimitive | Sequence[QueryParamPrimitive]


def _normalize_params(
    params: Mapping[str, object] | None,
) -> dict[str, QueryParamValue] | None:
    if params is None:
        return None
    normalized: dict[str, QueryParamValue] = {}
    for key, value in params.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            normalized[key] = value
            continue
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            items: list[QueryParamPrimitive] = []
            for item in value:
                if item is None or isinstance(item, (str, int, float, bool)):
                    items.append(item)
                else:
                    items.append(str(item))
            normalized[key] = items
            continue
        normalized[key] = str(value)
    return normalized

_REDACTED_QUERY_NAMES = {
    "api_key",
    "apikey",
    "access_token",
    "token",
    "key",
    "authorization",
    "email",
    "mailto",
}


def sanitize_url(url: str) -> str:
    parts = urlsplit(url)
    sanitized_query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        rendered = "<redacted>" if key.casefold() in _REDACTED_QUERY_NAMES else value
        sanitized_query.append((key, rendered))
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(sanitized_query, doseq=True),
            parts.fragment,
        )
    )


def _fingerprint(method: str, url: str, content: bytes | None) -> str:
    digest = hashlib.sha256()
    digest.update(method.upper().encode())
    digest.update(b"\0")
    digest.update(sanitize_url(url).encode())
    digest.update(b"\0")
    if content:
        digest.update(content)
    return f"sha256:{digest.hexdigest()}"


def _response_headers(headers: httpx.Headers) -> dict[str, str]:
    selected = {
        "content-type",
        "etag",
        "last-modified",
        "retry-after",
        "x-ratelimit-limit",
        "x-ratelimit-remaining",
        "x-ratelimit-reset",
        "ratelimit-limit",
        "ratelimit-remaining",
        "ratelimit-reset",
    }
    return {key: value for key, value in headers.items() if key.casefold() in selected}


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


class ResilientHttpClient:
    """Small synchronous HTTP execution layer with auditable retries.

    It does not hide provider semantics. It only centralizes request hygiene,
    bounded retry behavior, rate-limit backoff, redacted request fingerprints,
    and final-response observation for provenance/replay tooling.
    """

    def __init__(
        self,
        client: httpx.Client,
        *,
        retry_policy: RetryPolicy | None = None,
        observer: RequestObserver | None = None,
        sleep: SleepFunction = time.sleep,
    ) -> None:
        self.client = client
        self.retry_policy = retry_policy or RetryPolicy()
        self.observer = observer
        self.sleep = sleep

    def request(
        self,
        method: str,
        url: str,
        *,
        provider: str,
        operation: str,
        params: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
        json_body: Mapping[str, object] | None = None,
        content: bytes | None = None,
    ) -> httpx.Response:
        body = content
        if json_body is not None:
            body = json.dumps(json_body, sort_keys=True, separators=(",", ":")).encode()
        request = self.client.build_request(
            method,
            url,
            params=_normalize_params(params),
            headers=headers,
            json=json_body,
            content=content if json_body is None else None,
        )
        request_id = str(uuid4())
        started = datetime.now(UTC)
        fingerprint = _fingerprint(method, str(request.url), body)
        last_error: Exception | None = None
        attempts = 0

        for attempts in range(1, self.retry_policy.max_attempts + 1):
            response: httpx.Response | None = None
            try:
                response = self.client.send(request)
                if (
                    response.status_code in self.retry_policy.retry_statuses
                    and attempts < self.retry_policy.max_attempts
                ):
                    delay = _retry_after_seconds(response)
                    if delay is None:
                        delay = min(
                            self.retry_policy.max_delay_seconds,
                            self.retry_policy.base_delay_seconds * (2 ** (attempts - 1)),
                        )
                    if delay > 0:
                        self.sleep(delay)
                    request = self.client.build_request(
                        method,
                        url,
                        params=_normalize_params(params),
                        headers=headers,
                        json=json_body,
                        content=content if json_body is None else None,
                    )
                    continue
                self._observe(
                    request_id=request_id,
                    provider=provider,
                    operation=operation,
                    method=method,
                    url=str(request.url),
                    request_fingerprint=fingerprint,
                    started=started,
                    attempts=attempts,
                    response=response,
                    error=None,
                )
                return response
            except httpx.TransportError as exc:
                last_error = exc
                if attempts >= self.retry_policy.max_attempts:
                    break
                delay = min(
                    self.retry_policy.max_delay_seconds,
                    self.retry_policy.base_delay_seconds * (2 ** (attempts - 1)),
                )
                if delay > 0:
                    self.sleep(delay)
                request = self.client.build_request(
                    method,
                    url,
                    params=_normalize_params(params),
                    headers=headers,
                    json=json_body,
                    content=content if json_body is None else None,
                )

        error = last_error or RuntimeError("HTTP request failed without a response")
        self._observe(
            request_id=request_id,
            provider=provider,
            operation=operation,
            method=method,
            url=str(request.url),
            request_fingerprint=fingerprint,
            started=started,
            attempts=max(1, attempts),
            response=None,
            error=error,
        )
        raise error

    def _observe(
        self,
        *,
        request_id: str,
        provider: str,
        operation: str,
        method: str,
        url: str,
        request_fingerprint: str,
        started: datetime,
        attempts: int,
        response: httpx.Response | None,
        error: Exception | None,
    ) -> None:
        if self.observer is None:
            return
        body = response.content if response is not None else None
        response_sha256 = None
        if body is not None:
            response_sha256 = f"sha256:{hashlib.sha256(body).hexdigest()}"
        record = HttpCallRecord(
            id=request_id,
            provider=provider,
            operation=operation,
            method=method.upper(),
            url=sanitize_url(url),
            request_fingerprint=request_fingerprint,
            started_at=started,
            completed_at=datetime.now(UTC),
            attempts=attempts,
            status_code=response.status_code if response is not None else None,
            response_sha256=response_sha256,
            response_headers=_response_headers(response.headers) if response is not None else {},
            error=f"{type(error).__name__}:{error}" if error is not None else None,
        )
        self.observer(record, body)

    def get_json(
        self,
        url: str,
        *,
        provider: str,
        operation: str,
        params: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        response = self.request(
            "GET",
            url,
            provider=provider,
            operation=operation,
            params=_normalize_params(params),
            headers=headers,
        )
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise ValueError(f"{provider}:{operation} returned non-object JSON")
        return value
