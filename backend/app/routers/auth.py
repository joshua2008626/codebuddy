"""Accounts: sign up, log in, log out, profile, change password, delete account.

These are plain `def` routes on purpose: password hashing takes a fraction of a second of CPU, and FastAPI
runs `def` routes in a worker thread so that does not block other requests.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..deps import client_key
from ..schemas import (
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    SignupRequest,
    UpdateProfileRequest,
    UserOut,
)
from ..security import (
    COOKIE_NAME,
    cookie_options,
    hash_password,
    needs_rehash,
    password_problem,
    verify_or_dummy,
    verify_password,
)
from ..services import accounts
from .common import current_user, get_db, rate_limit, session_token
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

BAD_LOGIN = {"code": "invalid_credentials", "message": "Email or password is incorrect."}
WRONG_PASSWORD = {"code": "wrong_password", "message": "That password isn't correct."}


def _set_cookie(request: Request, response: Response, token: str) -> None:
    s = request.app.state.settings
    response.set_cookie(COOKIE_NAME, token, **cookie_options(secure=s.cookie_secure, ttl_days=s.session_ttl_days))


def _clear_cookie(request: Request, response: Response) -> None:
    s = request.app.state.settings
    # Must repeat the same attributes, or some browsers will not remove the cookie.
    response.delete_cookie(COOKIE_NAME, path="/", secure=s.cookie_secure, httponly=True, samesite="lax")


@router.post("/signup", response_model=UserOut, status_code=201, dependencies=[Depends(rate_limit("auth", "trying to sign up"))])
def signup(body: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> User:
    # Validation (email format, password rules, name) already happened in SignupRequest.
    if accounts.get_user_by_email(db, body.email) is not None:
        raise HTTPException(status_code=409, detail={"code": "email_taken", "message": "An account with that email already exists. Try logging in."})
    try:
        user = accounts.create_user(db, body.email, body.display_name, hash_password(body.password))
    except accounts.EmailTaken:
        raise HTTPException(status_code=409, detail={"code": "email_taken", "message": "An account with that email already exists. Try logging in."})
    token = accounts.create_session(db, user, request.app.state.settings.session_ttl_days)
    _set_cookie(request, response, token)
    return user


@router.post("/login", response_model=UserOut, dependencies=[Depends(rate_limit("auth", "trying to log in"))])
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> User:
    state = request.app.state
    ip = client_key(request, state.settings.trust_proxy)
    pair_key, email_key = f"{ip}|{body.email}", body.email

    # Two throttles: failures from this client for this email (stops guessing), and failures for this email from
    # anywhere (stops a spread-out attack). The second has a higher limit so one person can't easily lock you out.
    wait = max(state.login_throttle.retry_after(pair_key), state.login_throttle_email.retry_after(email_key))
    if wait > 0:
        seconds = int(wait) + 1
        raise HTTPException(
            status_code=429,
            detail={"code": "too_many_attempts", "message": f"Too many failed attempts. Try again in {max(1, seconds // 60)} minute(s)."},
            headers={"Retry-After": str(seconds)},
        )

    user = accounts.get_user_by_email(db, body.email)
    ok = verify_or_dummy(body.password, user.password_hash if user else None)
    if not ok or user is None:
        state.login_throttle.record_failure(pair_key)
        state.login_throttle_email.record_failure(email_key)
        raise HTTPException(status_code=401, detail=BAD_LOGIN)  # same message whether the email exists or not

    state.login_throttle.reset(pair_key)
    if needs_rehash(user.password_hash):  # upgrade old hashes while we have the plaintext password
        accounts.update_password_hash(db, user, hash_password(body.password))
    accounts.purge_expired(db)
    token = accounts.create_session(db, user, state.settings.session_ttl_days)
    _set_cookie(request, response, token)
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, db: Session = Depends(get_db)) -> Response:
    token = session_token(request)
    if token:
        accounts.delete_session(db, token)  # revoked on the server, so a copied cookie stops working too
    out = Response(status_code=204)
    _clear_cookie(request, out)
    return out


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: UpdateProfileRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    return accounts.update_display_name(db, user, body.display_name)


@router.post("/me/password", status_code=204, dependencies=[Depends(rate_limit("auth", "changing your password"))])
def change_password(body: ChangePasswordRequest, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=403, detail=WRONG_PASSWORD)
    problem = password_problem(body.new_password, user.email)
    if problem:
        raise HTTPException(status_code=422, detail=[{"msg": problem.rstrip(".")}])
    accounts.update_password_hash(db, user, hash_password(body.new_password))
    token = session_token(request)
    if token:
        accounts.delete_other_sessions(db, user.id, token)  # other browsers are signed out
    return Response(status_code=204)


@router.post("/me/delete", status_code=204, dependencies=[Depends(rate_limit("auth", "deleting your account"))])
def delete_me(body: DeleteAccountRequest, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=403, detail=WRONG_PASSWORD)
    accounts.delete_user(db, user)
    out = Response(status_code=204)
    _clear_cookie(request, out)
    return out
