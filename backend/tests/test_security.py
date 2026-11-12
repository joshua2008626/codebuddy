import hashlib

import pytest

from app import security as sec


# ---------------------------------------------------------------- hashing
def test_hash_then_verify_round_trip():
    h = sec.hash_password("correct horse battery")
    assert sec.verify_password("correct horse battery", h)
    assert not sec.verify_password("correct horse batterY", h)
    assert not sec.verify_password("", h)


def test_hash_format_and_no_plaintext():
    pw = "my secret passphrase"
    h = sec.hash_password(pw)
    scheme, n, r, p, salt, digest = h.split("$")
    assert (scheme, int(n), int(r), int(p)) == ("scrypt", sec.SCRYPT_N, sec.SCRYPT_R, sec.SCRYPT_P)
    assert pw not in h


def test_same_password_hashes_differently_each_time():
    assert sec.hash_password("same password!") != sec.hash_password("same password!")


@pytest.mark.parametrize("bad", ["", "nonsense", "scrypt$1$2$3", "bcrypt$1$2$3$4$5", "scrypt$x$8$3$AAAA$AAAA",
                                 "scrypt$32768$8$3$!!!$AAAA", "scrypt$3$8$3$AAAA$AAAA", "scrypt$99999999$8$3$AAAA$AAAA"])
def test_malformed_or_hostile_stored_values_are_rejected_without_crashing(bad):
    assert sec.verify_password("anything", bad) is False
    assert sec.needs_rehash(bad) is True


def test_composed_and_decomposed_unicode_passwords_match():
    composed, decomposed = "café passphrase", "café passphrase"
    assert composed != decomposed
    assert sec.verify_password(decomposed, sec.hash_password(composed))


def test_verify_uses_parameters_stored_in_the_hash():
    # A hash made with cheaper settings (an "old" hash) must still verify, and be flagged for upgrade.
    salt = b"0123456789abcdef"
    digest = hashlib.scrypt(b"old password!", salt=salt, n=2**14, r=8, p=1, dklen=32)
    old = f"scrypt$16384$8$1${sec._b64(salt)}${sec._b64(digest)}"
    assert sec.verify_password("old password!", old)
    assert sec.needs_rehash(old)
    assert not sec.needs_rehash(sec.hash_password("fresh password!"))


def test_verify_or_dummy_never_accepts_a_missing_user():
    assert sec.verify_or_dummy("anything at all", None) is False
    assert sec.verify_or_dummy("whatever", sec.hash_password("whatever")) is True


# ------------------------------------------------------------ password rules
@pytest.mark.parametrize("pw", ["short", "123456789", "x" * 9])
def test_too_short(pw):
    assert "at least 10" in sec.password_problem(pw)


def test_length_boundaries_and_nul():
    assert sec.password_problem("ab12" * 32) is None  # exactly 128 characters is allowed
    assert "at most 128" in sec.password_problem("ab12" * 32 + "x")  # 129 is not
    assert sec.password_problem("abcdefghi1") is None  # exactly 10 is allowed
    assert "at least 10" in sec.password_problem("abcdefgh1")  # 9 is not
    assert "isn't allowed" in sec.password_problem("good password\x00x")


@pytest.mark.parametrize("pw", ["password123", "PASSWORD123", "1234567890", "qwertyuiop"])
def test_common_passwords_rejected_case_insensitively(pw):
    assert "too common" in sec.password_problem(pw)


def test_low_variety_rejected():
    assert "repeats" in sec.password_problem("aaaaaaaaaaaa")
    assert "repeats" in sec.password_problem("abababababab")


def test_password_may_not_be_the_email_or_its_name_part():
    email = "ashawilliams@example.com"
    assert "email" in sec.password_problem("AshaWilliams@Example.com", email)  # the whole address, any case
    assert "email" in sec.password_problem("ashawilliams", email)  # the part before the @
    assert sec.password_problem("ashawilliams-2026!", email) is None  # merely containing it is fine
    assert sec.password_problem("ashawilliams", "someone.else@example.com") is None  # other people's email is irrelevant


def test_a_reasonable_passphrase_is_accepted_and_has_no_composition_rules():
    assert sec.password_problem("correct horse battery staple") is None
    assert sec.password_problem("alllowercaseletters") is None  # no forced symbols or digits


# -------------------------------------------------------------------- email
@pytest.mark.parametrize("e", ["a@b.co", "first.last+tag@sub.example.com", "x_y@ex-ample.org"])
def test_valid_emails(e):
    assert sec.is_valid_email(e)


@pytest.mark.parametrize("e", ["", "plain", "a@b", "@b.com", "a@.com", "a@b..com", "a b@c.com", "a@b.com ", ".a@b.com",
                               "a.@b.com", "a..b@c.com", "a@-b.com", "a@b-.com", "x" * 65 + "@b.com", "a@" + "b" * 250 + ".com", "a@b@c.com"])
def test_invalid_emails(e):
    assert not sec.is_valid_email(e)


def test_normalize_email():
    assert sec.normalize_email("  Asha@Example.COM ") == "asha@example.com"


# ------------------------------------------------------------ session tokens
def test_tokens_are_long_random_and_unique():
    tokens = {sec.new_session_token() for _ in range(200)}
    assert len(tokens) == 200 and all(len(t) >= 43 for t in tokens)


def test_token_hash_is_stable_and_not_the_token():
    t = sec.new_session_token()
    assert sec.hash_token(t) == sec.hash_token(t) and sec.hash_token(t) != t and len(sec.hash_token(t)) == 64
    assert sec.hash_token(t) != sec.hash_token(sec.new_session_token())


# ------------------------------------------------------------ origin / cookie
ALLOWED = ["http://localhost:5173", "https://app.example.com/"]


@pytest.mark.parametrize("origin,ok", [
    (None, True), ("http://localhost:5173", True), ("http://localhost:5173/", True), ("https://app.example.com", True),
    ("https://evil.example", False), ("http://localhost:5174", False), ("null", False), ("", False),
    ("https://app.example.com.evil.io", False), ("http://app.example.com", False),
])
def test_origin_allowed(origin, ok):
    assert sec.origin_allowed(origin, ALLOWED) is ok


def test_cookie_options():
    o = sec.cookie_options(secure=True, ttl_days=14)
    assert o == {"httponly": True, "samesite": "lax", "secure": True, "path": "/", "max_age": 14 * 86400}
    assert sec.cookie_options(secure=False, ttl_days=1)["secure"] is False


@pytest.mark.parametrize("given,expected", [
    ("postgres://u:p@h:5432/db", "postgresql+psycopg://u:p@h:5432/db"),
    ("postgresql://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ("sqlite:///./x.db", "sqlite:///./x.db"),
    ("  postgres://h/db  ", "postgresql+psycopg://h/db"),
])
def test_normalize_database_url(given, expected):
    assert sec.normalize_database_url(given) == expected


def test_oversized_stored_parameters_are_refused_before_any_hashing(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("scrypt must not be attempted with hostile parameters")

    monkeypatch.setattr(sec, "_scrypt", boom)
    too_big = 2**21  # a power of two, but above the allowed maximum
    assert sec.verify_password("x", f"scrypt${too_big}$8$3$AAAA$AAAA") is False
    assert sec.needs_rehash(f"scrypt${too_big}$8$3$AAAA$AAAA") is True
