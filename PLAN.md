# CodeBuddy – Implementation Plan

## Environment constraints (found while inspecting)
- Workspace was empty: greenfield build, nothing to preserve.
- Node 22 / npm 10 and Python 3.13 are present.
- Package installs are blocked in this session. FastAPI, SQLAlchemy, bcrypt, React, Vite,
  Tailwind, Monaco etc. are NOT installed, so the app cannot be built, run or tested here.
- Consequence: every phase is written as source, then marked **Written, not yet verified**
  until you run the verify steps locally (`npm run build`, `pytest`, manual checks).
  Nothing is marked "complete" without that.

## Architecture
```
codebuddy/
  frontend/   React + TS + Vite + Tailwind + Monaco + Framer Motion + Lucide
  backend/    FastAPI (REST), SQLAlchemy, Pydantic validation
    app/
      main.py, config.py, db.py, security.py, deps.py, ratelimit.py
      models.py, schemas.py
      routers/  auth.py, projects.py, execute.py, ai.py, challenges.py
      services/ judge0.py, llm.py
      data/     challenges.json
    tests/
  docker-compose.yml   (PostgreSQL)
  .env.example
```

## Key decisions
- **Execution**: backend proxies to Judge0 (CE self-hosted or RapidAPI). User code never runs
  on our backend. Without `JUDGE0_URL`, `/api/execute` returns 503 with a configuration message.
- **AI**: backend proxies to a configurable LLM API (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`).
  Keys stay server-side. Without a key, Buddy AI shows a configuration message.
- **Auth**: email + password hashed with scrypt (standard library), random session tokens stored as SHA-256
  hashes server-side and sent in an httpOnly SameSite=Lax cookie (so logout really revokes access), plus an Origin
  check on every state-changing request. No JWT.
- **DB**: PostgreSQL in production (`DATABASE_URL`), SQLite fallback for local dev.
- **Rate limiting**: in-process sliding window per IP/user (swap for Redis in production).
- **Challenges**: stored server-side with hidden tests; submissions run through Judge0 per test case.

## Environment variables
DATABASE_URL, SESSION_TTL_DAYS, COOKIE_SECURE, CORS_ORIGINS,
JUDGE0_URL, JUDGE0_API_KEY, JUDGE0_API_HOST,
LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL,
RATE_LIMIT_EXECUTE_PER_MIN, RATE_LIMIT_AI_PER_MIN

## Phases (status)
1. Branding, design system, landing page – in progress
2. IDE + Monaco – todo
3. Real execution (Judge0) – todo
4. Buddy AI – todo
5. Practice arena – todo
6. Auth + database – todo
7. Learning hub + projects – todo
8. Tests, responsive pass, deployment prep – todo
