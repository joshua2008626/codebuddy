# CodeBuddy

Write, run and understand code in C, Python and Java: Monaco editor, sandboxed execution (Judge0), an AI assistant
(Buddy AI), a practice arena with hidden tests, saved projects, and a learning hub.

> **Status:** written in an environment where packages could not be installed, so only the pure logic was executed
> (see `PROJECT_PROGRESS.md` for exactly what was and was not verified). Follow the first-run checklist below.

## Quick start (development)
```bash
cp .env.example .env            # then edit: see the comments in that file
cd backend && pip install -r requirements.txt && pytest          # expect 0 skipped
uvicorn app.main:app --reload --env-file ../.env                 # http://localhost:8000
cd ../frontend && npm install && npm run build && npm test       # then: npm run dev (http://localhost:5173)
```
SQLite is used by default, so no database setup is needed locally.

## What needs credentials
| Feature | Variables | Without them |
|---|---|---|
| Run code, practice grading | `JUDGE0_URL` (+ `JUDGE0_API_KEY`/`JUDGE0_API_HOST` for hosted) | Clear "not configured" message; nothing is faked |
| Buddy AI | `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` (+ `LLM_BASE_URL`) | Clear "not configured" message |
| Accounts and projects | `DATABASE_URL` | SQLite file |
API keys stay on the server and are never sent to the browser. User code is never run by this backend; it is sent to Judge0.

## Docker (PostgreSQL + API + web)
```bash
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)" >> .env
docker compose up --build        # http://localhost:8080
```
Set `APP_ENV=production` and `CORS_ORIGINS=https://your-site` in `.env` for a real deployment.

## First run checklist
1. `pytest` in `backend/`: all tests run, **0 skipped** (the 4 skipped modules are the DB/route tests: accounts_db, auth_api, projects_api, lessons_api).
2. `npm run build` in `frontend/`: fix any type errors it reports (the UI was never type-checked before).
3. Open `/workspace`, press Run: expect a "not configured" message until Judge0 is set, then real output.
4. Sign up, create a project, edit a file, reload: the text should still be there.
5. `/learn`: open a lesson, "Open in workspace", Run; then submit the exercise.
6. Resize the browser below 1024px wide and check the Files/Editor/Buddy tabs.

See `DEPLOYMENT.md` before going public.
