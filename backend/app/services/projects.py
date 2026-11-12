"""Database operations for projects and files.

EVERY function takes user_id and filters by it. A project that exists but belongs to someone else is
indistinguishable from one that does not exist (both return None), so ids cannot be probed.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import projects_logic as pl
from ..models import Project, ProjectFile, utcnow


class LimitReached(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NameTaken(Exception):
    pass


class LastFile(Exception):
    pass


def list_projects(db: Session, user_id: str) -> list[tuple[Project, int]]:
    rows = db.execute(
        select(Project, func.count(ProjectFile.id))
        .outerjoin(ProjectFile, ProjectFile.project_id == Project.id)
        .where(Project.user_id == user_id)
        .group_by(Project.id)
        .order_by(Project.updated_at.desc())
    ).all()
    return [(p, int(n)) for p, n in rows]


def get_project(db: Session, user_id: str, project_id: str) -> Project | None:
    return db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user_id))


def project_files(db: Session, project_id: str) -> list[ProjectFile]:
    return list(db.scalars(select(ProjectFile).where(ProjectFile.project_id == project_id).order_by(ProjectFile.created_at, ProjectFile.name)))


def _new_file(project_id: str, name: str, content: str, now: datetime) -> ProjectFile:
    return ProjectFile(
        project_id=project_id, name=name, name_key=pl.name_key(name), language=pl.language_for_filename(name) or "python",
        content=content, created_at=now, updated_at=now,
    )


def create_project(db: Session, user_id: str, name: str, files: list[tuple[str, str]], language: str) -> Project:
    count = db.scalar(select(func.count(Project.id)).where(Project.user_id == user_id)) or 0
    if count >= pl.MAX_PROJECTS_PER_USER:
        raise LimitReached(f"You can have up to {pl.MAX_PROJECTS_PER_USER} projects. Delete one to make room.")
    if not files:
        files = [(pl.DEFAULT_FILE_NAMES[language], pl.TEMPLATES[language])]

    now = utcnow()
    project = Project(user_id=user_id, name=name, created_at=now, updated_at=now)
    db.add(project)
    db.flush()  # assigns project.id
    for fname, content in files:
        db.add(_new_file(project.id, fname, content, now))
    db.commit()
    return project


def rename_project(db: Session, project: Project, name: str) -> Project:
    project.name = name
    project.updated_at = utcnow()
    db.commit()
    return project


def delete_project(db: Session, project: Project) -> None:
    # Explicit deletes so this also works on SQLite, where foreign-key cascades are off by default.
    db.execute(delete(ProjectFile).where(ProjectFile.project_id == project.id))
    db.delete(project)
    db.commit()


def get_file(db: Session, user_id: str, project_id: str, file_id: str) -> tuple[Project, ProjectFile] | None:
    project = get_project(db, user_id, project_id)
    if project is None:
        return None
    f = db.scalar(select(ProjectFile).where(ProjectFile.id == file_id, ProjectFile.project_id == project.id))
    return (project, f) if f is not None else None


def add_file(db: Session, project: Project, name: str, content: str | None) -> ProjectFile:
    existing = db.scalar(select(func.count(ProjectFile.id)).where(ProjectFile.project_id == project.id)) or 0
    if existing >= pl.MAX_FILES_PER_PROJECT:
        raise LimitReached(f"A project can have up to {pl.MAX_FILES_PER_PROJECT} files.")
    lang = pl.language_for_filename(name) or "python"
    now = utcnow()
    f = _new_file(project.id, name, pl.TEMPLATES[lang] if content is None else content, now)
    db.add(f)
    project.updated_at = now
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise NameTaken() from None
    return f


def update_file(db: Session, project: Project, f: ProjectFile, name: str | None, content: str | None) -> ProjectFile:
    now = utcnow()
    if name is not None:
        f.name, f.name_key, f.language = name, pl.name_key(name), pl.language_for_filename(name) or f.language
    if content is not None:
        f.content = content
    f.updated_at = now
    project.updated_at = now
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise NameTaken() from None
    return f


def delete_file(db: Session, project: Project, f: ProjectFile) -> None:
    remaining = db.scalar(select(func.count(ProjectFile.id)).where(ProjectFile.project_id == project.id)) or 0
    if remaining <= 1:
        raise LastFile()
    db.delete(f)
    project.updated_at = utcnow()
    db.commit()


def delete_all_for_user(db: Session, user_id: str) -> None:
    """Used when an account is deleted, so no orphaned projects remain."""
    ids = list(db.scalars(select(Project.id).where(Project.user_id == user_id)))
    if ids:
        db.execute(delete(ProjectFile).where(ProjectFile.project_id.in_(ids)))
        db.execute(delete(Project).where(Project.id.in_(ids)))
        db.commit()
