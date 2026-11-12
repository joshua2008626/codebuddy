"""LLM client. The API key lives only in the server environment and is never sent to the browser.

Supports Anthropic's Messages API and any OpenAI-compatible chat completions API.
"""
from __future__ import annotations

from typing import Any

from ..config import Settings
from .http import Transport, TransportError, httpx_transport

ANTHROPIC_DEFAULT_URL = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"


class LlmNotConfigured(Exception):
    """LLM_API_KEY / LLM_MODEL (and LLM_BASE_URL for openai_compatible) are not all set."""


class LlmUnavailable(Exception):
    def __init__(self, message: str, http_status: int = 502, code: str = "ai_unavailable"):
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.code = code


class LlmClient:
    def __init__(self, settings: Settings, transport: Transport = httpx_transport):
        self.settings = settings
        self._transport = transport

    def _build(self, system: str, user: str) -> tuple[str, dict[str, str], dict[str, Any]]:
        s = self.settings
        if s.llm_provider == "anthropic":
            base = s.llm_base_url or ANTHROPIC_DEFAULT_URL
            headers = {"content-type": "application/json", "x-api-key": s.llm_api_key, "anthropic-version": ANTHROPIC_VERSION}
            body = {"model": s.llm_model, "max_tokens": s.llm_max_tokens, "system": system, "messages": [{"role": "user", "content": user}]}
            return f"{base}/v1/messages", headers, body
        headers = {"content-type": "application/json", "authorization": f"Bearer {s.llm_api_key}"}
        body = {
            "model": s.llm_model,
            "max_tokens": s.llm_max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        return f"{s.llm_base_url}/chat/completions", headers, body

    def _extract(self, body: dict) -> str:
        try:
            if self.settings.llm_provider == "anthropic":
                blocks = body.get("content") or []
                return "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
            return body["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError, AttributeError):
            return ""

    async def complete(self, system: str, user: str) -> str:
        if not self.settings.ai_configured:
            raise LlmNotConfigured()

        url, headers, payload = self._build(system, user)
        try:
            status, body = await self._transport("POST", url, headers=headers, params=None, json=payload, timeout=self.settings.llm_timeout)
        except TransportError as exc:
            if exc.timed_out:
                raise LlmUnavailable("Buddy AI took too long to answer. Try again.", 504, "ai_timeout") from exc
            raise LlmUnavailable("Couldn't reach the AI service.", 502, "ai_unreachable") from exc

        # Messages are deliberately generic: upstream bodies can contain request details, so they are never echoed.
        if status in (429, 529):
            raise LlmUnavailable("Buddy AI is busy right now. Try again in a moment.", 503, "ai_busy")
        if status in (401, 403):
            raise LlmUnavailable("The AI service rejected the server's credentials. Check LLM_API_KEY.", 502, "ai_auth")
        if status == 404:
            raise LlmUnavailable("The AI service doesn't recognise the configured model. Check LLM_MODEL.", 502, "ai_model")
        if status in (400, 422):
            raise LlmUnavailable("The AI service rejected this request.", 502, "ai_rejected")
        if status >= 400 or not isinstance(body, dict):
            raise LlmUnavailable("The AI service returned an error.", 502, "ai_error")

        answer = self._extract(body).strip()
        if not answer:
            raise LlmUnavailable("Buddy AI sent back an empty answer. Try asking again.", 502, "ai_empty")
        return answer
