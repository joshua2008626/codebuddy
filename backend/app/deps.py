"""Small request helpers shared by routers."""
from __future__ import annotations

from typing import Any


def client_key(request: Any, trust_proxy: bool) -> str:
    """Identifies the caller for rate limiting.

    With trust_proxy, uses the LAST X-Forwarded-For entry, the one appended by our own proxy.
    Earlier entries are supplied by the client and can be forged.
    """
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[-1]
    client = getattr(request, "client", None)
    return client.host if client and client.host else "unknown"
