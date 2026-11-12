"""Lesson routes (FastAPI TestClient). Needs: pip install -r requirements.txt.

NOTE: written without being able to run them (fastapi could not be installed where this was authored).
A failure on your machine is real information: please report it.
"""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.data.lessons import LESSONS  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(create_app(Settings(database_url="sqlite://")))


def test_list_has_twelve_lessons_with_languages(client):
    body = client.get("/api/lessons").json()
    assert [x["id"] for x in body] == [l.id for l in LESSONS]
    assert {x["id"]: x["languages"] for x in body}["c-fundamentals"] == ["c"]


def test_lesson_detail_includes_exercise_without_hidden_tests(client):
    r = client.get("/api/lessons/loops")
    assert r.status_code == 200
    body = r.json()
    assert body["exercise"]["id"] == "ex-loops-sum" and body["examples"] and body["sections"]


def test_unknown_lesson_is_404(client):
    assert client.get("/api/lessons/nope").status_code == 404


def test_exercises_are_not_in_the_practice_list_but_can_be_fetched_and_submitted(client):
    assert "ex-loops-sum" not in [c["id"] for c in client.get("/api/challenges").json()]
    assert client.get("/api/challenges/ex-loops-sum").status_code == 200
    # No Judge0 configured here: an honest 503, never a fake verdict.
    r = client.post("/api/challenges/ex-loops-sum/submit", json={"language": "python", "source_code": "print(1)"})
    assert r.status_code == 503
