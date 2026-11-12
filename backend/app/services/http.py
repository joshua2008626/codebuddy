"""Shared HTTP transport used by the Judge0 and LLM clients.

A transport performs one HTTP call and returns (status_code, parsed_json_or_None). Keeping it behind a
small callable lets tests swap in a scripted fake instead of the network.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable


class TransportError(Exception):
    """Raised by a transport when the request could not complete (network failure or timeout)."""

    def __init__(self, timed_out: bool):
        super().__init__("timeout" if timed_out else "network error")
        self.timed_out = timed_out


Transport = Callable[..., Awaitable[tuple[int, Any]]]


async def httpx_transport(method: str, url: str, *, headers: dict, params: dict | None, json: Any, timeout: float):
    """Production transport. httpx is imported lazily so the rest of the code works without it installed."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(method, url, headers=headers, params=params, json=json)
    except httpx.TimeoutException as exc:
        raise TransportError(timed_out=True) from exc
    except httpx.HTTPError as exc:
        raise TransportError(timed_out=False) from exc
    try:
        body = resp.json()
    except ValueError:
        body = None
    return resp.status_code, body
