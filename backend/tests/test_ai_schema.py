import pytest
from pydantic import ValidationError

from app.schemas import MAX_PROMPT_CHARS, MAX_RUN_OUTPUT_CHARS, MAX_SELECTION_CHARS, AiRequest


def req(**kw):
    base = {"mode": "explain", "language": "python", "code": "print(1)"}
    base.update(kw)
    return AiRequest(**base)


@pytest.mark.parametrize("mode", ["explain", "debug", "simplify", "complexity", "convert"])
def test_code_modes_need_code_or_selection(mode):
    extra = {"target_language": "java"} if mode == "convert" else {}
    with pytest.raises(ValidationError):
        req(mode=mode, code="", selection="  ", **extra)
    assert req(mode=mode, code="", selection="x = 1", **extra)  # a selection alone is enough
    assert req(mode=mode, code="x = 1", **extra)  # so is the file alone


@pytest.mark.parametrize("mode", ["generate", "algorithm", "learn"])
def test_prompt_modes_need_a_prompt(mode):
    with pytest.raises(ValidationError):
        req(mode=mode, code="", prompt="   ")
    assert req(mode=mode, code="", prompt="sum of two numbers")


def test_convert_needs_a_different_target_language():
    with pytest.raises(ValidationError):
        req(mode="convert", target_language=None)
    with pytest.raises(ValidationError):
        req(mode="convert", language="python", target_language="python")
    assert req(mode="convert", language="python", target_language="c")


def test_unknown_mode_and_language_rejected():
    with pytest.raises(ValidationError):
        req(mode="hack")
    with pytest.raises(ValidationError):
        req(language="ruby")


def test_length_limits_and_null_bytes():
    with pytest.raises(ValidationError):
        req(selection="x" * (MAX_SELECTION_CHARS + 1))
    with pytest.raises(ValidationError):
        req(mode="generate", prompt="x" * (MAX_PROMPT_CHARS + 1))
    with pytest.raises(ValidationError):
        req(run_output="x" * (MAX_RUN_OUTPUT_CHARS + 1))
    for field in ("code", "selection", "prompt", "run_output"):
        with pytest.raises(ValidationError):
            req(**{field: "a\x00b"})
