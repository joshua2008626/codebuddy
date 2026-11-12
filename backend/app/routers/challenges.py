"""Practice arena: list challenges, read one, submit a solution for grading."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ..data.challenges import BY_ID, CHALLENGES
from ..data.lessons import EXERCISE_BY_ID
from ..schemas import ChallengeDetail, ChallengeSummary, SubmitRequest, SubmitResponse
from ..services.grader import grade, public_detail
from ..services.judge0 import ExecutionNotConfigured, ExecutionUnavailable, Judge0Client
from .common import rate_limit
from .execute import NOT_CONFIGURED_MESSAGE, get_judge0

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.get("", response_model=list[ChallengeSummary])
async def list_challenges() -> list[ChallengeSummary]:
    return [
        ChallengeSummary(id=c.id, title=c.title, difficulty=c.difficulty, summary=c.summary, tags=list(c.tags))  # type: ignore[arg-type]
        for c in CHALLENGES
    ]


def _get(challenge_id: str):
    # Lesson exercises are graded exactly like practice challenges but are not listed in the arena.
    ch = BY_ID.get(challenge_id) or EXERCISE_BY_ID.get(challenge_id)
    if ch is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "That challenge doesn't exist."})
    return ch


@router.get("/{challenge_id}", response_model=ChallengeDetail)
async def get_challenge(challenge_id: str) -> ChallengeDetail:
    return public_detail(_get(challenge_id))


@router.post("/{challenge_id}/submit", response_model=SubmitResponse, dependencies=[Depends(rate_limit("submit", "submitting"))])
async def submit(challenge_id: str, body: SubmitRequest, request: Request, judge0: Judge0Client = Depends(get_judge0)) -> SubmitResponse:
    ch = _get(challenge_id)
    try:
        return await grade(ch, body.language, body.source_code, judge0.run)
    except ExecutionNotConfigured:
        raise HTTPException(status_code=503, detail={"code": "execution_not_configured", "message": NOT_CONFIGURED_MESSAGE})
    except ExecutionUnavailable as exc:
        raise HTTPException(status_code=exc.http_status, detail={"code": exc.code, "message": exc.message})
