"""End-to-end tests of the account routes through FastAPI's TestClient, against in-memory SQLite.

They need: pip install -r requirements.txt  (fastapi, sqlalchemy, httpx).

NOTE: written without being able to run them (FastAPI and SQLAlchemy could not be installed where this was
authored). If one fails on your machine, the failure is real information: please report it.
"""
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import AuthSession, User  # noqa: E402
from app.security import COOKIE_NAME, hash_password  # noqa: E402
from app.services import accounts  # noqa: E402

ORIGIN = "http://localhost:5173"
PW = "correct horse battery staple"
SIGNUP = {"email": "asha@example.com", "display_name": "Asha", "password": PW}


def build_app(**overrides):
    settings = Settings(database_url="sqlite://", rate_limit_auth_per_min=1000, cors_origins=(ORIGIN,), **overrides)
    return create_app(settings)


@pytest.fixture()
def app():
    return build_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as c:  # the `with` runs startup, which creates the tables
        yield c


def sign_up(c, **kw):
    return c.post("/api/auth/signup", json={**SIGNUP, **kw})


def log_in(c, email="asha@example.com", password=PW):
    return c.post("/api/auth/login", json={"email": email, "password": password})


def db_rows(app, model):
    with app.state.db_factory() as db:
        return db.scalars(select(model)).all()


