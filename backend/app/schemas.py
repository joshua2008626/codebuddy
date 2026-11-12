"""Request and response models. Pydantic enforces the size and shape limits before any work happens."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_SOURCE_CHARS = 64_000
MAX_STDIN_CHARS = 16_000

LanguageId = Literal["python", "c", "java"]
Outcome = Literal["success", "compile_error", "runtime_error", "time_limit", "internal_error"]


def _reject_null_bytes(value: str) -> str:
    # NUL bytes are never valid in source or input here and can confuse downstream tooling.
    if "\x00" in value:
        raise ValueError("must not contain null bytes")
    return value


class ExecuteRequest(BaseModel):
    language: LanguageId
    source_code: str = Field(min_length=1, max_length=MAX_SOURCE_CHARS)
    stdin: str = Field(default="", max_length=MAX_STDIN_CHARS)

    _no_nul_source = field_validator("source_code")(_reject_null_bytes)
    _no_nul_stdin = field_validator("stdin")(_reject_null_bytes)

    @field_validator("source_code")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class ExecuteResponse(BaseModel):
    """Normalised result of one run. Everything here comes from the execution service, nothing is invented."""

    outcome: Outcome
    status_id: int
    status_text: str
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    message: str = ""
    time_seconds: float | None = None
    memory_kb: int | None = None


# ---------------------------------------------------------------------------
# Buddy AI
# ---------------------------------------------------------------------------
from pydantic import model_validator  # noqa: E402  (kept next to the models that use it)

AiMode = Literal["explain", "debug", "simplify", "generate", "convert", "algorithm", "complexity", "learn"]

MAX_SELECTION_CHARS = 20_000
MAX_PROMPT_CHARS = 2_000
MAX_RUN_OUTPUT_CHARS = 8_000

_NEEDS_CODE = {"explain", "debug", "simplify", "convert", "complexity"}
_NEEDS_PROMPT = {"generate", "algorithm", "learn"}


class AiRequest(BaseModel):
    mode: AiMode
    language: LanguageId
    code: str = Field(default="", max_length=MAX_SOURCE_CHARS)  # the whole current file, for context
    selection: str = Field(default="", max_length=MAX_SELECTION_CHARS)  # what the user highlighted
    prompt: str = Field(default="", max_length=MAX_PROMPT_CHARS)  # the user's own words
    target_language: LanguageId | None = None  # convert only
    run_output: str = Field(default="", max_length=MAX_RUN_OUTPUT_CHARS)  # last run's errors, for debug

    @field_validator("code", "selection", "prompt", "run_output")
    @classmethod
    def _no_nul(cls, v: str) -> str:
        return _reject_null_bytes(v)

    @model_validator(mode="after")
    def _check_mode_inputs(self) -> "AiRequest":
        if self.mode in _NEEDS_CODE and not (self.selection.strip() or self.code.strip()):
            raise ValueError("Select some code, or write some in the editor first.")
        if self.mode in _NEEDS_PROMPT and not self.prompt.strip():
            raise ValueError("Describe what you want first.")
        if self.mode == "convert" and (self.target_language is None or self.target_language == self.language):
            raise ValueError("Choose a different language to convert to.")
        return self


class AiResponse(BaseModel):
    mode: AiMode
    answer: str
    model: str


# ---------------------------------------------------------------------------
# Practice arena
# ---------------------------------------------------------------------------
Difficulty = Literal["beginner", "intermediate", "advanced"]
TestStatus = Literal["passed", "failed", "compile_error", "runtime_error", "time_limit", "skipped"]
Verdict = Literal["accepted", "wrong_answer", "compile_error", "runtime_error", "time_limit"]


class SampleOut(BaseModel):
    input: str
    output: str
    note: str = ""


class ChallengeSummary(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    summary: str
    tags: list[str]


class ChallengeDetail(ChallengeSummary):
    """Everything a student may see. Hidden test cases are never part of this model."""

    statement: str
    input_format: str
    output_format: str
    constraints: list[str]
    samples: list[SampleOut]
    starters: dict[LanguageId, str]


class SubmitRequest(BaseModel):
    language: LanguageId
    source_code: str = Field(min_length=1, max_length=MAX_SOURCE_CHARS)

    _no_nul = field_validator("source_code")(_reject_null_bytes)

    @field_validator("source_code")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class TestResult(BaseModel):
    __test__ = False  # not a pytest test class, despite the name
    index: int
    hidden: bool
    status: TestStatus
    time_seconds: float | None = None
    memory_kb: int | None = None
    # Details are filled in for sample tests only. For hidden tests they stay None, otherwise a program
    # could print what it reads and leak the hidden cases.
    input: str | None = None
    expected: str | None = None
    actual: str | None = None
    stderr: str | None = None


class SubmitResponse(BaseModel):
    verdict: Verdict
    passed: int
    total: int
    first_failure: int | None = None  # index of the first test that did not pass
    compile_output: str = ""
    results: list[TestResult]


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------
from datetime import datetime  # noqa: E402

from . import security  # noqa: E402


def _clean_email(v: str) -> str:
    email = security.normalize_email(v)
    if not security.is_valid_email(email):
        raise ValueError("Enter a valid email address")
    return email


def _clean_name(v: str) -> str:
    name = " ".join(v.split())  # trims and collapses runs of whitespace
    if not name:
        raise ValueError("Enter a name")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ValueError("The name can't contain control characters")
    return name


class SignupRequest(BaseModel):
    email: str = Field(max_length=254)
    display_name: str = Field(min_length=1, max_length=60)
    password: str = Field(max_length=security.MAX_PASSWORD + 1)  # the exact limit is reported by password_problem

    _email = field_validator("email")(_clean_email)
    _name = field_validator("display_name")(_clean_name)

    @model_validator(mode="after")
    def _check_password(self) -> "SignupRequest":
        problem = security.password_problem(self.password, self.email)
        if problem:
            raise ValueError(problem.rstrip("."))
        return self


class LoginRequest(BaseModel):
    # No password rules here: accounts made under older rules must still be able to log in.
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=security.MAX_PASSWORD + 1)

    @field_validator("email")
    @classmethod
    def _norm(cls, v: str) -> str:
        return security.normalize_email(v)


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=60)
    _name = field_validator("display_name")(_clean_name)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=security.MAX_PASSWORD + 1)
    new_password: str = Field(max_length=security.MAX_PASSWORD + 1)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=security.MAX_PASSWORD + 1)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # built straight from database rows

    id: str
    email: str
    display_name: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
from . import projects_logic as _pl  # noqa: E402


def _check_file_name(v: str) -> str:
    problem = _pl.file_name_problem(v)
    if problem:
        raise ValueError(problem.rstrip("."))
    return v


def _check_project_name(v: str) -> str:
    problem = _pl.project_name_problem(v)
    if problem:
        raise ValueError(problem.rstrip("."))
    return _pl.clean_project_name(v)


class ProjectFileIn(BaseModel):
    name: str = Field(max_length=64)
    content: str = Field(default="", max_length=MAX_SOURCE_CHARS)

    _name = field_validator("name")(_check_file_name)
    _nul = field_validator("content")(_reject_null_bytes)


class CreateProjectRequest(BaseModel):
    name: str = Field(max_length=200)
    files: list[ProjectFileIn] = Field(default_factory=list, max_length=_pl.MAX_FILES_PER_PROJECT)
    # With no files given, one starter file is created in this language.
    language: LanguageId = "python"

    _name = field_validator("name")(_check_project_name)

    @model_validator(mode="after")
    def _unique_names(self) -> "CreateProjectRequest":
        dupes = _pl.duplicate_names([f.name for f in self.files])
        if dupes:
            raise ValueError(f"Each file needs its own name. {dupes[0]} appears twice")
        return self


class RenameProjectRequest(BaseModel):
    name: str = Field(max_length=200)
    _name = field_validator("name")(_check_project_name)


class CreateFileRequest(BaseModel):
    name: str = Field(max_length=64)
    content: str | None = Field(default=None, max_length=MAX_SOURCE_CHARS)  # None means "use the starter template"

    _name = field_validator("name")(_check_file_name)

    @field_validator("content")
    @classmethod
    def _nul(cls, v: str | None) -> str | None:
        return None if v is None else _reject_null_bytes(v)


class UpdateFileRequest(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    content: str | None = Field(default=None, max_length=MAX_SOURCE_CHARS)

    @field_validator("name")
    @classmethod
    def _n(cls, v: str | None) -> str | None:
        return None if v is None else _check_file_name(v)

    @field_validator("content")
    @classmethod
    def _c(cls, v: str | None) -> str | None:
        return None if v is None else _reject_null_bytes(v)

    @model_validator(mode="after")
    def _something(self) -> "UpdateFileRequest":
        if self.name is None and self.content is None:
            raise ValueError("Send a new name, new content, or both")
        return self


class ProjectFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    language: LanguageId
    content: str
    updated_at: datetime


class ProjectSummary(BaseModel):
    id: str
    name: str
    file_count: int
    created_at: datetime
    updated_at: datetime


class ProjectDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    files: list[ProjectFileOut]


# ---------------------------------------------------------------------------
# Learning hub
# ---------------------------------------------------------------------------
class ExampleOut(BaseModel):
    title: str
    language: LanguageId
    code: str
    output: str  # what the example prints, verified against real compilers by the test suite
    stdin: str = ""


class SectionOut(BaseModel):
    heading: str
    body: str  # Markdown, rendered by the frontend's safe renderer


class LessonSummary(BaseModel):
    id: str
    title: str
    group: str
    summary: str
    minutes: int
    languages: list[LanguageId]
    exercise_id: str


class LessonDetail(LessonSummary):
    sections: list[SectionOut]
    examples: list[ExampleOut]
    exercise: ChallengeDetail
