"""Project routes end to end (FastAPI TestClient + in-memory SQLite), with the focus on privacy between users.

They need: pip install -r requirements.txt  (fastapi, sqlalchemy, httpx).

NOTE: written without being able to run them (those libraries could not be installed where this was
authored). If one fails on your machine, the failure is real information: please report it.
"""
import io
import zipfile

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Project, ProjectFile  # noqa: E402

PW = "correct horse battery staple"


@pytest.fixture()
def app():
    return create_app(Settings(database_url="sqlite://", rate_limit_auth_per_min=1000, rate_limit_projects_per_min=1000))


@pytest.fixture()
def asha(app):
    with TestClient(app) as c:
        assert c.post("/api/auth/signup", json={"email": "asha@example.com", "display_name": "Asha", "password": PW}).status_code == 201
        yield c


@pytest.fixture()
def ben(app, asha):  # a second, separate browser logged in as a different person (needs `asha` so tables exist)
    c = TestClient(app)
    assert c.post("/api/auth/signup", json={"email": "ben@example.com", "display_name": "Ben", "password": PW}).status_code == 201
    return c


def make(c, name="First", **kw):
    r = c.post("/api/projects", json={"name": name, **kw})
    assert r.status_code == 201, r.text
    return r.json()


# ----------------------------------------------------------------------- basics
def test_everything_requires_login(app):
    anon = TestClient(app)
    for method, path in [("get", "/api/projects"), ("post", "/api/projects"), ("get", "/api/projects/x"),
                         ("patch", "/api/projects/x"), ("delete", "/api/projects/x"), ("get", "/api/projects/x/download"),
                         ("post", "/api/projects/x/files"), ("patch", "/api/projects/x/files/y"), ("delete", "/api/projects/x/files/y")]:
        assert getattr(anon, method)(path, **({"json": {}} if method in ("post", "patch") else {})).status_code == 401, (method, path)


def test_create_with_default_file_in_the_chosen_language(asha):
    p = make(asha, language="java")
    assert [f["name"] for f in p["files"]] == ["Main.java"] and "public class Main" in p["files"][0]["content"]
    assert p["files"][0]["language"] == "java"


def test_create_with_given_files_and_list_shows_counts(asha):
    make(asha, "Two files", files=[{"name": "a.py", "content": "print(1)\n"}, {"name": "b.c", "content": "int x;\n"}])
    listed = asha.get("/api/projects").json()
    assert len(listed) == 1 and listed[0]["file_count"] == 2 and listed[0]["name"] == "Two files"


def test_get_rename_and_delete(asha):
    p = make(asha)
    assert asha.get(f"/api/projects/{p['id']}").json()["name"] == "First"
    assert asha.patch(f"/api/projects/{p['id']}", json={"name": "  Renamed   project "}).json()["name"] == "Renamed project"
    assert asha.delete(f"/api/projects/{p['id']}").status_code == 204
    assert asha.get(f"/api/projects/{p['id']}").status_code == 404 and asha.get("/api/projects").json() == []


def test_invalid_input_is_422(asha):
    assert asha.post("/api/projects", json={"name": "  "}).status_code == 422
    assert asha.post("/api/projects", json={"name": "x", "files": [{"name": "../evil.py"}]}).status_code == 422
    assert asha.post("/api/projects", json={"name": "x", "files": [{"name": "a.py"}, {"name": "A.py"}]}).status_code == 422
    assert asha.post("/api/projects", json={"name": "x", "language": "ruby"}).status_code == 422


# ------------------------------------------------------------------------ files
def test_file_lifecycle(asha):
    p = make(asha)
    fid = p["files"][0]["id"]
    new = asha.post(f"/api/projects/{p['id']}/files", json={"name": "util.c"})
    assert new.status_code == 201 and new.json()["language"] == "c" and "#include" in new.json()["content"]

    saved = asha.patch(f"/api/projects/{p['id']}/files/{fid}", json={"content": "print('saved')\n"})
    assert saved.status_code == 200 and saved.json()["content"] == "print('saved')\n"
    renamed = asha.patch(f"/api/projects/{p['id']}/files/{fid}", json={"name": "app.py"})
    assert renamed.json()["name"] == "app.py"
    assert renamed.json()["content"] == "print('saved')\n"  # content survives a rename

    assert asha.delete(f"/api/projects/{p['id']}/files/{new.json()['id']}").status_code == 204
    assert [f["name"] for f in asha.get(f"/api/projects/{p['id']}").json()["files"]] == ["app.py"]


