"""LLM client tests with a scripted fake transport (stands in for the network; does not prove a real API accepts these requests)."""
import asyncio

import pytest

from app.config import Settings
from app.services.http import TransportError
from app.services.llm import LlmClient, LlmNotConfigured, LlmUnavailable


class Fake:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def __call__(self, method, url, *, headers, params, json, timeout):
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json, "timeout": timeout})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def anthropic(**kw):
    return Settings(llm_provider="anthropic", llm_api_key="sk-secret", llm_model="some-model", **kw)


def openai(**kw):
    return Settings(llm_provider="openai_compatible", llm_api_key="sk-secret", llm_model="m", llm_base_url="https://llm.example/v1", **kw)


def complete(settings, response, system="SYS", user="USER"):
    fake = Fake(response)
    out = asyncio.run(LlmClient(settings, transport=fake).complete(system, user))
    return out, fake


def test_anthropic_request_and_response():
    out, fake = complete(anthropic(), (200, {"content": [{"type": "text", "text": "Hello "}, {"type": "text", "text": "there"}]}))
    assert out == "Hello there"
    c = fake.calls[0]
    assert c["url"] == "https://api.anthropic.com/v1/messages" and c["method"] == "POST"
    assert c["headers"]["x-api-key"] == "sk-secret" and c["headers"]["anthropic-version"]
    assert c["json"]["system"] == "SYS" and c["json"]["messages"] == [{"role": "user", "content": "USER"}]
    assert c["json"]["model"] == "some-model" and c["json"]["max_tokens"] == 1500


def test_anthropic_ignores_non_text_blocks():
    out, _ = complete(anthropic(), (200, {"content": [{"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": "answer"}]}))
    assert out == "answer"


def test_openai_compatible_request_and_response():
    out, fake = complete(openai(), (200, {"choices": [{"message": {"content": "  hi  "}}]}))
    assert out == "hi"
    c = fake.calls[0]
    assert c["url"] == "https://llm.example/v1/chat/completions"
    assert c["headers"]["authorization"] == "Bearer sk-secret"
    assert c["json"]["messages"][0] == {"role": "system", "content": "SYS"}


def test_not_configured_makes_no_call():
    for s in (Settings(), Settings(llm_api_key="k"), Settings(llm_api_key="k", llm_model="m", llm_provider="openai_compatible"),
              Settings(llm_api_key="k", llm_model="m", llm_provider="mystery")):
        fake = Fake((200, {}))
        with pytest.raises(LlmNotConfigured):
            asyncio.run(LlmClient(s, transport=fake).complete("a", "b"))
        assert fake.calls == []


@pytest.mark.parametrize(
    "status,code,http",
    [(429, "ai_busy", 503), (529, "ai_busy", 503), (401, "ai_auth", 502), (403, "ai_auth", 502),
     (404, "ai_model", 502), (400, "ai_rejected", 502), (500, "ai_error", 502)],
)
def test_upstream_errors_map_and_never_echo_the_body(status, code, http):
    with pytest.raises(LlmUnavailable) as e:
        complete(anthropic(), (status, {"error": {"message": "echo sk-secret and the prompt"}}))
    assert (e.value.code, e.value.http_status) == (code, http)
    assert "sk-secret" not in e.value.message and "prompt" not in e.value.message


@pytest.mark.parametrize("err,code,http", [(TransportError(True), "ai_timeout", 504), (TransportError(False), "ai_unreachable", 502)])
def test_transport_failures(err, code, http):
    with pytest.raises(LlmUnavailable) as e:
        complete(anthropic(), err)
    assert (e.value.code, e.value.http_status) == (code, http)


@pytest.mark.parametrize("body", [{}, {"content": []}, {"content": [{"type": "text", "text": "   "}]}, {"choices": []}, None])
def test_empty_or_malformed_answers_are_errors(body):
    for settings in (anthropic(), openai()):
        with pytest.raises(LlmUnavailable) as e:
            complete(settings, (200, body))
        assert e.value.code in {"ai_empty", "ai_error"}


def test_timeout_comes_from_settings():
    _, fake = complete(anthropic(llm_timeout=12.5), (200, {"content": [{"type": "text", "text": "ok"}]}))
    assert fake.calls[0]["timeout"] == 12.5
