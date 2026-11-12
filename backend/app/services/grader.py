"""Grades a submission by running it against every test case of a challenge.

The program is executed by the sandboxed execution service (Judge0), never here. Results are exactly
what that service returned: if it fails mid-way an error is raised instead of guessing a verdict.
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from ..data.challenges import STARTERS, Challenge, TestCase
from ..schemas import ChallengeDetail, ExecuteResponse, SampleOut, SubmitResponse, TestResult
from .judge0 import ExecutionUnavailable

Runner = Callable[[str, str, str], Awaitable[ExecuteResponse]]  # (language, source, stdin) -> result

MAX_DETAIL_CHARS = 2_000
DEFAULT_CONCURRENCY = 3  # keeps a single submission from flooding the execution service


def outputs_match(expected: str, actual: str) -> bool:
    """Exact comparison, ignoring trailing spaces on each line and trailing blank lines."""

    def norm(text: str) -> list[str]:
        lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
        while lines and lines[-1] == "":
            lines.pop()
        return lines

    return norm(expected) == norm(actual)


def public_detail(ch: Challenge) -> ChallengeDetail:
    """The student-facing view. Built field by field so hidden tests can never leak by accident."""
    return ChallengeDetail(
        id=ch.id,
        title=ch.title,
        difficulty=ch.difficulty,  # type: ignore[arg-type]
        summary=ch.summary,
        tags=list(ch.tags),
        statement=ch.statement,
        input_format=ch.input_format,
        output_format=ch.output_format,
        constraints=list(ch.constraints),
        samples=[SampleOut(input=t.input, output=t.expected, note=t.note) for t in ch.tests if not t.hidden],
        starters={lang: code for lang, code in STARTERS[ch.kind].items()},  # type: ignore[misc]
    )


def _clip(text: str) -> str:
    return text if len(text) <= MAX_DETAIL_CHARS else text[:MAX_DETAIL_CHARS] + "\n[truncated]"


def _stdin(test: TestCase) -> str:
    return test.input if test.input.endswith("\n") else test.input + "\n"


def _to_result(index: int, test: TestCase, run: ExecuteResponse) -> TestResult:
    if run.outcome == "internal_error":
        # A problem on the execution side says nothing about the student's code, so it is not a verdict.
        raise ExecutionUnavailable("The execution service had a problem while grading. Try again.", 502, "execution_error")

    if run.outcome == "success":
        status = "passed" if outputs_match(test.expected, run.stdout) else "failed"
    else:
        status = run.outcome  # compile_error, runtime_error or time_limit

    result = TestResult(index=index, hidden=test.hidden, status=status, time_seconds=run.time_seconds, memory_kb=run.memory_kb)  # type: ignore[arg-type]
    if not test.hidden:
        result.input = test.input
        result.expected = test.expected
        result.actual = _clip(run.stdout)
        result.stderr = _clip(run.stderr) if run.stderr else None
    return result


def _skipped(index: int, test: TestCase) -> TestResult:
    return TestResult(index=index, hidden=test.hidden, status="skipped")


async def grade(ch: Challenge, language: str, source: str, run: Runner, concurrency: int = DEFAULT_CONCURRENCY) -> SubmitResponse:
    tests = ch.tests

    # Run the first test alone. A compile error will repeat on every test, so there is no point running the rest.
    first_run = await run(language, source, _stdin(tests[0]))
    first = _to_result(0, tests[0], first_run)
    if first.status == "compile_error":
        return SubmitResponse(
            verdict="compile_error",
            passed=0,
            total=len(tests),
            first_failure=0,
            compile_output=_clip(first_run.compile_output),
            results=[first] + [_skipped(i, t) for i, t in enumerate(tests) if i > 0],
        )

    sem = asyncio.Semaphore(concurrency)

    async def one(i: int, t: TestCase) -> TestResult:
        async with sem:
            return _to_result(i, t, await run(language, source, _stdin(t)))

    rest = await asyncio.gather(*(one(i, t) for i, t in enumerate(tests) if i > 0))
    results = [first, *rest]

    passed = sum(r.status == "passed" for r in results)
    failure = next((r for r in results if r.status != "passed"), None)
    if failure is None:
        verdict = "accepted"
    elif failure.status == "failed":
        verdict = "wrong_answer"
    else:
        verdict = failure.status  # compile_error, runtime_error or time_limit

    return SubmitResponse(
        verdict=verdict,  # type: ignore[arg-type]
        passed=passed,
        total=len(tests),
        first_failure=failure.index if failure else None,
        results=results,
    )
