"""POST /api/execute: validates the request, applies rate limiting, delegates to Judge0."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from .common import rate_limit
from ..schemas import ExecuteRequest, ExecuteResponse
from ..services.judge0 import ExecutionNotConfigured, ExecutionUnavailable, Judge0Client

router = APIRouter(prefix="/api", tags=["execute"])

NOT_CONFIGURED_MESSAGE = (
    "Code execution isn't set up on this server. Set JUDGE0_URL (and JUDGE0_API_KEY / JUDGE0_API_HOST "
    "for RapidAPI) in the backend .env file, then restart. See .env.example."
)


def get_judge0(request: Request) -> Judge0Client:
    return request.app.state.judge0


@router.post("/execute", response_model=ExecuteResponse, dependencies=[Depends(rate_limit("execute", "running code"))])
async def execute(body: ExecuteRequest, judge0: Judge0Client = Depends(get_judge0)) -> ExecuteResponse:
    try:
        return await judge0.run(body.language, body.source_code, body.stdin)
    except ExecutionNotConfigured:
        raise HTTPException(status_code=503, detail={"code": "execution_not_configured", "message": NOT_CONFIGURED_MESSAGE})
    except ExecutionUnavailable as exc:
        raise HTTPException(status_code=exc.http_status, detail={"code": exc.code, "message": exc.message})
