# CodeBuddy – Progress

Protocol: say "continue" and the next unfinished item below is built.

## Status legend
- WRITTEN = source exists, not yet run/tested
- VERIFIED = built and manually tested locally

## Phases
- [x] Inspect workspace, write PLAN.md, .env.example (workspace was empty)
- [~] Phase 1: scaffold, design system, logo, landing page. WRITTEN, not yet VERIFIED.
      Done: Vite/TS/Tailwind config, tokens (dark+light), logo, navbar, hero with live-annotated editor,
      interactive features, workspace layout preview, product-scope facts, footer, theme toggle.
      Syntax-checked only (14 files, 0 errors). Not type-checked, built, or viewed in a browser.
      Routes /workspace, /practice, /learn, /login, /signup show an honest "not built yet" page.
      To verify: `cd frontend && npm install && npm run build && npm run dev`, then check 375px / 768px / 1280px widths.
- [~] Phase 2: IDE + Monaco. WRITTEN, not yet VERIFIED in a browser.
      Done: /workspace route with toolbar, file explorer (create/rename/delete, validated names), Monaco editor
      (custom dark/light themes, snippet completions, auto-indent), formatter, copy, download, reset (two-click),
      stdin tab, resizable panels (drag + arrow keys), mobile/tablet one-view-at-a-time layout, Buddy AI panel shell
      showing language + selected-code context. Files persist in localStorage only.
      VERIFIED: formatter (9 unit tests pass via `npm test`). Everything else: syntax-checked only (25 files).
      Intentionally not working yet: Run (phase 3), Buddy AI modes (phase 4), account projects (phases 6-7).
      Known risk to check first: Monaco loads from a CDN by default, so the editor needs internet access.
- [~] Phase 3: backend + Judge0 execution. WRITTEN; core logic unit-tested, end-to-end NOT verified.
      Done: FastAPI app (CORS, security headers, generic 500 handler, /api/health), POST /api/execute with
      pydantic validation (language, 64k source, 16k stdin, no NUL bytes), sliding-window rate limit,
      Judge0 client (base64 submit, polling, status mapping, generic upstream errors, output truncation,
      RapidAPI / X-Auth-Token auth), clear 503 "not configured" message, frontend api client, useRunner,
      real Output panel (status, stdout, compiler output, errors, time, memory), Run button + Ctrl+Enter.
      VERIFIED: 39 backend tests pass; 5 deliberate bugs were each caught by the tests (mutation check).
      NOT verified: the FastAPI routes (fastapi/httpx not installable here), real Judge0 calls, browser behaviour.
      Tests use a fake transport, so they do not prove a real Judge0 accepts the requests.
      To verify: `cd backend && pip install -r requirements.txt && pytest`, then
      `uvicorn app.main:app --reload --env-file ../.env` (copy .env.example to .env and set JUDGE0_*).
      First manual checks: GET /api/health; run hello-world in all 3 languages; a compile error; an infinite loop
      (expect time limit); 21 quick runs (expect HTTP 429). Confirm language ids against GET {JUDGE0_URL}/languages.
- [~] Phase 4: Buddy AI. WRITTEN; backend logic and Markdown renderer unit-tested, end-to-end NOT verified.
      Done: POST /api/ai (8 modes, own rate limit bucket), LLM client (Anthropic Messages API or any
      OpenAI-compatible chat API, key server-side only), prompt builder with per-request random delimiters and a
      system prompt that treats code/output as data, per-mode input validation, "not configured" 503 message,
      generic upstream errors (never echoes upstream bodies or the key), refactor to shared services/http.py.
      Frontend: mode picker, selection-aware context, convert target, prompt boxes, Debug includes the last run's
      errors, safe Markdown renderer (no raw HTML), Copy and "New file" on code blocks, session-only answer list.
      VERIFIED: 79 backend tests + 18 frontend tests pass; 12 deliberate bugs across phases 3-4 were each caught.
      NOT verified: FastAPI routes, real LLM calls (fake transport only), prompt quality, browser behaviour.
      Not built: streaming answers (answers arrive all at once), follow-up questions in one thread (each ask is independent).
      To verify: set LLM_API_KEY and LLM_MODEL in .env, restart; GET /api/health should show ai_configured: true.
      Try Explain with and without a selection, Debug after a failing run, Convert Python to Java, Generate, and a
      code comment like "ignore previous instructions" (it should be analysed as code, not obeyed).
- [~] Phase 5: Practice arena. WRITTEN; challenge data and grader verified with real compilers, UI and routes NOT verified.
      Done: 9 challenges (3 beginner, 3 intermediate, 3 advanced), each with 2 visible samples and 3-10 hidden tests,
      starter code in C/Python/Java; GET /api/challenges, GET /api/challenges/{id}, POST /api/challenges/{id}/submit
      (own rate limit, default 6/min); grader runs every test via Judge0, stops early on a compile error, treats
      execution-service faults as errors (never as a wrong answer), clips output, and sends details for sample tests only.
      Frontend: /practice list with solved counts, /practice/:id with statement, Monaco editor, per-language drafts,
      Run on custom/sample input, Submit, per-test results, browser-side progress (solved, attempts, best score).
      VERIFIED here with real gcc, javac and python: every expected output matches independent reference solutions
      (Python for all 9; C and Java for 3), 9 plausible-but-wrong solutions are rejected (7 pass both samples and are
      caught only by hidden tests), the classic C negative-modulo bug is caught, all starter code compiles and runs,
      hidden inputs/outputs never appear in API responses, an "echo the input" program leaks nothing.
      155 backend + 26 frontend tests pass; 9 grader bugs planted, all caught (one initially missed, test added).
      NOT verified: the FastAPI routes, real Judge0 grading (limits, speed, Java class name), browser UI.
      Limits: only the 3 beginner-level challenges have C and Java reference solutions; the rest are checked in Python
      only, so a C/Java-specific problem (overflow, input parsing) in a harder challenge could slip through.
      Progress is per browser until phase 6. Hidden tests live in app/data/challenges.py (server only).
      To verify: with Judge0 configured, open /practice, submit the starter code (expect Wrong answer, not an error),
      then a correct solution in each language (expect Accepted), then a syntax error (expect compile failure).
