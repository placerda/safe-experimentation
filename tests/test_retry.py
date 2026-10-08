"""Tests for API retry/backoff and user-simulator failure handling."""

from __future__ import annotations

import types

import httpx
import pytest
from openai import APITimeoutError, BadRequestError, RateLimitError

from safe_benchmark import agent_runner

_REQ = httpx.Request("POST", "https://example.invalid")


def _rate_limit(retry_after: str | None = "0") -> RateLimitError:
    headers = {"retry-after": retry_after} if retry_after is not None else {}
    return RateLimitError(
        "rate_limit_exceeded",
        response=httpx.Response(429, request=_REQ, headers=headers),
        body=None,
    )


def _content_filter() -> BadRequestError:
    return BadRequestError(
        "content_filter triggered",
        response=httpx.Response(400, request=_REQ),
        body={"code": "content_filter"},
    )


def _ok(text: str = "ok"):
    msg = types.SimpleNamespace(content=text)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


def _fake_client(outcomes):
    calls = {"n": 0}
    seq = list(outcomes)

    def create(**kwargs):
        calls["n"] += 1
        item = seq.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create))
    )
    return client, calls


@pytest.fixture
def sleeps(monkeypatch):
    recorded: list[float] = []
    monkeypatch.setattr(agent_runner, "_sleep", recorded.append)
    return recorded


def test_retries_rate_limit_then_succeeds(sleeps):
    client, calls = _fake_client([_rate_limit(), _rate_limit(), _ok("done")])
    resp = agent_runner._create_with_retry(client, model="m", messages=[])
    assert resp.choices[0].message.content == "done"
    assert calls["n"] == 3
    assert len(sleeps) == 2


def test_timeout_is_retried(sleeps):
    client, calls = _fake_client([APITimeoutError(request=_REQ), _ok()])
    agent_runner._create_with_retry(client, model="m", messages=[])
    assert calls["n"] == 2
    assert len(sleeps) == 1


def test_non_retryable_raises_immediately(sleeps):
    client, calls = _fake_client([_content_filter(), _ok()])
    with pytest.raises(BadRequestError):
        agent_runner._create_with_retry(client, model="m", messages=[])
    assert calls["n"] == 1
    assert sleeps == []


def test_exhausted_attempts_reraise(sleeps):
    n = agent_runner.API_MAX_ATTEMPTS
    client, calls = _fake_client([_rate_limit() for _ in range(n)])
    with pytest.raises(RateLimitError):
        agent_runner._create_with_retry(client, model="m", messages=[])
    assert calls["n"] == n
    assert len(sleeps) == n - 1


def test_retry_after_header_is_honoured(sleeps):
    client, _ = _fake_client([_rate_limit(retry_after="7"), _ok()])
    agent_runner._create_with_retry(client, model="m", messages=[])
    # 7s from header plus up to 1s jitter.
    assert 7.0 <= sleeps[0] <= 8.0


def test_backoff_is_capped(sleeps):
    client, _ = _fake_client([_rate_limit(retry_after="9999"), _ok()])
    agent_runner._create_with_retry(client, model="m", messages=[])
    assert sleeps[0] <= agent_runner.API_BACKOFF_CAP_S + 1.0


def test_exponential_backoff_without_header(sleeps):
    client, _ = _fake_client([_rate_limit(retry_after=None)] * 3 + [_ok()])
    agent_runner._create_with_retry(client, model="m", messages=[])
    base = agent_runner.API_BACKOFF_BASE_S
    for i, delay in enumerate(sleeps):
        expected = min(agent_runner.API_BACKOFF_CAP_S, base * (2**i))
        assert expected <= delay <= expected + 1.0


def test_user_sim_content_filter_falls_back(sleeps):
    client, _ = _fake_client([_content_filter()])
    text = agent_runner._simulate_user_turn(
        client, "gpt-5.4", "system", [{"role": "assistant", "content": "hi"}]
    )
    assert text == "I'd like help with my request, please."


def test_user_sim_exhausted_rate_limit_raises(sleeps):
    n = agent_runner.API_MAX_ATTEMPTS
    client, _ = _fake_client([_rate_limit() for _ in range(n)])
    with pytest.raises(agent_runner.UserSimulatorError):
        agent_runner._simulate_user_turn(
            client, "gpt-5.4", "system", [{"role": "assistant", "content": "hi"}]
        )
