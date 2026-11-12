import asyncio
import shutil

import pytest

from app.data.challenges import BY_ID
from app.schemas import ExecuteResponse
from app.services.grader import grade
from app.services.judge0 import ExecutionUnavailable
from tests.local_runner import local_runner
from tests.reference_solutions import PYTHON, WRONG_PYTHON

CH = BY_ID["sum-of-two"]  # 2 sample + 4 hidden tests


def resp(outcome="success", stdout="", stderr="", compile_output="", status_id=None):
    ids = {"success": 3, "compile_error": 6, "runtime_error": 11, "time_limit": 5, "internal_error": 13}
    return ExecuteResponse(outcome=outcome, status_id=status_id or ids[outcome], status_text=outcome,
                           stdout=stdout, stderr=stderr, compile_output=compile_output)


def scripted(by_stdin, default=None):
    """Runner that answers by the stdin it receives, and records every call."""
    calls = []

    async def run(language, source, stdin):
        calls.append(stdin)
        return by_stdin.get(stdin, default or resp(stdout="WRONG"))

    run.calls = calls
    return run


def answers_for(ch, overrides=None):
    """A runner script where every test gets its expected output, with optional per-index overrides."""
    out = {}
    for i, t in enumerate(ch.tests):
        stdin = t.input if t.input.endswith("\n") else t.input + "\n"
        out[stdin] = (overrides or {}).get(i, resp(stdout=t.expected + "\n"))
    return out


def run_grade(runner, ch=CH):
    return asyncio.run(grade(ch, "python", "code", runner))


def test_all_pass_is_accepted():
    r = run_grade(scripted(answers_for(CH)))
    assert (r.verdict, r.passed, r.total, r.first_failure) == ("accepted", 6, 6, None)
    assert [x.status for x in r.results] == ["passed"] * 6


def test_wrong_answer_reports_first_failure_and_counts():
    r = run_grade(scripted(answers_for(CH, {1: resp(stdout="999\n"), 4: resp(stdout="0\n")})))
    assert r.verdict == "wrong_answer" and r.passed == 4 and r.first_failure == 1
    assert [x.status for x in r.results].count("failed") == 2


def test_compile_error_stops_after_one_run():
    runner = scripted({}, default=resp("compile_error", compile_output="main.c:1: error: boom"))
    r = run_grade(runner)
    assert r.verdict == "compile_error" and r.passed == 0 and "boom" in r.compile_output
    assert len(runner.calls) == 1  # the other tests were not run
    assert [x.status for x in r.results] == ["compile_error"] + ["skipped"] * 5


def test_runtime_error_and_time_limit_verdicts():
    r = run_grade(scripted(answers_for(CH, {3: resp("runtime_error", stderr="Traceback")})))
    assert r.verdict == "runtime_error" and r.first_failure == 3 and r.passed == 5
    r = run_grade(scripted(answers_for(CH, {2: resp("time_limit")})))
    assert r.verdict == "time_limit" and r.first_failure == 2


def test_first_failure_is_the_lowest_index_even_with_mixed_failures():
    r = run_grade(scripted(answers_for(CH, {5: resp("time_limit"), 2: resp(stdout="x")})))
    assert r.first_failure == 2 and r.verdict == "wrong_answer"


def test_internal_error_is_an_error_not_a_verdict():
    # A fault in the execution service must never be reported as the student's wrong answer.
    with pytest.raises(ExecutionUnavailable):
        run_grade(scripted(answers_for(CH, {2: resp("internal_error")})))
    with pytest.raises(ExecutionUnavailable):
        run_grade(scripted({}, default=resp("internal_error")))


def test_runner_failure_propagates():
    async def boom(*_):
        raise ExecutionUnavailable("down", 502, "execution_unreachable")

    with pytest.raises(ExecutionUnavailable):
        run_grade(boom)


def test_stdin_always_ends_with_a_newline_and_every_test_runs_once():
    runner = scripted(answers_for(CH))
    run_grade(runner)
    assert len(runner.calls) == len(CH.tests) and all(c.endswith("\n") for c in runner.calls)


def test_details_are_given_for_samples_only():
    r = run_grade(scripted(answers_for(CH, {0: resp(stdout="9\n", stderr="warn"), 4: resp(stdout="SECRET-HIDDEN-OUTPUT\n")})))
    sample, hidden = r.results[0], r.results[4]
    assert (sample.input, sample.expected, sample.actual, sample.stderr) == ("3 4\n", "7", "9\n", "warn")
    assert hidden.hidden and (hidden.input, hidden.expected, hidden.actual, hidden.stderr) == (None, None, None, None)
    assert "SECRET-HIDDEN-OUTPUT" not in r.model_dump_json()


def test_long_output_detail_is_clipped():
    r = run_grade(scripted(answers_for(CH, {0: resp(stdout="x" * 50_000)})))
    assert len(r.results[0].actual) < 2_100


# ---------------- end to end through real compilers (tests only; the app never runs user code itself)
def test_real_reference_solution_is_accepted_end_to_end():
    r = asyncio.run(grade(CH, "python", PYTHON["sum-of-two"], local_runner))
    assert (r.verdict, r.passed, r.total) == ("accepted", 6, 6)
    assert all(x.time_seconds is not None for x in r.results)


def test_real_wrong_solution_passes_samples_but_fails_hidden_end_to_end():
    src = dict((c, s) for c, s, _ in WRONG_PYTHON)["sum-of-two"]
    r = asyncio.run(grade(CH, "python", src, local_runner))
    assert r.verdict == "wrong_answer" and r.first_failure is not None and r.first_failure >= 2
    assert [x.status for x in r.results[:2]] == ["passed", "passed"]  # the visible samples pass
    assert all(x.actual is None for x in r.results if x.hidden)


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc not installed")
def test_real_c_compile_error_end_to_end():
    r = asyncio.run(grade(CH, "c", "int main( { return 0; }", local_runner))
    assert r.verdict == "compile_error" and r.compile_output and r.results[1].status == "skipped"


def test_real_runtime_error_end_to_end():
    r = asyncio.run(grade(CH, "python", "raise SystemExit(3)", local_runner))
    assert r.verdict == "runtime_error" and r.passed == 0


def test_a_program_that_prints_its_input_cannot_leak_hidden_tests():
    # "echo" solutions are how hidden data would leak; the response must hold nothing from hidden cases.
    r = asyncio.run(grade(CH, "python", "print(input())", local_runner))
    blob = r.model_dump_json()
    assert "-1000000 -1000000" not in blob and "999999 1" not in blob


def test_input_without_trailing_newline_gets_one_before_running():
    from dataclasses import replace

    from app.data.challenges import TestCase

    ch = replace(CH, tests=(TestCase("1 2", "3"), TestCase("4 5", "9", hidden=True)))
    runner = scripted({"1 2\n": resp(stdout="3\n"), "4 5\n": resp(stdout="9\n")})
    r = run_grade(runner, ch)
    assert r.verdict == "accepted" and runner.calls == ["1 2\n", "4 5\n"]
