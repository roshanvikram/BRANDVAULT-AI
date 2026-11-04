# DEPLOYMENT.md — BRANDVAULT AI

**Date:** 2026-11-04. How to run BRANDVAULT AI locally and deploy it for public judging.

> **Honesty note.** The deployment config below (Dockerfile, `render.yaml`, `Procfile`, Alembic scaffold) is standard and correct, but was **authored, not executed** in this environment — there is no network, no hosting access, and no Postgres/alembic installed here. What **is** verified locally: the app boots, the full test suite passes, config/CORS are env-driven, and the ORM models are Postgres-portable. Treat the live-deploy steps as the runbook to execute on the target host.

---

## 1. Local development (verified)

**Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows (use source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
cd ..
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs at `http://127.0.0.1:8000/docs`. The app auto-creates tables, seeds the NOVA TECH brand + demo users, and builds RAG embeddings on startup.

**Frontend**
```bash
cd frontend
npm install
npm run dev            # http://localhost:3000
```

**Tests & evaluation**
```bash
backend/venv/Scripts/python -m unittest backend.tests.test_unit backend.tests.test_integration backend.tests.test_visual
backend/venv/Scripts/python backend/eval/run_eval.py
```

## 2. Demo accounts (NOVA TECH workspace)

Seeded automatically; for the judging demo only — **not** production credentials.

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@novatech.demo` | `Admin@2026` |
| Creator | `creator@novatech.demo` | `Creator@2026` |
| Reviewer | `reviewer@novatech.demo` | `Reviewer@2026` |

The UI signs in automatically as the demo Creator (submit for review) and Reviewer (approve). Only Reviewer/Administrator can approve — see Security below.

## 3. Environment variables

| Var | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./brandvault.db` | Set a Postgres DSN in prod: `postgresql+psycopg2://user:pass@host:5432/brandvault` |
| `SECRET_KEY` | dev placeholder | **Generate a strong random value in production.** Signs auth tokens |
| `ENVIRONMENT` | `development` | `production` in prod |
| `BACKEND_CORS_ORIGINS` | localhost dev origins | Comma-separated frontend origin(s) in prod, e.g. `https://brandvault.vercel.app` |
| `ANTHROPIC_API_KEY` | empty | Optional — enables the LLM layer; unset = heuristic-only |
| `FRONTEND_URL` | `http://localhost:3000` | Public SPA origin; Google OAuth redirects back here after sign-in |
| `GOOGLE_CLIENT_ID` | empty | Optional — enables "Continue with Google" (see §3a) |
| `GOOGLE_CLIENT_SECRET` | empty | Optional — server-side only, **never** exposed to the browser |
| `GOOGLE_REDIRECT_URI` | `http://127.0.0.1:8000/api/v1/auth/google/callback` | Must exactly match an Authorized redirect URI in Google Cloud |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000/api/v1` | Frontend → backend base URL |

Never commit real secrets. See `.env.example`.

### 3a. Google OAuth (optional)

Sign-up and email/password sign-in work out of the box. "Continue with Google" is a **real** server-side OAuth 2.0 authorization-code flow that stays **disabled** (the button is greyed with a "configure to enable" note, backed by `GET /api/v1/auth/google/status`) until both `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set — there is no fake button.

To enable it:

1. Google Cloud Console → **APIs & Services → Credentials → Create credentials → OAuth client ID → Web application**.
2. Add an **Authorized redirect URI** that exactly matches `GOOGLE_REDIRECT_URI`, e.g.
   - dev: `http://127.0.0.1:8000/api/v1/auth/google/callback`
   - prod: `https://api.yourdomain.com/api/v1/auth/google/callback`
3. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, and `FRONTEND_URL` in the backend environment. The client secret is used only in the server-side token exchange and is never sent to the browser; the minted session token is returned to the SPA in the URL **fragment** (kept out of server logs).

Google accounts are provisioned as **Creators** (like any self-service sign-up) and, if an email already exists as a local account, are linked to it on first federated sign-in.

## 4. Database

- **Default:** SQLite file (`brandvault.db`), persistent across restarts.
- **Production:** PostgreSQL. The ORM models use only portable column types (String/Text/Integer/Float/Boolean/DateTime/JSON), so a fresh Postgres database gets the correct schema from `Base.metadata.create_all` (run on startup). The additive shim in `app/db/migrations.py` is SQLite-only (it upgrades an existing dev DB); Postgres does not need it.
- **Versioned migrations (recommended for prod):** an Alembic scaffold is provided in `backend/alembic.ini` + `backend/migrations/`. After `pip install alembic`:
  ```bash
  cd backend
  alembic revision --autogenerate -m "initial schema"
  alembic upgrade head
  ```

## 5. Deploy the backend (Render example)

1. Push the repo to GitHub.
2. In Render: **New → Blueprint**, select this repo. `render.yaml` provisions a Python web service (`brandvault-api`) + a managed Postgres (`brandvault-db`).
3. Render injects `DATABASE_URL` from the database and generates `SECRET_KEY`. Set `BACKEND_CORS_ORIGINS` to your frontend URL. Optionally set `ANTHROPIC_API_KEY`.
4. Health check: `GET /api/v1/health`.

Alternatively use the root `Dockerfile` (any container host) or the `Procfile` (Heroku-style): `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

## 6. Deploy the frontend (Vercel example)

1. Import the repo in Vercel; set the project root to `frontend/`.
2. Set `NEXT_PUBLIC_API_URL` to the backend URL + `/api/v1`.
3. Deploy. Add the resulting Vercel origin to the backend's `BACKEND_CORS_ORIGINS`.

## 7. Security checklist (production)

- [ ] Strong random `SECRET_KEY` (not the dev default).
- [ ] `BACKEND_CORS_ORIGINS` restricted to your real frontend origin(s). The API is stateless bearer-token (no cookies), and CORS ships with `allow_credentials=False` and **no** `*` default.
- [ ] `DATABASE_URL` points at managed Postgres over TLS.
- [ ] Rotate/replace the demo accounts before any real use.
- [ ] Secrets live in the host's env, never in the repo.
- [ ] `/approval/decide` is auth-gated (Reviewer/Administrator only); verify a Creator token gets 403.

## 8. Post-deploy verification (incognito)

In a private/incognito window, confirm the full acceptance flow without a developer walkthrough:
1. Open the frontend URL.
2. Content Intelligence → run analysis on the sample NOVA copy → see findings + evidence citations.
3. Apply a correction → re-analysis.
4. Approval Hub → approve as Reviewer → Brand Passport generated.
5. Refresh → records persist.
6. `GET /api/v1/health` returns `healthy` and shows the LLM mode.