def test_rename_changes_language_with_the_extension(asha):
    p = make(asha)
    r = asha.patch(f"/api/projects/{p['id']}/files/{p['files'][0]['id']}", json={"name": "main.c"})
    assert r.json()["language"] == "c"


def test_duplicate_file_names_are_refused_ignoring_case(asha):
    p = make(asha)
    assert asha.post(f"/api/projects/{p['id']}/files", json={"name": "MAIN.PY"}).status_code == 409
    other = asha.post(f"/api/projects/{p['id']}/files", json={"name": "other.py"}).json()
    clash = asha.patch(f"/api/projects/{p['id']}/files/{other['id']}", json={"name": "Main.py"})
    assert clash.status_code == 409 and clash.json()["detail"]["code"] == "name_taken"


def test_the_last_file_cannot_be_deleted(asha):
    p = make(asha)
    r = asha.delete(f"/api/projects/{p['id']}/files/{p['files'][0]['id']}")
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_file"


def test_limits(asha):
    from app import projects_logic as pl

    p = make(asha)
    for i in range(pl.MAX_FILES_PER_PROJECT - 1):
        assert asha.post(f"/api/projects/{p['id']}/files", json={"name": f"f{i}.py"}).status_code == 201
    over = asha.post(f"/api/projects/{p['id']}/files", json={"name": "one-too-many.py"})
    assert over.status_code == 409 and over.json()["detail"]["code"] == "limit_reached"
    big = asha.post(f"/api/projects/{p['id']}/files", json={"name": "big.py", "content": "x" * 70_000})
    assert big.status_code == 422


# --------------------------------------------------------------------- download
def test_download_is_a_zip_of_the_real_files(asha):
    p = make(asha, "My App!", files=[{"name": "a.py", "content": "print('é')\n"}, {"name": "Main.java", "content": "class Main {}\n"}])
    r = asha.get(f"/api/projects/{p['id']}/download")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert r.headers["content-disposition"] == 'attachment; filename="codebuddy-my-app.zip"'
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        assert sorted(zf.namelist()) == ["Main.java", "a.py"] and zf.read("a.py").decode() == "print('é')\n"


# -------------------------------------------------- privacy between two people
def test_other_people_cannot_read_change_or_delete_my_projects(asha, ben):
    mine = make(asha, "Private", files=[{"name": "secret.py", "content": "password = 'hunter2'\n"}])
    pid, fid = mine["id"], mine["files"][0]["id"]

    assert ben.get("/api/projects").json() == []  # not even listed
    for r in [ben.get(f"/api/projects/{pid}"), ben.patch(f"/api/projects/{pid}", json={"name": "mine now"}),
              ben.delete(f"/api/projects/{pid}"), ben.get(f"/api/projects/{pid}/download"),
              ben.post(f"/api/projects/{pid}/files", json={"name": "x.py"}),
              ben.patch(f"/api/projects/{pid}/files/{fid}", json={"content": "hacked"}),
              ben.delete(f"/api/projects/{pid}/files/{fid}")]:
        assert r.status_code == 404, r.request.url  # the same answer as for a project that does not exist
        assert "hunter2" not in r.text

    after = asha.get(f"/api/projects/{pid}").json()
    assert after["name"] == "Private" and after["files"][0]["content"] == "password = 'hunter2'\n"


def test_a_file_id_from_my_other_project_cannot_be_used_through_a_different_project(asha):
    a, b = make(asha, "A"), make(asha, "B")
    r = asha.patch(f"/api/projects/{b['id']}/files/{a['files'][0]['id']}", json={"content": "x"})
    assert r.status_code == 404


def test_deleting_an_account_removes_its_projects_but_not_others(app, asha, ben):
    make(asha, "Gone")
    keep = make(ben, "Stays")
    assert asha.post("/api/auth/me/delete", json={"password": PW}).status_code == 204
    with app.state.db_factory() as db:
        assert [p.name for p in db.scalars(select(Project)).all()] == ["Stays"]
        assert {f.project_id for f in db.scalars(select(ProjectFile)).all()} == {keep["id"]}
