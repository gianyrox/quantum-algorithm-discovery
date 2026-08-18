from __future__ import annotations

import httpx

from discovery.retrieval.http import ResilientHttpClient, RetryPolicy, sanitize_url


def test_resilient_http_retries_and_redacts_sensitive_query_values() -> None:
    calls = 0
    observed = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(200, json={"ok": True}, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://example.test")
    resilient = ResilientHttpClient(
        client,
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0),
        observer=lambda record, body: observed.append((record, body)),
        sleep=lambda _seconds: None,
    )
    response = resilient.request(
        "GET",
        "/works",
        provider="fixture",
        operation="search",
        params={"query": "spectral", "api_key": "secret", "mailto": "me@example.test"},
    )
    assert response.status_code == 200
    assert calls == 2
    assert len(observed) == 1
    record, _body = observed[0]
    assert record.attempts == 2
    assert "secret" not in record.url
    assert "me%40example.test" not in record.url
    assert "%3Credacted%3E" in record.url


def test_sanitize_url_keeps_nonsecret_query_values() -> None:
    rendered = sanitize_url("https://example.test/x?q=abc&token=sensitive")
    assert "q=abc" in rendered
    assert "sensitive" not in rendered
