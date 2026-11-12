"""Database-layer tests. They need SQLAlchemy (pip install -r requirements.txt) and use an in-memory SQLite database.

NOTE: written without being able to run them (SQLAlchemy could not be installed where this was authored).
If one fails on your machine, the failure is real information: please report it.
"""
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select  # noqa: E402

from app.db import create_tables, make_engine, make_session_factory  # noqa: E402
from app.models import AuthSession, User  # noqa: E402
from app.security import hash_password, hash_token  # noqa: E402
from app.services import accounts  # noqa: E402

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def db():
    engine = make_engine("sqlite://")
    create_tables(engine)
    session = make_session_factory(engine)()
    yield session
    session.close()
    engine.dispose()


def make_user(db, email="asha@example.com"):
    return accounts.create_user(db, email, "Asha", hash_password("correct horse battery"))


def test_create_and_find_user(db):
    u = make_user(db)
    assert u.id and u.created_at is not None
    assert accounts.get_user_by_email(db, "asha@example.com").id == u.id
    assert accounts.get_user_by_email(db, "nobody@example.com") is None


def test_duplicate_email_is_refused_by_the_database(db):
    make_user(db)
    with pytest.raises(accounts.EmailTaken):
        make_user(db)
    # The failed insert must not leave the session unusable.
    assert accounts.get_user_by_email(db, "asha@example.com") is not None
    assert len(db.scalars(select(User)).all()) == 1


def test_session_token_round_trip_and_only_the_hash_is_stored(db):
    u = make_user(db)
    token = accounts.create_session(db, u, ttl_days=14, now=NOW)
    stored = db.scalars(select(AuthSession)).one()
    assert stored.token_hash == hash_token(token) and token not in (stored.token_hash, stored.id)
    assert accounts.user_for_token(db, token, now=NOW + timedelta(days=1)).id == u.id


def test_unknown_token_gives_no_user(db):
    make_user(db)
    assert accounts.user_for_token(db, "not-a-real-token") is None


def test_expired_session_is_rejected_and_removed(db):
    # SQLite hands back naive datetimes; this is the case that breaks naive comparisons.
    u = make_user(db)
    token = accounts.create_session(db, u, ttl_days=14, now=NOW)
    assert accounts.user_for_token(db, token, now=NOW + timedelta(days=14, seconds=1)) is None
    assert db.scalars(select(AuthSession)).all() == []


def test_session_is_valid_just_before_expiry(db):
    u = make_user(db)
    token = accounts.create_session(db, u, ttl_days=14, now=NOW)
    assert accounts.user_for_token(db, token, now=NOW + timedelta(days=14, seconds=-1)) is not None


def test_logout_revokes_only_that_session(db):
    u = make_user(db)
    a, b = accounts.create_session(db, u, 14, NOW), accounts.create_session(db, u, 14, NOW)
    accounts.delete_session(db, a)
    assert accounts.user_for_token(db, a, NOW) is None and accounts.user_for_token(db, b, NOW) is not None
    accounts.delete_session(db, "already-gone")  # harmless


def test_delete_other_sessions_keeps_the_current_one_and_other_users(db):
    u1, u2 = make_user(db), make_user(db, "ben@example.com")
    keep, other = accounts.create_session(db, u1, 14, NOW), accounts.create_session(db, u1, 14, NOW)
    theirs = accounts.create_session(db, u2, 14, NOW)
    accounts.delete_other_sessions(db, u1.id, keep)
    assert accounts.user_for_token(db, keep, NOW) is not None
    assert accounts.user_for_token(db, other, NOW) is None
    assert accounts.user_for_token(db, theirs, NOW) is not None


def test_purge_expired_removes_only_expired(db):
    u = make_user(db)
    old = accounts.create_session(db, u, 1, now=NOW - timedelta(days=5))
    fresh = accounts.create_session(db, u, 14, now=NOW)
    accounts.purge_expired(db, now=NOW)
    assert accounts.user_for_token(db, old, NOW) is None and accounts.user_for_token(db, fresh, NOW) is not None


def test_profile_and_password_updates(db):
    u = make_user(db)
    accounts.update_display_name(db, u, "Asha Rao")
    accounts.update_password_hash(db, u, "new-hash")
    again = accounts.get_user_by_email(db, "asha@example.com")
    assert (again.display_name, again.password_hash) == ("Asha Rao", "new-hash")


def test_delete_user_removes_their_sessions_but_not_others(db):
    u1, u2 = make_user(db), make_user(db, "ben@example.com")
    accounts.create_session(db, u1, 14, NOW)
    theirs = accounts.create_session(db, u2, 14, NOW)
    accounts.delete_user(db, u1)
    assert accounts.get_user_by_email(db, "asha@example.com") is None
    assert [s.user_id for s in db.scalars(select(AuthSession)).all()] == [u2.id]
    assert accounts.user_for_token(db, theirs, NOW) is not None
