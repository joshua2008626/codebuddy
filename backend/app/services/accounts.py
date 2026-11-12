"""Database operations for users and login sessions. Kept thin: the rules live in app.security."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import AuthSession, User, utcnow
from ..security import hash_token, new_session_token


class EmailTaken(Exception):
    pass


def _aware(moment: datetime) -> datetime:
    # SQLite returns naive datetimes even for timezone-aware columns; everything we store is UTC.
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def create_user(db: Session, email: str, display_name: str, password_hash: str) -> User:
    user = User(email=email, display_name=display_name, password_hash=password_hash)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two signups racing for one email: the unique constraint decides, so the loser lands here.
        db.rollback()
        raise EmailTaken() from None
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_session(db: Session, user: User, ttl_days: int, now: datetime | None = None) -> str:
    """Returns the raw token, which goes in the cookie. It is never stored, only its hash is."""
    now = now or utcnow()
    token = new_session_token()
    db.add(AuthSession(user_id=user.id, token_hash=hash_token(token), created_at=now, expires_at=now + timedelta(days=ttl_days)))
    db.commit()
    return token


def user_for_token(db: Session, token: str, now: datetime | None = None) -> User | None:
    now = now or utcnow()
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    if session is None:
        return None
    if _aware(session.expires_at) <= now:
        db.delete(session)
        db.commit()
        return None
    return db.get(User, session.user_id)


def delete_session(db: Session, token: str) -> None:
    db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_token(token)))
    db.commit()


def delete_other_sessions(db: Session, user_id: str, keep_token: str) -> None:
    """Signs a user out everywhere except the browser they are using (after a password change)."""
    db.execute(delete(AuthSession).where(AuthSession.user_id == user_id, AuthSession.token_hash != hash_token(keep_token)))
    db.commit()


def purge_expired(db: Session, now: datetime | None = None) -> None:
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= (now or utcnow())))
    db.commit()


def update_display_name(db: Session, user: User, display_name: str) -> User:
    user.display_name = display_name
    db.commit()
    return user


def update_password_hash(db: Session, user: User, password_hash: str) -> None:
    user.password_hash = password_hash
    db.commit()


def delete_user(db: Session, user: User) -> None:
    # Explicit deletes, so this works on SQLite too, where foreign-key cascades are off by default.
    from . import projects  # imported here to avoid a circular import at module load

    projects.delete_all_for_user(db, user.id)
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    db.delete(user)
    db.commit()
