"""Judge0 client tests.

These use a scripted fake transport, which is test scaffolding only: it stands in for the network so the
client's request building, polling and error handling can be checked without a Judge0 instance.
They do NOT prove that a real Judge0 server accepts these requests; that needs a manual check.
"""
import asyncio
import base64

import pytest

from app.config import Settings
from app.services.judge0 import (
    MAX_OUTPUT_CHARS,
    ExecutionNotConfigured,
    ExecutionUnavailable,
    Judge0Client,
    TransportError,
)


def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


class FakeTransport:
    """Returns scripted (status, body) tuples in order, or raises scripted exceptions."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    async def __call__(self, method, url, *, headers, params, json, timeout):
        self.calls.append({"method": method, "url": url, "headers": headers, "params": params, "json": json})
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        return item


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def make(transport, **overrides):
    clock = FakeClock()
    settings = Settings(judge0_url="http://j0", **overrides)
    return Judge0Client(settings, transport=transport, sleep=clock.sleep, clock=clock), clock


def result(status_id, description, **fields):
    body = {"status": {"id": status_id, "description": description}, "stdout": None, "stderr": None,
            "compile_output": None, "message": None, "time": None, "memory": None}
    body.update(fields)
    return 200, body


def run(client, language="python", code="print(1)", stdin=""):
    return asyncio.run(client.run(language, code, stdin))


def test_success_and_request_shape():
    t = FakeTransport((201, {"token": "tok"}), result(3, "Accepted", stdout=b64("Hello\n"), time="0.012", memory=3000))
    client, _ = make(t)
    out = run(client, "python", "print('hi')", "Asha\n")

    assert out.outcome == "success" and out.stdout == "Hello\n"
    assert out.time_seconds == 0.012 and out.memory_kb == 3000 and out.status_text == "Accepted"

    post = t.calls[0]
    assert post["method"] == "POST" and post["url"] == "http://j0/submissions"
    assert post["params"] == {"base64_encoded": "true", "wait": "false"}
    assert post["json"]["language_id"] == 71
    assert base64.b64decode(post["json"]["source_code"]).decode() == "print('hi')"
    assert base64.b64decode(post["json"]["stdin"]).decode() == "Asha\n"
    assert post["json"]["cpu_time_limit"] == 5
    assert t.calls[1]["url"] == "http://j0/submissions/tok"


def test_language_ids():
    for lang, lid in {"python": 71, "c": 50, "java": 62}.items():
        t = FakeTransport((201, {"token": "x"}), result(3, "Accepted"))
        client, _ = make(t)
        run(client, lang)
        assert t.calls[0]["json"]["language_id"] == lid


def test_polls_until_finished():
    t = FakeTransport((201, {"token": "x"}), result(1, "In Queue"), result(2, "Processing"), result(3, "Accepted", stdout=b64("ok")))
    client, clock = make(t)
    out = run(client)
    assert out.stdout == "ok"
    assert len(t.calls) == 4 and len(clock.sleeps) == 2


def test_compile_error():
    t = FakeTransport((201, {"token": "x"}), result(6, "Compilation Error", compile_output=b64("main.c:3: error: expected ';'")))
    client, _ = make(t)
    out = run(client, "c")
    assert out.outcome == "compile_error" and "expected ';'" in out.compile_output


def test_runtime_error():
    t = FakeTransport((201, {"token": "x"}), result(11, "Runtime Error (NZEC)", stderr=b64("ZeroDivisionError")))
    client, _ = make(t)
    out = run(client)
    assert out.outcome == "runtime_error" and out.stderr == "ZeroDivisionError"


def test_time_limit():
    t = FakeTransport((201, {"token": "x"}), result(5, "Time Limit Exceeded"))
    client, _ = make(t)
    assert run(client).outcome == "time_limit"


def test_internal_error_status():
    t = FakeTransport((201, {"token": "x"}), result(13, "Internal Error", message=b64("boom")))
    client, _ = make(t)
    out = run(client)
    assert out.outcome == "internal_error" and out.message == "boom"


def test_poll_timeout():
    t = FakeTransport((201, {"token": "x"}), result(2, "Processing"))
    client, _ = make(t, judge0_poll_timeout=2.0, judge0_poll_interval=1.0)
    with pytest.raises(ExecutionUnavailable) as e:
        run(client)
    assert e.value.code == "execution_timeout" and e.value.http_status == 504


def test_not_configured_makes_no_network_call():
    t = FakeTransport((201, {"token": "x"}))
    client = Judge0Client(Settings(judge0_url=""), transport=t)
    with pytest.raises(ExecutionNotConfigured):
        asyncio.run(client.run("python", "x", ""))
    assert t.calls == []


def test_auth_headers():
    rapid = FakeTransport((201, {"token": "x"}), result(3, "Accepted"))
    client, _ = make(rapid, judge0_api_key="k", judge0_api_host="judge0-ce.p.rapidapi.com")
    run(client)
    h = rapid.calls[0]["headers"]
    assert h["X-RapidAPI-Key"] == "k" and h["X-RapidAPI-Host"] == "judge0-ce.p.rapidapi.com"

    selfhosted = FakeTransport((201, {"token": "x"}), result(3, "Accepted"))
    client, _ = make(selfhosted, judge0_api_key="tok")
    run(client)
    h = selfhosted.calls[0]["headers"]
    assert h["X-Auth-Token"] == "tok" and "X-RapidAPI-Key" not in h

    none = FakeTransport((201, {"token": "x"}), result(3, "Accepted"))
    client, _ = make(none)
    run(client)
    assert set(none.calls[0]["headers"]) == {"Content-Type"}


@pytest.mark.parametrize(
    "transport_error,code,status",
    [(TransportError(timed_out=True), "execution_timeout", 504), (TransportError(timed_out=False), "execution_unreachable", 502)],
)
def test_transport_failures(transport_error, code, status):
    client, _ = make(FakeTransport(transport_error))
    with pytest.raises(ExecutionUnavailable) as e:
        run(client)
    assert e.value.code == code and e.value.http_status == status


@pytest.mark.parametrize(
    "upstream_status,code,http_status",
    [(429, "execution_busy", 503), (401, "execution_auth", 502), (403, "execution_auth", 502),
     (422, "execution_rejected", 502), (500, "execution_error", 502)],
)
def test_upstream_error_mapping(upstream_status, code, http_status):
    client, _ = make(FakeTransport((upstream_status, {"error": "secret-upstream-detail"})))
    with pytest.raises(ExecutionUnavailable) as e:
        run(client)
    assert e.value.code == code and e.value.http_status == http_status
    assert "secret-upstream-detail" not in e.value.message  # upstream bodies are never echoed


def test_missing_token_and_unreadable_body():
    client, _ = make(FakeTransport((201, {})))
    with pytest.raises(ExecutionUnavailable):
        run(client)
    client, _ = make(FakeTransport((200, None)))
    with pytest.raises(ExecutionUnavailable):
        run(client)


def test_invalid_base64_does_not_crash():
    t = FakeTransport((201, {"token": "x"}), result(3, "Accepted", stdout="!!!not base64!!!"))
    client, _ = make(t)
    assert run(client).stdout == ""


def test_huge_output_is_truncated():
    big = "a" * (MAX_OUTPUT_CHARS + 500)
    t = FakeTransport((201, {"token": "x"}), result(3, "Accepted", stdout=b64(big)))
    client, _ = make(t)
    out = run(client)
    assert out.stdout.endswith("[output truncated]") and len(out.stdout) < len(big)


def test_cpu_limit_omitted_when_zero():
    t = FakeTransport((201, {"token": "x"}), result(3, "Accepted"))
    client, _ = make(t, judge0_cpu_time_limit=0)
    run(client)
    assert "cpu_time_limit" not in t.calls[0]["json"]
