"""Security helpers: password hashing and rules, session tokens, origin and cookie settings.

Everything here is plain Python with no web or database imports, so it is unit-tested directly.

Passwords use scrypt from the standard library (an OWASP-recommended password hash) with a random salt
per password. The parameters are stored inside each hash string, so they can be raised later and old
hashes are upgraded the next time that user logs in (see needs_rehash).
"""
from __future__ import annotations

import base64
import functools
import hashlib
import hmac
import re
import secrets
import unicodedata
from typing import Iterable

# ----------------------------------------------------------------------------- password hashing
# OWASP lists scrypt N=2^15, r=8, p=3 (about 32 MiB of memory) as an acceptable minimum configuration.
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 3
SCRYPT_DKLEN = 32
SCRYPT_MAXMEM = 128 * 1024 * 1024
_MAX_STORED_N = 2**20  # refuse absurd parameters in a stored hash, so a tampered row cannot exhaust memory


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _prepare(password: str) -> bytes:
    # NFKC makes visually identical passwords (e.g. composed vs decomposed accents) hash the same.
    return unicodedata.normalize("NFKC", password).encode("utf-8")


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int, dklen: int) -> bytes:
    return hashlib.scrypt(_prepare(password), salt=salt, n=n, r=r, p=p, maxmem=SCRYPT_MAXMEM, dklen=dklen)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_DKLEN)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def _parse(stored: str) -> tuple[int, int, int, bytes, bytes] | None:
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
        if scheme != "scrypt":
            return None
        n_i, r_i, p_i = int(n), int(r), int(p)
        if not (2 <= n_i <= _MAX_STORED_N and n_i & (n_i - 1) == 0 and 1 <= r_i <= 32 and 1 <= p_i <= 16):
            return None
        return n_i, r_i, p_i, base64.b64decode(salt, validate=True), base64.b64decode(digest, validate=True)
    except (ValueError, TypeError):
        return None


def verify_password(password: str, stored: str) -> bool:
    """True only if the password matches. Malformed stored values simply return False."""
    parsed = _parse(stored)
    if parsed is None:
        return False
    n, r, p, salt, expected = parsed
    try:
        actual = _scrypt(password, salt, n, r, p, len(expected))
    except (ValueError, MemoryError):
        return False
    return hmac.compare_digest(actual, expected)


def needs_rehash(stored: str) -> bool:
    parsed = _parse(stored)
    return parsed is None or parsed[:3] != (SCRYPT_N, SCRYPT_R, SCRYPT_P)


@functools.lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return hash_password("dummy password used only to equalise timing")


def verify_or_dummy(password: str, stored: str | None) -> bool:
    """Verifies against `stored`, or against a throwaway hash when there is no such user.

    Doing the same amount of work either way stops response time from revealing whether an email is registered.
    """
    if stored is None:
        verify_password(password, _dummy_hash())
        return False
    return verify_password(password, stored)


# ----------------------------------------------------------------------------- password rules
MIN_PASSWORD = 10
MAX_PASSWORD = 128

# A short list of the most common passwords that still meet the length rule. It catches the worst choices,
# but it is not a substitute for a breached-password check (noted in the deployment checklist).
_COMMON = frozenset(
    "password123 password1234 1234567890 12345678910 123456789012 qwertyuiop qwerty12345 qwertyuiop123 "
    "letmein1234 iloveyou123 welcome1234 admin12345 administrator abcdefghij abcd123456 1q2w3e4r5t "
    "passw0rd123 changeme123 football123 monkey12345 dragon12345 trustno1234 superman123 0123456789".split()
)


def password_problem(password: str, email: str = "") -> str | None:
    """Returns a plain-language reason the password is not acceptable, or None if it is fine."""
    if len(password) < MIN_PASSWORD:
        return f"Use at least {MIN_PASSWORD} characters."
    if len(password) > MAX_PASSWORD:
        return f"Use at most {MAX_PASSWORD} characters."
    if "\x00" in password:
        return "That password contains a character that isn't allowed."
    folded = password.casefold()
    if folded in _COMMON:
        return "That password is too common. Pick something harder to guess."
    if len(set(password)) < 4:
        return "That password repeats too few different characters."
    if email:
        local = email.strip().casefold().split("@")[0]
        if folded == email.strip().casefold() or (len(local) >= 4 and folded == local):
            return "Your password can't be your email address."
    return None


# ----------------------------------------------------------------------------------------- email
_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    """Practical check, not full RFC 5322. Internationalised domains must be given in their ASCII (punycode) form."""
    if len(email) > 254 or ".." in email:
        return False
    local = email.split("@")[0]
    if len(local) > 64 or local.startswith(".") or local.endswith("."):
        return False
    return bool(_EMAIL_RE.match(email))


# ----------------------------------------------------------------------------- session tokens
def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Only this hash is stored, so a copy of the database does not contain usable session tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------------- origin and cookie
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def origin_allowed(origin: str | None, allowed: Iterable[str]) -> bool:
    """CSRF defence for cookie auth. A browser always sends Origin on cross-site POSTs, so one that is not ours is refused.

    A missing Origin means a non-browser client (curl, tests) or a same-site request, and passes.
    """
    if origin is None:
        return True
    return origin.rstrip("/") in {a.rstrip("/") for a in allowed}


COOKIE_NAME = "cb_session"


def cookie_options(*, secure: bool, ttl_days: int) -> dict:
    """Settings for the session cookie: unreadable by scripts, not sent on cross-site POSTs, HTTPS-only in production."""
    return {"httponly": True, "samesite": "lax", "secure": secure, "path": "/", "max_age": ttl_days * 24 * 3600}


# ------------------------------------------------------------------------------------ database url
def normalize_database_url(url: str) -> str:
    """Accepts the URL forms hosting providers hand out and returns one SQLAlchemy can use with psycopg 3."""
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url
