"""Projects and their files. Every route requires login and only ever sees the caller's own projects."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .. import projects_logic as pl
from ..models import Project, User
from ..schemas import (
    CreateFileRequest,
    CreateProjectRequest,
    ProjectDetail,
    ProjectFileOut,
    ProjectSummary,
    RenameProjectRequest,
    UpdateFileRequest,
)
from ..services import projects as svc
from .common import current_user, get_db, rate_limit

router = APIRouter(prefix="/api/projects", tags=["projects"])

NOT_FOUND = {"code": "not_found", "message": "That project doesn't exist."}
FILE_NOT_FOUND = {"code": "not_found", "message": "That file doesn't exist."}
NAME_TAKEN = {"code": "name_taken", "message": "A file with that name already exists in this project."}

write_limit = Depends(rate_limit("projects", "saving"))


def _owned(db: Session, user: User, project_id: str) -> Project:
    project = svc.get_project(db, user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=NOT_FOUND)  # also the answer for other people's projects
    return project


def _detail(db: Session, project: Project) -> ProjectDetail:
    return ProjectDetail(
        id=project.id, name=project.name, created_at=project.created_at, updated_at=project.updated_at,
        files=[ProjectFileOut.model_validate(f) for f in svc.project_files(db, project.id)],
    )


@router.get("", response_model=list[ProjectSummary])
def list_projects(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[ProjectSummary]:
    return [
        ProjectSummary(id=p.id, name=p.name, file_count=n, created_at=p.created_at, updated_at=p.updated_at)
        for p, n in svc.list_projects(db, user.id)
    ]


@router.post("", response_model=ProjectDetail, status_code=201, dependencies=[write_limit])
def create_project(body: CreateProjectRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ProjectDetail:
    try:
        project = svc.create_project(db, user.id, body.name, [(f.name, f.content) for f in body.files], body.language)
    except svc.LimitReached as exc:
        raise HTTPException(status_code=409, detail={"code": "limit_reached", "message": exc.message})
    return _detail(db, project)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ProjectDetail:
    return _detail(db, _owned(db, user, project_id))


@router.patch("/{project_id}", response_model=ProjectDetail, dependencies=[write_limit])
def rename_project(project_id: str, body: RenameProjectRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> ProjectDetail:
    return _detail(db, svc.rename_project(db, _owned(db, user, project_id), body.name))


@router.delete("/{project_id}", status_code=204, dependencies=[write_limit])
def delete_project(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    svc.delete_project(db, _owned(db, user, project_id))
    return Response(status_code=204)


@router.get("/{project_id}/download")
def download_project(project_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    project = _owned(db, user, project_id)
    files = [(f.name, f.content) for f in svc.project_files(db, project.id)]
    data = pl.build_zip(files, datetime.now(timezone.utc))
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{pl.zip_download_name(project.name)}"'},
    )


@router.post("/{project_id}/files", response_model=ProjectFileOut, status_code=201, dependencies=[write_limit])
def add_file(project_id: str, body: CreateFileRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    project = _owned(db, user, project_id)
    try:
        return svc.add_file(db, project, body.name, body.content)
    except svc.LimitReached as exc:
        raise HTTPException(status_code=409, detail={"code": "limit_reached", "message": exc.message})
    except svc.NameTaken:
        raise HTTPException(status_code=409, detail=NAME_TAKEN)


@router.patch("/{project_id}/files/{file_id}", response_model=ProjectFileOut, dependencies=[write_limit])
def update_file(project_id: str, file_id: str, body: UpdateFileRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    found = svc.get_file(db, user.id, project_id, file_id)
    if found is None:
        raise HTTPException(status_code=404, detail=FILE_NOT_FOUND)
    project, f = found
    try:
        return svc.update_file(db, project, f, body.name, body.content)
    except svc.NameTaken:
        raise HTTPException(status_code=409, detail=NAME_TAKEN)


@router.delete("/{project_id}/files/{file_id}", status_code=204, dependencies=[write_limit])
def delete_file(project_id: str, file_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    found = svc.get_file(db, user.id, project_id, file_id)
    if found is None:
        raise HTTPException(status_code=404, detail=FILE_NOT_FOUND)
    project, f = found
    try:
        svc.delete_file(db, project, f)
    except svc.LastFile:
        raise HTTPException(status_code=409, detail={"code": "last_file", "message": "A project needs at least one file."})
    return Response(status_code=204)