- [~] Phase 6: Auth + DB. WRITTEN; security logic verified, DATABASE LAYER AND ROUTES NEVER RUN.
      Design: scrypt password hashes (stdlib; replaces the bcrypt plan, no extra package), random session tokens
      stored only as SHA-256 hashes, httpOnly SameSite=Lax cookie (Secure in production), server-side revocation
      (logout and password change really end sessions, unlike JWT), Origin check on every state-changing request,
      login throttling per (client, email) and per email, identical error for unknown email vs wrong password plus a
      dummy hash so timing does not reveal accounts, old hashes upgraded on login, password rules (10-128 chars, small
      common-password list, not your email; no forced symbols).
      Routes: POST /api/auth/signup, /login, /logout, GET+PATCH /me, POST /me/password (signs out other browsers),
      POST /me/delete (needs password). SQLAlchemy models: users, auth_sessions. Tables are created at startup.
      Frontend: AuthProvider, /login, /signup, /profile (protected; name, password change, log out, delete account),
      navbar account links, redirect-back after login, "server unreachable" state kept separate from "logged out".
      VERIFIED here: 238 backend tests + 29 frontend tests pass. Mutation-checked: 14 planted security bugs, 12 caught
      at first; the 2 survivors were a throttle that never forgot old failures (a REAL gap, test added, now caught)
      and a non-constant-time compare (a timing property a unit test cannot observe).
      WRITTEN BUT NEVER EXECUTED: tests/test_accounts_db.py (12 tests) and tests/test_auth_api.py (27 tests) skip
      automatically when sqlalchemy/fastapi/httpx are missing, as they were where this was authored. They are the
      real check of the database layer, the routes, cookies and CSRF behaviour. Run them first.
      Known limits: no email verification or password reset (needs an email service); signup reveals whether an email is
      registered (unavoidable without verification); in-memory throttling (single process); tables are created with
      create_all, so add Alembic migrations before changing the schema; the common-password list is short, add a
      breached-password check before launch; fixed 14-day sessions (no sliding renewal).
      To verify: `cd backend && pip install -r requirements.txt && pytest` (expect 0 skipped), then sign up, log out,
      log in, change password in two browsers, delete the account; check the cookie is HttpOnly in browser dev tools.
- [~] Phase 7: Projects + Learning hub. WRITTEN; pure logic and lesson content VERIFIED with real compilers, routes/DB/UI NEVER RUN.
      Projects (server-side, per account): create/rename/delete projects, add/rename/edit/delete files, zip download,
      autosave (1.5 s after typing; failed saves are kept, retried and shown as "Not saved yet"; last write wins if the
      same project is open in two tabs). Every query is scoped to the logged-in user (another user's id gives 404).
      Limits: 50 projects, 20 files per project, 64k characters per file. Pages: /projects, /projects/:id (protected).
      The scratch workspace at /workspace still works without an account (browser storage); the sidebar says which.
      Learning hub (/learn, /learn/:id): 12 lessons (C, Python, Java fundamentals; variables/types, conditionals, loops,
      functions, arrays, strings, data structures, algorithms, OOP). Each has 3 explanation sections, runnable examples
      ("Open in workspace" adds them as a NEW file, never overwrites yours) and one graded exercise (same grader and
      hidden-test rules as the practice arena; not listed in the arena).
      VERIFIED here: all 33 lesson examples run through real gcc/javac/python and print EXACTLY the output shown;
      all 12 exercises have Python, C and Java reference solutions that pass every test; 6 plausible wrong solutions
      are rejected; no starter code passes already; hidden tests never appear in the public view or lesson text.
      410 backend tests pass (4 DB/route modules skip, see below) + 33 frontend tests pass; all 50 TS/TSX files parse.
      NOT verified: project routes + SQLAlchemy layer (tests/test_projects_api.py), lesson routes
      (tests/test_lessons_api.py), real Judge0 grading of exercises, every new React page and the autosave hook
      (no type-check or browser run was possible: React/Vite are not installed here).
      Known limits: progress on lesson exercises is stored in the browser, not the account; no project sharing;
      Java exercise starters assume the class is named Main.
- [~] Phase 8: Tests, responsive, deployment prep. See the Phase 8 section below.

## Known limitation
No package installs in the authoring session, so nothing has been executed yet.
First local run: `cd frontend && npm install && npm run build`, then `cd backend && pip install -r requirements.txt && pytest`.

## Phase 8: what was and was not done
DONE: README.md (setup, run, test, configure), docker-compose.yml (PostgreSQL + API + web), Dockerfiles, nginx config,
DEPLOYMENT.md (pre-launch checklist), .gitignore. Full backend + frontend unit suites run clean here.
NOT DONE / NOT POSSIBLE here: running the app, `npm run build`, the type-check, browser/responsive testing and a
real Judge0 or LLM call. The layouts are written mobile-first (stacked tabs below the lg breakpoint) but have never
been seen in a browser. Treat first run as the real test: follow README "First run checklist".
