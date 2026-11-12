"""Application settings, read from environment variables (see ../.env.example).

Plain dataclass instead of a settings library: no extra dependency, and easy to construct in tests.
Run the server with `uvicorn app.main:app --env-file ../.env` to load the .env file.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .security import normalize_database_url

# Default Judge0 CE language ids. Instances differ, so verify with GET {JUDGE0_URL}/languages
# and override with JUDGE0_LANG_PYTHON / JUDGE0_LANG_C / JUDGE0_LANG_JAVA if needed.
DEFAULT_LANG_IDS = {"python": 71, "c": 50, "java": 62}


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None or raw.strip() == "" else raw.strip().lower() in {"1", "true", "yes"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    # Only enable behind a reverse proxy that sets X-Forwarded-For; otherwise clients could spoof their IP.
    trust_proxy: bool = False

    database_url: str = "sqlite:///./codebuddy.db"  # PostgreSQL in production, see .env.example
    session_ttl_days: int = 14
    cookie_secure: bool = False  # HTTPS-only cookie; on by default in production
    rate_limit_auth_per_min: int = 10  # signup/login attempts per client per minute
    rate_limit_projects_per_min: int = 120  # project and file writes, which include autosaves
    login_max_failures: int = 5  # failed logins allowed per (client, email) per window
    login_window_seconds: int = 900

    judge0_url: str = ""
    judge0_api_key: str = ""
    judge0_api_host: str = ""
    judge0_cpu_time_limit: int = 5  # seconds; 0 means "use the Judge0 instance default"
    judge0_poll_timeout: float = 25.0  # seconds to wait for a result before giving up
    judge0_poll_interval: float = 0.6
    lang_ids: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_LANG_IDS))

    llm_provider: str = "anthropic"  # "anthropic" or "openai_compatible"
    llm_api_key: str = ""
    llm_model: str = ""  # no default on purpose: model names change, so set one from your provider's docs
    llm_base_url: str = ""  # required for openai_compatible; optional override for anthropic
    llm_max_tokens: int = 1500
    llm_timeout: float = 60.0

    rate_limit_execute_per_min: int = 20
    rate_limit_ai_per_min: int = 15
    rate_limit_submit_per_min: int = 6  # each submission runs every test case, so it is limited more tightly

    @property
    def ai_configured(self) -> bool:
        if not (self.llm_api_key.strip() and self.llm_model.strip()):
            return False
        if self.llm_provider == "anthropic":
            return True
        return self.llm_provider == "openai_compatible" and bool(self.llm_base_url.strip())

    @property
    def execution_configured(self) -> bool:
        return bool(self.judge0_url.strip())

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


def load_settings() -> Settings:
    origins = tuple(o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip())
    lang_ids = {
        "python": _int("JUDGE0_LANG_PYTHON", DEFAULT_LANG_IDS["python"]),
        "c": _int("JUDGE0_LANG_C", DEFAULT_LANG_IDS["c"]),
        "java": _int("JUDGE0_LANG_JAVA", DEFAULT_LANG_IDS["java"]),
    }
    return Settings(
        app_env=os.environ.get("APP_ENV", "development"),
        cors_origins=origins,
        trust_proxy=os.environ.get("TRUST_PROXY", "").lower() in {"1", "true", "yes"},
        database_url=normalize_database_url(os.environ.get("DATABASE_URL", "") or "sqlite:///./codebuddy.db"),
        session_ttl_days=max(1, _int("SESSION_TTL_DAYS", 14)),
        cookie_secure=_bool("COOKIE_SECURE", os.environ.get("APP_ENV", "development").lower() == "production"),
        rate_limit_auth_per_min=_int("RATE_LIMIT_AUTH_PER_MIN", 10),
        rate_limit_projects_per_min=_int("RATE_LIMIT_PROJECTS_PER_MIN", 120),
        login_max_failures=max(1, _int("LOGIN_MAX_FAILURES", 5)),
        login_window_seconds=max(60, _int("LOGIN_WINDOW_SECONDS", 900)),
        judge0_url=os.environ.get("JUDGE0_URL", "").strip().rstrip("/"),
        judge0_api_key=os.environ.get("JUDGE0_API_KEY", "").strip(),
        judge0_api_host=os.environ.get("JUDGE0_API_HOST", "").strip(),
        judge0_cpu_time_limit=_int("JUDGE0_CPU_TIME_LIMIT", 5),
        judge0_poll_timeout=_float("JUDGE0_POLL_TIMEOUT", 25.0),
        judge0_poll_interval=_float("JUDGE0_POLL_INTERVAL", 0.6),
        lang_ids=lang_ids,
        llm_provider=os.environ.get("LLM_PROVIDER", "anthropic").strip().lower(),
        llm_api_key=os.environ.get("LLM_API_KEY", "").strip(),
        llm_model=os.environ.get("LLM_MODEL", "").strip(),
        llm_base_url=os.environ.get("LLM_BASE_URL", "").strip().rstrip("/"),
        llm_max_tokens=_int("LLM_MAX_TOKENS", 1500),
        llm_timeout=_float("LLM_TIMEOUT", 60.0),
        rate_limit_execute_per_min=_int("RATE_LIMIT_EXECUTE_PER_MIN", 20),
        rate_limit_ai_per_min=_int("RATE_LIMIT_AI_PER_MIN", 15),
        rate_limit_submit_per_min=_int("RATE_LIMIT_SUBMIT_PER_MIN", 6),
    )
