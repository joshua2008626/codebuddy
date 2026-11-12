# Deployment checklist

Do these before real users sign up. Items marked (gap) are known missing features, not just configuration.

**Secrets and transport**
- [ ] HTTPS in front of everything; `APP_ENV=production` (secure cookie, API docs off).
- [ ] `CORS_ORIGINS` = your exact site origin (it also powers the CSRF Origin check).
- [ ] `TRUST_PROXY=true` only behind a proxy that sets `X-Forwarded-For`.
- [ ] Keep `.env` out of git; use your host's secret store for `LLM_API_KEY`, `JUDGE0_API_KEY`, DB password.

**Data**
- [ ] Managed PostgreSQL with backups. (gap) Tables are created with `create_all`; add Alembic migrations before any schema change.
- [ ] Decide a retention policy for deleted accounts (deleting an account removes its projects).

**Abuse and cost**
- [ ] (gap) Rate limits are per process, in memory. With more than one API instance, move them to Redis or the proxy.
- [ ] Set a spending limit at your LLM provider and review `RATE_LIMIT_*` values.
- [ ] Run Judge0 with its own resource limits; never expose it publicly.

**Accounts**
- [ ] (gap) No email verification or password reset yet (needs an email service).
- [ ] (gap) The common-password list is short; add a breached-password check (for example Have I Been Pwned range API).

**Verification before launch**
- [ ] `pytest` with 0 skipped, `npm run build`, and the First run checklist in `README.md`.
- [ ] Test with a real Judge0: starter code gives Wrong answer, a correct solution gives Accepted, a syntax error gives a compile error; check Java class naming.
