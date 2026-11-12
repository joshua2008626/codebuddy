import io
import zipfile
from datetime import datetime, timezone

import pytest

from app import projects_logic as pl

WHEN = datetime(2026, 11, 11, 10, 30, 41, tzinfo=timezone.utc)


@pytest.mark.parametrize("name,lang", [("a.py", "python"), ("Main.java", "java"), ("x.C", "c"), ("hello.world.py", "python")])
def test_language_from_extension(name, lang):
    assert pl.language_for_filename(name) == lang


@pytest.mark.parametrize("name", ["a.txt", "py", ".py", "noext", "a.pyc", "a.py.txt"])
def test_unsupported_names_have_no_language(name):
    assert pl.language_for_filename(name) is None


@pytest.mark.parametrize("name", ["main.py", "Main.java", "a_b-c.1.c", "_x.py", "9lives.c", "x" * 60 + ".py"])
def test_valid_file_names(name):
    assert pl.file_name_problem(name) is None


@pytest.mark.parametrize("name", [
    "", ".py", "../x.py", "a/b.py", "a\\b.py", "..\\x.c", "-x.py", ".hidden.py", "a b.py", "a.py\n", "a\x00.py",
    "x" * 70 + ".py", "café.py", "con:.py", "a.txt", "noext",
])
def test_invalid_file_names_including_path_tricks(name):
    assert pl.file_name_problem(name) is not None


def test_project_names():
    assert pl.project_name_problem("  My first project ") is None
    assert pl.clean_project_name("  My   first \t project ") == "My first project"
    assert pl.project_name_problem("   ") and pl.project_name_problem("x" * 61) and pl.project_name_problem("a\x07b")
    assert pl.project_name_problem("x" * 60) is None


def test_duplicate_names_ignore_case():
    assert pl.duplicate_names(["a.py", "B.py", "A.PY"]) == ["A.PY"]
    assert pl.duplicate_names(["a.py", "b.py"]) == []


@pytest.mark.parametrize("given,expected", [
    ("My First Project", "codebuddy-my-first-project.zip"),
    ("  ---  ", "codebuddy-project.zip"),
    ("../../etc/passwd", "codebuddy-etc-passwd.zip"),
    ('evil"\r\nSet-Cookie: x=1', "codebuddy-evil-set-cookie-x-1.zip"),
    ("café ☃", "codebuddy-caf.zip"),
    ("x" * 100, "codebuddy-" + "x" * 40 + ".zip"),
])
def test_zip_download_name_is_header_safe(given, expected):
    name = pl.zip_download_name(given)
    assert name == expected
    assert all(c.isalnum() or c in "-." for c in name)


def test_zip_round_trip_with_exact_contents():
    files = [("main.py", "print('héllo')\n"), ("Main.java", "class Main {}\n")]
    data = pl.build_zip(files, WHEN)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.testzip() is None
        assert sorted(zf.namelist()) == ["Main.java", "main.py"]
        assert zf.read("main.py").decode("utf-8") == "print('héllo')\n"
        assert oct(zf.getinfo("main.py").external_attr >> 16) == "0o644"
        assert zf.getinfo("main.py").date_time == (2026, 11, 11, 10, 30, 40)  # zip stores even seconds


def test_zip_refuses_bad_names_and_duplicates():
    for bad in ["../evil.py", "/abs.py", "a/b.py", "x.txt"]:
        with pytest.raises(ValueError):
            pl.build_zip([(bad, "x")], WHEN)
    with pytest.raises(ValueError):
        pl.build_zip([("a.py", "1"), ("A.py", "2")], WHEN)


def test_zip_of_nothing_is_valid_and_old_dates_are_clamped():
    data = pl.build_zip([], datetime(1970, 1, 1))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.namelist() == []
    data = pl.build_zip([("a.py", "x")], datetime(1970, 1, 1))  # zip cannot store dates before 1980
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.getinfo("a.py").date_time[0] == 1980


def test_default_templates_cover_every_language_and_use_a_valid_name():
    assert set(pl.TEMPLATES) == set(pl.DEFAULT_FILE_NAMES) == {"python", "c", "java"}
    for lang, name in pl.DEFAULT_FILE_NAMES.items():
        assert pl.file_name_problem(name) is None and pl.language_for_filename(name) == lang
    assert "public class Main" in pl.TEMPLATES["java"]
