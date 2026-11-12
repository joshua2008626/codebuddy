"""Pure rules for projects and their files: names, limits, starter code and zip download.

No web or database imports, so everything here is unit-tested directly.
"""
from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime

MAX_PROJECTS_PER_USER = 50
MAX_FILES_PER_PROJECT = 20
MAX_PROJECT_NAME = 60

_FILE_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$")
_EXT_LANG = {".py": "python", ".c": "c", ".java": "java"}

# Keep in sync with frontend/src/lib/languages.ts (the browser uses its own copy for scratch files).
TEMPLATES = {
    "python": '# Welcome to CodeBuddy. Press Run to execute this file.\nname = input("What\'s your name? ")\nprint(f"Hello, {name}!")\n',
    "c": '#include <stdio.h>\n\nint main(void) {\n    char name[64];\n    printf("What\'s your name? ");\n    scanf("%63s", name);\n    printf("Hello, %s!\\n", name);\n    return 0;\n}\n',
    "java": 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        System.out.print("What\'s your name? ");\n        String name = in.hasNext() ? in.next() : "friend";\n        System.out.println("Hello, " + name + "!");\n    }\n}\n',
}
DEFAULT_FILE_NAMES = {"python": "main.py", "c": "main.c", "java": "Main.java"}


def language_for_filename(name: str) -> str | None:
    lower = name.lower()
    for ext, lang in _EXT_LANG.items():
        if lower.endswith(ext) and len(lower) > len(ext):
            return lang
    return None


def file_name_problem(name: str) -> str | None:
    if not _FILE_NAME_RE.match(name):
        return "Use letters, numbers, dots, dashes or underscores (up to 64 characters)."
    if language_for_filename(name) is None:
        return "File names must end in .py, .c or .java."
    return None


def name_key(name: str) -> str:
    """Case-insensitive identity of a file name inside a project."""
    return name.lower()


def project_name_problem(name: str) -> str | None:
    cleaned = " ".join(name.split())
    if not cleaned:
        return "Enter a project name."
    if len(cleaned) > MAX_PROJECT_NAME:
        return f"Use at most {MAX_PROJECT_NAME} characters."
    if any(ord(c) < 32 or ord(c) == 127 for c in cleaned):
        return "The name can't contain control characters."
    return None


def clean_project_name(name: str) -> str:
    return " ".join(name.split())


def duplicate_names(names: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for n in names:
        k = name_key(n)
        if k in seen and n not in dupes:
            dupes.append(n)
        seen.add(k)
    return dupes


def zip_download_name(project_name: str) -> str:
    """A safe file name for the download. Only [a-z0-9-] survives, so nothing can break out of a header."""
    slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")[:40].strip("-")
    return f"codebuddy-{slug or 'project'}.zip"


def build_zip(files: list[tuple[str, str]], when: datetime) -> bytes:
    """Zips (name, content) pairs. Names are re-validated here, so a bad name can never become a path like ../x."""
    names = [n for n, _ in files]
    for n in names:
        problem = file_name_problem(n)
        if problem:
            raise ValueError(f"Invalid file name {n!r}: {problem}")
    if duplicate_names(names):
        raise ValueError("Duplicate file names")

    stamp = (max(when.year, 1980), when.month, when.day, when.hour, when.minute, when.second - when.second % 2)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files:
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.external_attr = 0o644 << 16  # regular file, rw-r--r--
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, content.encode("utf-8"))
    return buffer.getvalue()
