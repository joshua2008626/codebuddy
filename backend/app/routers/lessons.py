"""Learning hub: list lessons and read one. Exercises are submitted through /api/challenges/{id}/submit."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..data.lessons import EXERCISE_BY_ID, LESSON_BY_ID, LESSONS, Lesson
from ..schemas import ExampleOut, LessonDetail, LessonSummary, SectionOut
from ..services.grader import public_detail

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

_LANG_ORDER = ("python", "c", "java")


def _summary(lesson: Lesson) -> LessonSummary:
    used = {e.language for e in lesson.examples}
    return LessonSummary(
        id=lesson.id, title=lesson.title, group=lesson.group, summary=lesson.summary, minutes=lesson.minutes,
        languages=[lang for lang in _LANG_ORDER if lang in used],  # type: ignore[misc]
        exercise_id=lesson.exercise_id,
    )


@router.get("", response_model=list[LessonSummary])
async def list_lessons() -> list[LessonSummary]:
    return [_summary(lesson) for lesson in LESSONS]


@router.get("/{lesson_id}", response_model=LessonDetail)
async def get_lesson(lesson_id: str) -> LessonDetail:
    lesson = LESSON_BY_ID.get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "That lesson doesn't exist."})
    return LessonDetail(
        **_summary(lesson).model_dump(),
        sections=[SectionOut(heading=h, body=b) for h, b in lesson.sections],
        examples=[ExampleOut(title=e.title, language=e.language, code=e.code, output=e.output, stdin=e.stdin) for e in lesson.examples],  # type: ignore[arg-type]
        exercise=public_detail(EXERCISE_BY_ID[lesson.exercise_id]),
    )
