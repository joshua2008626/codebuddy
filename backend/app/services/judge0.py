"""Judge0 client.

User code is NEVER run on this server. It is sent to a Judge0 instance (self-hosted or RapidAPI),
which runs it in a sandbox. This module submits the code, polls for the result and normalises it.

Nothing is faked: if Judge0 is not configured or unreachable, a typed error is raised and the API
returns a clear message instead of made-up output.
"""
from __future__ import annotations

import asyncio
import base64
import binascii
import time
from typing import Any, Awaitable, Callable

from ..config import Settings
from ..schemas import ExecuteResponse, Outcome
from .http import Transport, TransportError, httpx_transport

MAX_OUTPUT_CHARS = 100_000  # keeps a runaway program from producing a huge response

# Judge0 status ids: 1 In Queue, 2 Processing, 3 Accepted, 4 Wrong Answer, 5 Time Limit Exceeded,
# 6 Compilation Error, 7-12 Runtime Error (SIGSEGV, SIGXFSZ, SIGFPE, SIGABRT, NZEC, Other),
# 13 Internal Error, 14 Exec Format Error.
_PENDING = {1, 2}


class ExecutionNotConfigured(Exception):
    """JUDGE0_URL is not set."""


class ExecutionUnavailable(Exception):
    def __init__(self, message: str, http_status: int = 502, code: str = "execution_unavailable"):
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.code = code


def _b64e(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _b64d(value: str | None) -> str:
    """Judge0 returns null for empty streams and base64 (with newlines) otherwise."""
    if not value:
        return ""
    try:
        text = base64.b64decode(value).decode("utf-8", "replace")
    except (binascii.Error, ValueError):
        return ""
    if len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + "\n[output truncated]"
    return text


def _outcome(status_id: int) -> Outcome:
    if status_id == 5:
        return "time_limit"
    if status_id == 6:
        return "compile_error"
    if 7 <= status_id <= 12:
        return "runtime_error"
    if status_id in (13, 14):
        return "internal_error"
    return "success"  # 3 Accepted (and 4, which only applies when an expected output is supplied)


def normalise(body: dict) -> ExecuteResponse:
    status = body.get("status") or {}
    status_id = int(status.get("id", 13))
    time_raw = body.get("time")
    memory_raw = body.get("memory")
    try:
        time_seconds = float(time_raw) if time_raw is not None else None
    except (TypeError, ValueError):
        time_seconds = None
    try:
        memory_kb = int(memory_raw) if memory_raw is not None else None
    except (TypeError, ValueError):
        memory_kb = None

    return ExecuteResponse(
        outcome=_outcome(status_id),
        status_id=status_id,
        status_text=str(status.get("description", "Unknown")),
        stdout=_b64d(body.get("stdout")),
        stderr=_b64d(body.get("stderr")),
        compile_output=_b64d(body.get("compile_output")),
        message=_b64d(body.get("message")),
        time_seconds=time_seconds,
        memory_kb=memory_kb,
    )


class Judge0Client:
    def __init__(
        self,
        settings: Settings,
        transport: Transport = httpx_transport,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.settings = settings
        self._transport = transport
        self._sleep = sleep
        self._clock = clock

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.settings.judge0_api_host:  # RapidAPI
            headers["X-RapidAPI-Key"] = self.settings.judge0_api_key
            headers["X-RapidAPI-Host"] = self.settings.judge0_api_host
        elif self.settings.judge0_api_key:  # self-hosted Judge0 with AUTHN_TOKEN enabled
            headers["X-Auth-Token"] = self.settings.judge0_api_key
        return headers

    async def _call(self, method: str, path: str, *, params: dict | None = None, json: Any = None) -> dict:
        try:
            status, body = await self._transport(
                method, f"{self.settings.judge0_url}{path}", headers=self._headers(), params=params, json=json, timeout=15.0
            )
        except TransportError as exc:
            if exc.timed_out:
                raise ExecutionUnavailable("The execution service took too long to respond.", 504, "execution_timeout") from exc
            raise ExecutionUnavailable("Couldn't reach the execution service.", 502, "execution_unreachable") from exc

        # Error messages are deliberately generic: never echo upstream bodies, which could contain secrets.
        if status == 429:
            raise ExecutionUnavailable("The execution service is busy. Try again in a moment.", 503, "execution_busy")
        if status in (401, 403):
            raise ExecutionUnavailable("The execution service rejected the server's credentials. Check JUDGE0_API_KEY.", 502, "execution_auth")
        if status == 422:
            raise ExecutionUnavailable("The execution service rejected this submission.", 502, "execution_rejected")
        if status >= 400:
            raise ExecutionUnavailable("The execution service returned an error.", 502, "execution_error")
        if not isinstance(body, dict):
            raise ExecutionUnavailable("The execution service sent an unreadable response.", 502, "execution_error")
        return body

    async def run(self, language: str, source_code: str, stdin: str) -> ExecuteResponse:
        if not self.settings.execution_configured:
            raise ExecutionNotConfigured()

        payload: dict[str, Any] = {
            "language_id": self.settings.lang_ids[language],
            "source_code": _b64e(source_code),
            "stdin": _b64e(stdin),
        }
        if self.settings.judge0_cpu_time_limit > 0:
            payload["cpu_time_limit"] = self.settings.judge0_cpu_time_limit

        created = await self._call("POST", "/submissions", params={"base64_encoded": "true", "wait": "false"}, json=payload)
        token = created.get("token")
        if not isinstance(token, str) or not token:
            raise ExecutionUnavailable("The execution service did not accept the submission.", 502, "execution_error")

        deadline = self._clock() + self.settings.judge0_poll_timeout
        while True:
            body = await self._call("GET", f"/submissions/{token}", params={"base64_encoded": "true"})
            status_id = (body.get("status") or {}).get("id")
            if isinstance(status_id, int) and status_id not in _PENDING:
                return normalise(body)
            if self._clock() >= deadline:
                raise ExecutionUnavailable("Timed out waiting for the program to finish.", 504, "execution_timeout")
            await self._sleep(self.settings.judge0_poll_interval)
