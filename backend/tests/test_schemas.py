import pytest
from pydantic import ValidationError

from app.schemas import MAX_SOURCE_CHARS, MAX_STDIN_CHARS, ExecuteRequest


def test_valid_request_with_default_stdin():
    req = ExecuteRequest(language="python", source_code="print(1)")
    assert req.stdin == ""


@pytest.mark.parametrize("lang", ["ruby", "", "PYTHON", "c++"])
def test_unsupported_language_rejected(lang):
    with pytest.raises(ValidationError):
        ExecuteRequest(language=lang, source_code="x")


@pytest.mark.parametrize("code", ["", "   \n\t  "])
def test_empty_or_blank_source_rejected(code):
    with pytest.raises(ValidationError):
        ExecuteRequest(language="c", source_code=code)


def test_source_length_limit():
    ExecuteRequest(language="c", source_code="x" * MAX_SOURCE_CHARS)
    with pytest.raises(ValidationError):
        ExecuteRequest(language="c", source_code="x" * (MAX_SOURCE_CHARS + 1))


def test_stdin_length_limit():
    ExecuteRequest(language="c", source_code="x", stdin="y" * MAX_STDIN_CHARS)
    with pytest.raises(ValidationError):
        ExecuteRequest(language="c", source_code="x", stdin="y" * (MAX_STDIN_CHARS + 1))


def test_null_bytes_rejected_in_source_and_stdin():
    with pytest.raises(ValidationError):
        ExecuteRequest(language="java", source_code="a\x00b")
    with pytest.raises(ValidationError):
        ExecuteRequest(language="java", source_code="ok", stdin="a\x00b")


def test_missing_fields_rejected():
    with pytest.raises(ValidationError):
        ExecuteRequest(language="python")


# ------------------------------------------------------------------------------------ accounts
from datetime import datetime, timezone  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from app.schemas import ChangePasswordRequest, LoginRequest, SignupRequest, UpdateProfileRequest, UserOut  # noqa: E402

GOOD = {"email": "asha@example.com", "display_name": "Asha", "password": "correct horse battery"}


def signup(**kw):
    return SignupRequest(**{**GOOD, **kw})


def test_signup_normalises_email_and_name():
    r = signup(email="  Asha@Example.COM ", display_name="  Asha    Rao ")
    assert (r.email, r.display_name) == ("asha@example.com", "Asha Rao")


@pytest.mark.parametrize("field,value,fragment", [
    ("email", "not-an-email", "valid email"),
    ("email", "a" * 255, None),
    ("display_name", "   ", "Enter a name"),
    ("display_name", "bad\x07name", "control characters"),
    ("display_name", "x" * 61, None),
    ("password", "short", "at least 10"),
    ("password", "password123", "too common"),
    ("password", "x" * 130, None),
])
def test_signup_rejections(field, value, fragment):
    with pytest.raises(ValidationError) as e:
        signup(**{field: value})
    if fragment:
        assert fragment in str(e.value)


def test_signup_password_may_not_be_the_email_name():
    with pytest.raises(ValidationError) as e:
        signup(email="ashawilliams@example.com", password="ashawilliams")
    assert "email" in str(e.value)


def test_login_does_not_apply_signup_password_rules():
    # An account made under an older, weaker rule must still be able to log in.
    assert LoginRequest(email=" A@B.com ", password="x").email == "a@b.com"
    with pytest.raises(ValidationError):
        LoginRequest(email="a@b.com", password="")


def test_profile_and_password_requests():
    assert UpdateProfileRequest(display_name="  A  B ").display_name == "A B"
    with pytest.raises(ValidationError):
        UpdateProfileRequest(display_name="   ")
    with pytest.raises(ValidationError):
        ChangePasswordRequest(current_password="", new_password="whatever long enough")


def test_user_out_is_built_from_a_database_row_and_has_no_secrets():
    row = SimpleNamespace(id="u1", email="a@b.co", display_name="A", password_hash="scrypt$secret", created_at=datetime.now(timezone.utc))
    out = UserOut.model_validate(row)
    assert set(out.model_dump()) == {"id", "email", "display_name", "created_at"}
    assert "scrypt" not in out.model_dump_json()
