"""Dependencies shared by routers."""
from __future__ import annotations

import math

from fastapi import HTTPException, Request

from ..deps import client_key


def rate_limit(bucket: str, action: str):
    """Returns a FastAPI dependency that applies the named limiter (created in create_app)."""

    def dependency(request: Request) -> None:
        state = request.app.state
        allowed, retry_after = state.limiters[bucket].check(client_key(request, state.settings.trust_proxy))
        if not allowed:
            seconds = max(1, math.ceil(retry_after))
            raise HTTPException(
                status_code=429,
                detail={"code": "rate_limited", "message": f"You're {action} too quickly. Try again in {seconds} seconds."},
                headers={"Retry-After": str(seconds)},
            )

    return dependency


# ------------------------------------------------------------------------------ database and auth
from typing import Iterator  # noqa: E402

from fastapi import Depends  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from ..models import User  # noqa: E402
from ..security import COOKIE_NAME, SAFE_METHODS, origin_allowed  # noqa: E402
from ..services import accounts  # noqa: E402


def get_db(request: Request) -> Iterator[Session]:
    db = request.app.state.db_factory()
    try:
        yield db
    finally:
        db.close()


def enforce_origin(request: Request) -> None:
    """CSRF defence, applied to every route: state-changing requests from a browser must come from our own site."""
    if request.method in SAFE_METHODS:
        return
    if not origin_allowed(request.headers.get("origin"), request.app.state.settings.cors_origins):
        raise HTTPException(status_code=403, detail={"code": "bad_origin", "message": "This request came from a site that isn't allowed."})


NOT_AUTHENTICATED = {"code": "not_authenticated", "message": "Log in to continue."}


def session_token(request: Request) -> str | None:
    return request.cookies.get(COOKIE_NAME) or None


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = session_token(request)
    user = accounts.user_for_token(db, token) if token else None
    if user is None:
        raise HTTPException(status_code=401, detail=NOT_AUTHENTICATED)
    return user
