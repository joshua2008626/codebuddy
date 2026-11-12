"""Validates the challenge data itself: every expected output is checked by independent reference solutions
run through real compilers, wrong-but-plausible solutions must be rejected, and starter code must run."""
import json
import shutil
from collections import Counter

import pytest

from app.data.challenges import BY_ID, CHALLENGES, STARTERS
from app.services.grader import outputs_match, public_detail
from tests.local_runner import run_local
from tests.reference_solutions import C, JAVA, PYTHON, WRONG_C_EVEN_ODD, WRONG_PYTHON

HAS_GCC = shutil.which("gcc") is not None
HAS_JAVA = shutil.which("javac") is not None and shutil.which("java") is not None


def stdin_of(t):
    return t.input if t.input.endswith("\n") else t.input + "\n"


def passes(ch, language, source):
    """Returns the list of (test, passed) for a solution run on every test case."""
    out = []
    for t in ch.tests:
        r = run_local(language, source, stdin_of(t))
        out.append((t, r.outcome == "success" and outputs_match(t.expected, r.stdout)))
    return out


# ---------------------------------------------------------------- data shape
def test_ids_unique_and_difficulty_spread():
    assert len({c.id for c in CHALLENGES}) == len(CHALLENGES)
    assert Counter(c.difficulty for c in CHALLENGES) == {"beginner": 3, "intermediate": 3, "advanced": 3}


@pytest.mark.parametrize("ch", CHALLENGES, ids=lambda c: c.id)
def test_each_challenge_has_samples_hidden_tests_and_starters(ch):
    assert sum(not t.hidden for t in ch.tests) >= 2
    assert sum(t.hidden for t in ch.tests) >= 3
    assert all(t.expected.strip() for t in ch.tests)
    assert set(STARTERS[ch.kind]) == {"python", "c", "java"}
    assert ch.id in PYTHON  # every challenge has a reference solution


# ------------------------------------------------- expected outputs are right
@pytest.mark.parametrize("ch", CHALLENGES, ids=lambda c: c.id)
def test_python_reference_passes_every_test(ch):
    failed = [i for i, (t, ok) in enumerate(passes(ch, "python", PYTHON[ch.id])) if not ok]
    assert failed == [], f"reference solution failed tests {failed}: the expected output may be wrong"


@pytest.mark.skipif(not HAS_GCC, reason="gcc not installed")
@pytest.mark.parametrize("cid", sorted(C))
def test_c_reference_passes_every_test(cid):
    assert all(ok for _, ok in passes(BY_ID[cid], "c", C[cid]))


@pytest.mark.skipif(not HAS_JAVA, reason="javac/java not installed")
@pytest.mark.parametrize("cid", sorted(JAVA))
def test_java_reference_passes_every_test(cid):
    assert all(ok for _, ok in passes(BY_ID[cid], "java", JAVA[cid]))


# ------------------------------------------------------ tests catch mistakes
@pytest.mark.parametrize("cid,source,passes_samples", WRONG_PYTHON, ids=[w[0] for w in WRONG_PYTHON])
def test_wrong_solutions_are_rejected(cid, source, passes_samples):
    results = passes(BY_ID[cid], "python", source)
    assert not all(ok for _, ok in results), "a wrong solution was accepted"
    if passes_samples:
        assert all(ok for t, ok in results if not t.hidden), "meant to pass the samples"
        assert any(not ok for t, ok in results if t.hidden), "meant to be caught by a hidden test"


@pytest.mark.skipif(not HAS_GCC, reason="gcc not installed")
def test_classic_c_negative_modulo_bug_is_caught_by_a_hidden_test():
    results = passes(BY_ID["even-or-odd"], "c", WRONG_C_EVEN_ODD)
    assert all(ok for t, ok in results if not t.hidden)
    assert any(not ok for t, ok in results if t.hidden)


# ------------------------------------------------------------- starter code
@pytest.mark.parametrize("kind", sorted(STARTERS))
@pytest.mark.parametrize("language", ["python", "c", "java"])
def test_starter_code_compiles_and_runs(kind, language):
    if language == "c" and not HAS_GCC:
        pytest.skip("gcc not installed")
    if language == "java" and not HAS_JAVA:
        pytest.skip("java not installed")
    ch = next(c for c in CHALLENGES if c.kind == kind)
    r = run_local(language, STARTERS[kind][language], stdin_of(ch.tests[0]))
    assert r.outcome == "success", r.compile_output or r.stderr


# --------------------------------------------------- hidden tests stay hidden
@pytest.mark.parametrize("ch", CHALLENGES, ids=lambda c: c.id)
def test_public_view_contains_only_sample_tests(ch):
    detail = public_detail(ch)
    samples = [t for t in ch.tests if not t.hidden]
    assert [(s.input, s.output) for s in detail.samples] == [(t.input, t.expected) for t in samples]
    blob = detail.model_dump_json()
    sample_inputs = {t.input for t in samples}
    for t in ch.tests:
        if t.hidden and len(t.input) > 12 and t.input not in sample_inputs:
            assert json.dumps(t.input)[1:-1] not in blob, "hidden test input leaked into the public view"


# ------------------------------------------------------------- comparison
def test_outputs_match_ignores_only_trailing_whitespace():
    assert outputs_match("7", "7\n")
    assert outputs_match("a\nb", "a  \nb\n\n")
    assert outputs_match("a\nb", "a\r\nb\r\n")
    assert not outputs_match("Yes", "yes")  # case matters
    assert not outputs_match("1 2", "1  2")  # interior spacing matters
    assert not outputs_match("a\nb", "a b")  # line structure matters
    assert not outputs_match("7", "")
