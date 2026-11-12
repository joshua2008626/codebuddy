"""Checks the Learning Hub content with real compilers: every example prints exactly the output it
claims, every exercise's tests are right (three independent reference solutions per exercise), wrong
solutions are rejected, and the public API never exposes hidden tests."""
import json
import shutil

import pytest

from app.data.challenges import BY_ID, STARTERS
from app.data.lessons import EXERCISE_BY_ID, EXERCISES, LESSON_BY_ID, LESSONS
from app.services.grader import outputs_match, public_detail
from tests.lesson_references import C, JAVA, PYTHON, WRONG
from tests.local_runner import run_local

HAS_GCC = shutil.which("gcc") is not None
HAS_JAVA = shutil.which("javac") is not None and shutil.which("java") is not None
EXAMPLES = [(lesson.id, i, e) for lesson in LESSONS for i, e in enumerate(lesson.examples)]


def _skip_if_missing(language):
    if language == "c" and not HAS_GCC:
        pytest.skip("gcc not installed")
    if language == "java" and not HAS_JAVA:
        pytest.skip("java not installed")


def _stdin(t):
    return t.input if t.input.endswith("\n") else t.input + "\n"


def _results(ch, language, source):
    out = []
    for t in ch.tests:
        r = run_local(language, source, _stdin(t))
        out.append((t, r.outcome == "success" and outputs_match(t.expected, r.stdout)))
    return out


# --------------------------------------------------------------------------- shape
def test_twelve_lessons_with_unique_ids_covering_the_required_topics():
    assert len(LESSONS) == 12
    assert len({lesson.id for lesson in LESSONS}) == 12
    assert {lesson.id for lesson in LESSONS} == {
        "c-fundamentals", "python-fundamentals", "java-fundamentals", "variables-types", "conditionals", "loops",
        "functions", "arrays", "strings", "data-structures", "algorithms", "oop",
    }


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda x: x.id)
def test_each_lesson_has_explanations_examples_and_an_exercise(lesson):
    assert len(lesson.sections) >= 3
    assert all(h.strip() and b.strip() for h, b in lesson.sections)
    assert lesson.examples
    assert lesson.exercise_id in EXERCISE_BY_ID
    assert lesson.minutes > 0


def test_each_exercise_belongs_to_exactly_one_lesson_and_ids_do_not_clash_with_practice():
    used = [lesson.exercise_id for lesson in LESSONS]
    assert sorted(used) == sorted(e.id for e in EXERCISES)
    assert not set(EXERCISE_BY_ID) & set(BY_ID)


@pytest.mark.parametrize("ch", EXERCISES, ids=lambda c: c.id)
def test_each_exercise_has_samples_hidden_tests_and_starters(ch):
    assert sum(not t.hidden for t in ch.tests) >= 2
    assert sum(t.hidden for t in ch.tests) >= 3
    assert set(STARTERS[ch.kind]) == {"python", "c", "java"}
    assert ch.id in PYTHON and ch.id in C and ch.id in JAVA


def test_language_lessons_use_their_own_language_and_concept_lessons_show_all_three():
    only = {"c-fundamentals": {"c"}, "python-fundamentals": {"python"}, "java-fundamentals": {"java"}}
    for lesson in LESSONS:
        langs = {e.language for e in lesson.examples}
        assert langs == only.get(lesson.id, {"python", "c", "java"}), lesson.id


# ------------------------------------------------------- examples print what they claim
@pytest.mark.parametrize("lid,i,example", EXAMPLES, ids=lambda v: v if isinstance(v, str) else (str(v) if isinstance(v, int) else v.language))
def test_example_prints_exactly_the_claimed_output(lid, i, example):
    _skip_if_missing(example.language)
    r = run_local(example.language, example.code, example.stdin)
    assert r.outcome == "success", r.compile_output or r.stderr
    assert r.stdout.replace("\r\n", "\n").rstrip("\n") == example.output  # exact, not whitespace-insensitive


def test_concept_lesson_examples_agree_across_languages():
    for lesson in LESSONS:
        if len({e.language for e in lesson.examples}) == 3:
            assert len({e.output for e in lesson.examples}) == 1, lesson.id


# ---------------------------------------------------------- exercise tests are correct
@pytest.mark.parametrize("ch", EXERCISES, ids=lambda c: c.id)
def test_python_reference_passes_every_test(ch):
    failed = [i for i, (_, ok) in enumerate(_results(ch, "python", PYTHON[ch.id])) if not ok]
    assert failed == [], f"tests {failed} disagree with the reference solution"


@pytest.mark.parametrize("cid", sorted(C))
def test_c_reference_passes_every_test(cid):
    _skip_if_missing("c")
    assert all(ok for _, ok in _results(EXERCISE_BY_ID[cid], "c", C[cid]))


@pytest.mark.parametrize("cid", sorted(JAVA))
def test_java_reference_passes_every_test(cid):
    _skip_if_missing("java")
    assert all(ok for _, ok in _results(EXERCISE_BY_ID[cid], "java", JAVA[cid]))


@pytest.mark.parametrize("cid,source,passes_samples", WRONG, ids=[w[0] for w in WRONG])
def test_wrong_solutions_are_rejected(cid, source, passes_samples):
    results = _results(EXERCISE_BY_ID[cid], "python", source)
    assert not all(ok for _, ok in results), "a wrong solution was accepted"
    if passes_samples:
        assert all(ok for t, ok in results if not t.hidden), "meant to pass the samples"
        assert any(not ok for t, ok in results if t.hidden), "meant to be caught by a hidden test"


@pytest.mark.parametrize("ch", EXERCISES, ids=lambda c: c.id)
def test_starter_code_does_not_already_pass(ch):
    """A starter that is already correct would make the exercise meaningless."""
    results = _results(ch, "python", STARTERS[ch.kind]["python"])
    assert not all(ok for _, ok in results)


@pytest.mark.parametrize("ch", EXERCISES, ids=lambda c: c.id)
def test_public_view_contains_only_sample_tests(ch):
    detail = public_detail(ch)
    samples = [t for t in ch.tests if not t.hidden]
    assert [(s.input, s.output) for s in detail.samples] == [(t.input, t.expected) for t in samples]
    blob = detail.model_dump_json()
    sample_inputs = {t.input for t in samples}
    for t in ch.tests:
        if t.hidden and len(t.input) > 12 and t.input not in sample_inputs:
            assert json.dumps(t.input)[1:-1] not in blob


def test_lesson_text_never_contains_a_hidden_test_input():
    hidden = [t.input for ch in EXERCISES for t in ch.tests if t.hidden and len(t.input) > 12]
    text = json.dumps([(l.sections, [e.code for e in l.examples]) for l in LESSONS])
    assert not [h for h in hidden if json.dumps(h)[1:-1] in text]
