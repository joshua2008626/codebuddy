"""Runs code on THIS machine, for tests only.

The application never does this: user code goes to Judge0. This helper exists so the test suite can run
*our own* reference solutions and starter code through real compilers, to check the challenge data.
"""
from __future__ import annotations

import asyncio
import atexit
import hashlib
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from app.schemas import ExecuteResponse

TIMEOUT = 20  # seconds per step


def _resp(outcome, status_text, stdout="", stderr="", compile_output="", seconds=None) -> ExecuteResponse:
    ids = {"success": 3, "compile_error": 6, "runtime_error": 11, "time_limit": 5, "internal_error": 13}
    return ExecuteResponse(
        outcome=outcome, status_id=ids[outcome], status_text=status_text,
        stdout=stdout, stderr=stderr, compile_output=compile_output, time_seconds=seconds,
    )


# Compiling dominates the cost of these tests, so each distinct program is compiled once and reused.
_ROOT = Path(tempfile.mkdtemp(prefix="codebuddy-tests-"))
atexit.register(shutil.rmtree, _ROOT, ignore_errors=True)
_lock = threading.Lock()
_built: dict[tuple[str, str], tuple[Path, list[str]] | ExecuteResponse] = {}


def _build(language: str, source: str):
    """Returns (directory, command) ready to run, or the compile-error response."""
    key = (language, hashlib.sha256(source.encode()).hexdigest())
    with _lock:
        if key in _built:
            return _built[key]
        root = _ROOT / f"{language}-{key[1][:16]}"
        root.mkdir(parents=True, exist_ok=True)
        if language == "python":
            (root / "main.py").write_text(source)
            built = (root, ["python3", "-I", "main.py"])
        elif language == "c":
            (root / "main.c").write_text(source)
            proc = subprocess.run(["gcc", "-O2", "-o", "main", "main.c", "-lm"], cwd=root, capture_output=True, text=True, timeout=TIMEOUT)
            built = (root, ["./main"]) if proc.returncode == 0 else _resp("compile_error", "Compilation Error", compile_output=proc.stderr)
        elif language == "java":
            (root / "Main.java").write_text(source)
            proc = subprocess.run(["javac", "Main.java"], cwd=root, capture_output=True, text=True, timeout=TIMEOUT)
            built = (root, ["java", "-cp", ".", "Main"]) if proc.returncode == 0 else _resp("compile_error", "Compilation Error", compile_output=proc.stderr)
        else:
            raise ValueError(language)
        _built[key] = built
        return built


def run_local(language: str, source: str, stdin: str) -> ExecuteResponse:
    built = _build(language, source)
    if isinstance(built, ExecuteResponse):
        return built
    root, cmd = built
    start = time.monotonic()
    try:
        run = subprocess.run(cmd, cwd=root, input=stdin, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return _resp("time_limit", "Time Limit Exceeded")
    seconds = round(time.monotonic() - start, 3)
    if run.returncode != 0:
        return _resp("runtime_error", "Runtime Error", stdout=run.stdout, stderr=run.stderr, seconds=seconds)
    return _resp("success", "Accepted", stdout=run.stdout, stderr=run.stderr, seconds=seconds)


async def local_runner(language: str, source: str, stdin: str) -> ExecuteResponse:
    """Async wrapper with the same shape as Judge0Client.run, so the grader can be exercised end to end."""
    return await asyncio.to_thread(run_local, language, source, stdin)