# -------------------------------------------------------------------------- signup
def test_signup_creates_account_logs_in_and_returns_no_secrets(client):
    r = sign_up(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "asha@example.com" and body["display_name"] == "Asha"
    assert "password" not in str(body).lower() and "hash" not in str(body).lower()
    assert client.get("/api/auth/me").json()["email"] == "asha@example.com"  # the cookie from signup works


def test_session_cookie_attributes(client):
    cookie = sign_up(client).headers["set-cookie"].lower()
    assert f"{COOKIE_NAME}=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    assert "secure" not in cookie  # off by default, so plain-http development works


def test_cookie_is_secure_when_configured():
    c = TestClient(build_app(cookie_secure=True))
    with c:
        assert "secure" in sign_up(c).headers["set-cookie"].lower()


def test_passwords_and_session_tokens_are_not_stored_in_plain_text(app, client):
    r = sign_up(client)
    token = client.cookies.get(COOKIE_NAME)
    user = db_rows(app, User)[0]
    assert user.password_hash.startswith("scrypt$") and PW not in user.password_hash
    assert all(token not in (s.token_hash, s.id) for s in db_rows(app, AuthSession))
    assert r.status_code == 201


def test_duplicate_email_is_refused_ignoring_case(client):
    sign_up(client)
    r = sign_up(client, email="ASHA@Example.com")
    assert r.status_code == 409 and r.json()["detail"]["code"] == "email_taken"


@pytest.mark.parametrize("override", [{"email": "nope"}, {"password": "short"}, {"password": "password123"}, {"display_name": "  "}])
def test_invalid_signups_are_422_with_a_readable_message(client, override):
    r = sign_up(client, **override)
    assert r.status_code == 422 and r.json()["detail"][0]["msg"]


# ---------------------------------------------------------------------------- login
def test_login_works_and_email_is_case_insensitive(client):
    sign_up(client)
    client.cookies.clear()
    assert log_in(client, email=" ASHA@example.com ").status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_wrong_password_and_unknown_email_look_identical(client):
    sign_up(client)
    client.cookies.clear()
    wrong = log_in(client, password="not the password!!")
    unknown = log_in(client, email="ghost@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert COOKIE_NAME not in client.cookies


def test_repeated_failures_lock_further_attempts_even_with_the_right_password():
    c = TestClient(build_app(login_max_failures=3))
    with c:
        sign_up(c)
        c.cookies.clear()
        for _ in range(3):
            assert log_in(c, password="wrong wrong wrong").status_code == 401
        blocked = log_in(c)  # correct password, but the key is locked
        assert blocked.status_code == 429 and int(blocked.headers["retry-after"]) > 0


def test_old_weak_hash_is_upgraded_on_login(app, client):
    import hashlib

    from app.security import SCRYPT_N, _b64, needs_rehash

    sign_up(client)
    salt = b"0123456789abcdef"
    cheap = f"scrypt$16384$8$1${_b64(salt)}${_b64(hashlib.scrypt(PW.encode(), salt=salt, n=16384, r=8, p=1, dklen=32))}"
    with app.state.db_factory() as db:
        user = db.scalars(select(User)).one()
        user.password_hash = cheap
        db.commit()
    client.cookies.clear()
    assert log_in(client).status_code == 200
    assert not needs_rehash(db_rows(app, User)[0].password_hash) and SCRYPT_N > 16384


# --------------------------------------------------------------------- sessions / me
def test_me_requires_login(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401 and r.json()["detail"]["code"] == "not_authenticated"


def test_garbage_cookie_is_not_logged_in(client):
    client.cookies.set(COOKIE_NAME, "totally-made-up")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_the_cookie_and_revokes_the_session_on_the_server(client):
    sign_up(client)
    token = client.cookies.get(COOKIE_NAME)
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set(COOKIE_NAME, token)  # replaying the old cookie must not work either
    assert client.get("/api/auth/me").status_code == 401


def test_logout_without_a_session_is_fine(client):
    assert client.post("/api/auth/logout").status_code == 204


def test_expired_session_is_rejected(app, client):
    sign_up(client)
    with app.state.db_factory() as db:
        user = db.scalars(select(User)).one()
        old = accounts.create_session(db, user, ttl_days=1, now=datetime.now(timezone.utc) - timedelta(days=3))
    client.cookies.set(COOKIE_NAME, old)
    assert client.get("/api/auth/me").status_code == 401


def test_update_display_name(client):
    sign_up(client)
    r = client.patch("/api/auth/me", json={"display_name": "  Asha   Rao "})
    assert r.status_code == 200 and r.json()["display_name"] == "Asha Rao"
    assert client.patch("/api/auth/me", json={"display_name": "  "}).status_code == 422


def test_profile_changes_require_login(client):
    assert client.patch("/api/auth/me", json={"display_name": "X"}).status_code == 401
    assert client.post("/api/auth/me/password", json={"current_password": "a", "new_password": PW}).status_code == 401
    assert client.post("/api/auth/me/delete", json={"password": PW}).status_code == 401


# ------------------------------------------------------------------ csrf / origin
def test_post_from_another_origin_is_refused(client):
    r = client.post("/api/auth/login", json={"email": "a@b.co", "password": "x"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "bad_origin"


def test_cross_site_logout_cannot_log_you_out(client):
    sign_up(client)
    assert client.post("/api/auth/logout", headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.get("/api/auth/me").status_code == 200


def test_our_own_origin_and_missing_origin_are_fine(client):
    assert log_in(client).status_code == 401  # reaches the login logic (bad credentials), not blocked
    r = client.post("/api/auth/login", json={"email": "a@b.co", "password": "x"}, headers={"Origin": ORIGIN})
    assert r.status_code == 401


# --------------------------------------------------------------- change password
def test_change_password_signs_out_other_browsers_only(app, client):
    sign_up(client)
    other = TestClient(app)  # a second browser (no `with`: the tables already exist)
    assert log_in(other).status_code == 200

    r = client.post("/api/auth/me/password", json={"current_password": PW, "new_password": "a brand new passphrase"})
    assert r.status_code == 204
    assert client.get("/api/auth/me").status_code == 200  # this browser stays logged in
    assert other.get("/api/auth/me").status_code == 401  # the other one is signed out

    client.cookies.clear()
    assert log_in(client).status_code == 401  # old password no longer works
    assert log_in(client, password="a brand new passphrase").status_code == 200


def test_change_password_checks_current_and_new(client):
    sign_up(client)
    wrong = client.post("/api/auth/me/password", json={"current_password": "nope nope nope", "new_password": "a brand new passphrase"})
    assert wrong.status_code == 403 and wrong.json()["detail"]["code"] == "wrong_password"
    weak = client.post("/api/auth/me/password", json={"current_password": PW, "new_password": "short"})
    assert weak.status_code == 422 and "10 characters" in weak.json()["detail"][0]["msg"]


# ------------------------------------------------------------------ delete account
def test_delete_account(app, client):
    sign_up(client)
    assert client.post("/api/auth/me/delete", json={"password": "wrong wrong wrong"}).status_code == 403
    assert client.get("/api/auth/me").status_code == 200  # a wrong password deleted nothing

    assert client.post("/api/auth/me/delete", json={"password": PW}).status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    assert db_rows(app, User) == [] and db_rows(app, AuthSession) == []
    assert log_in(client).status_code == 401


def test_health_still_works(client):
    assert client.get("/api/health").json()["status"] == "ok"
