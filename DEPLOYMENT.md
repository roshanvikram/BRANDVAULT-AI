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
| `SECRET_KEY` | none | **Required when `ENVIRONMENT=production`** (startup fails without it). In development a random key is generated once into `backend/.secret_key` (git-ignored). Signs auth tokens |
| `RATE_LIMIT_ENABLED` | `true` | Per-IP request limits (in-process; use Redis for multi-instance) |
| `RATE_LIMIT_AUTH_PER_MIN` | `20` | Login / register requests per minute per IP |
| `RATE_LIMIT_AI_PER_MIN` | `30` | Analysis / Copy Studio / Assistant requests per minute per IP |
| `ENVIRONMENT` | `development` | `production` in prod |
| `SEED_DEMO_CONTENT` | `true` | Seeds 7 example NOVA TECH campaigns (real analyzer output, demo decisions labelled) only when the workspace has no campaigns, so a fresh deploy is not empty. Set `false` for real use |
| `BACKEND_CORS_ORIGINS` | localhost dev origins | Comma-separated frontend origin(s) in prod, e.g. `https://brandvault.vercel.app` |
| `ANTHROPIC_API_KEY` | empty | Optional — enables the LLM layer; unset = heuristic-only |
| `FRONTEND_URL` | `http://localhost:3000` | Public SPA origin; Google OAuth redirects back here after sign-in |
| `GOOGLE_CLIENT_ID` | empty | Optional — enables "Continue with Google" (see §3a) |
| `GOOGLE_CLIENT_SECRET` | empty | Optional — server-side only, **never** exposed to the browser |
| `GOOGLE_REDIRECT_URI` | `http://127.0.0.1:8000/api/v1/auth/google/callback` | Must exactly match an Authorized redirect URI in Google Cloud |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000/api/v1` | Frontend → backend base URL |
| `NEXT_PUBLIC_GUIDE_VIDEO_URL` | empty | Optional — a recorded walkthrough video for `/guide`. Empty = built-in animated narrated tour (see below) |

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

### 3b. Guide walkthrough video (optional)

The `/guide` page ("How to use BRANDVAULT AI") includes a **Watch the walkthrough** section. By default this is a built-in, narrated, auto-playing animated tour of the seven steps — it uses the browser's own speech synthesis and is clearly labelled as an animated walkthrough, not a recorded screen capture. To show a real recorded video instead, set `NEXT_PUBLIC_GUIDE_VIDEO_URL` to a direct video file URL (`.mp4`/`.webm`) or an embeddable player URL (e.g. a YouTube/Vimeo `/embed/` link); the section then renders that video in place of the animated tour.

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

- [ ] Strong random `SECRET_KEY` set (there is no default; production refuses to start without one).
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

## 9. Round 3: keep data across restarts (free PostgreSQL on Neon)

Render's free disk is wiped on every restart, so SQLite data (and, before Round 3, uploads) disappeared.
Uploads now live in the database, so one setting makes everything persistent:

1. Create a free project at neon.tech and copy its connection string (Dashboard → Connect).
2. In Render → your backend service → **Environment**, add `DATABASE_URL` = that string
   (e.g. `postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require`). Both the direct and the
   `-pooler` endpoints work (server-side prepared statements are disabled for poolers).
3. Save. On start the app creates all tables, enables pgvector for evidence search, and seeds the demo
   workspace once. Data now survives restarts and redeploys.

Other Round 3 settings (all optional):

| Variable | Default | Meaning |
|---|---|---|
| `DEMO_ACCOUNTS_ENABLED` | `true` | `false` blocks the published demo sign-ins |
| `EMBEDDING_PROVIDER` | `auto` | `auto`/`local` = BGE-small baked into the Docker image; `openai` + `EMBEDDING_BASE_URL`/`EMBEDDING_API_KEY`/`EMBEDDING_MODEL`; `none` |
| `RAG_MODE` | `hybrid` | `tfidf` reverts to the Round 2 retriever |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | empty | Email copies of notifications |

Memory: with OCR and the embedding model loaded the backend uses about 300 MB (Render free = 512 MB).
The Docker build downloads the embedding model once, so the first build takes a few minutes longer.

MCP: see Settings → MCP in the app, or the header of `backend/mcp_server.py`.

## 10. Keeping the free services awake

Render puts a free service to sleep after 15 minutes without visitors. The free plan has 750 hours a month, shared by both services, so they cannot both stay awake 24/7. Two things keep them awake from **9:00 AM to 8:30 PM IST** (about 730 of the 750 hours):

1. **The backend pings itself and the frontend** every 10 minutes during that window (`backend/app/services/keepawake.py`).
   - It needs no setup: on Render it uses `RENDER_EXTERNAL_URL` and the https origins in `BACKEND_CORS_ORIGINS`.
   - `KEEP_AWAKE=off` turns it off, and `KEEP_AWAKE_WINDOW=09:00-20:30` changes the hours.
   - A sleeping server can't wake itself. Once a visit wakes it, it stays awake until the window ends.
2. **GitHub Actions** (`.github/workflows/keep-awake.yml`) wakes the sites during the window. GitHub runs scheduled jobs late, about once an hour, so this alone is not enough.

`GET /api/v1/capabilities` shows `keep_awake.last_ping`.

For a site that is always on, switch both services to Render's Starter plan.

## 11. Make data permanent (required for real use)

On the free plan, `GET /api/v1/capabilities` reports `"database": "sqlite"` and `"persistent_storage": false`. The SQLite file is on a disk that resets whenever the server restarts or sleeps, so uploads, reviews and passports added on the live site are lost. The demo data is recreated on start. The app shows a "Temporary storage" notice while this is the case.

To fix it, connect a free PostgreSQL database:
1. Create a free project at neon.tech (PostgreSQL 16+; pgvector is supported).
2. Copy its connection string (`postgresql://...?sslmode=require`).
3. In Render, open **brandvault-ai → Environment**, add `DATABASE_URL` with that value, and save. Render redeploys.
4. Check `GET /api/v1/capabilities`: it should say `"database": "postgresql"` and `"persistent_storage": true`, and the notice disappears.

Uploaded files are stored in the database too, so nothing else is needed. Keep the connection string private: add it in Render yourself and never commit it.


## 12. Push notifications, email, shared rate limits and Row-Level Security

| Setting | What it does |
|---|---|
| `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | Optional. Identify this server to browser push services. Without them a key is generated once and stored in the database. `VAPID_SUBJECT` is a contact such as `mailto:brand@company.com`. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD` | Turn on email copies of notifications. |
| `RATE_LIMIT_BACKEND` | `database` (default): limits are shared by every server instance. `memory`: per process. |
| `RLS_ENABLED` | `true` (default): on PostgreSQL, Row-Level Security policies keep each organisation's rows separate. The app must connect as a normal role, not a superuser; Neon's default role is fine. |
| `REPUTATION_LLM_MAX_ROWS` | Most unrated feedback rows per upload that the AI model scores (default 300); the rest use the lexicon. |

People turn on browser notifications themselves in **Settings → Notifications → Turn on**. The server is started with `--proxy-headers` so rate limits use each visitor's real IP behind Render's proxy.


## 13. Running it for a real company

### What each company gets
- **Its own private workspace.** On the sign-up page, choose **My company** and enter the company name. That person becomes the workspace's Administrator. Data is separated from every other workspace (and, on PostgreSQL, by Row-Level Security).
- **Team invitations.** Settings → Team → Invite someone (email + role). The link is valid for `INVITE_DAYS` days. It is emailed when SMTP is set, otherwise copy it from the screen.
- **Security.** Settings → Security: two-step sign-in with any authenticator app, password change, "sign out everywhere", and (Administrators) the security log.
- **Data rights.** Settings → Data & privacy: download everything as a ZIP, close your own account, or delete the whole workspace.
- **System status** (Administrators): traffic, error rate, response times, AI fallback order, and the workspace's recent server errors with their reference IDs.

### Settings

| Setting | Default | What it does |
|---|---|---|
| `FRONTEND_URL` | `http://localhost:3000` | **Set it to the real frontend URL**: invitation links point here. |
| `ALLOW_NEW_WORKSPACES` | `true` | `false` makes the server invite-only (no new company workspaces from sign-up). |
| `SEED_DEMO_CONTENT` | `true` | Also decides the sign-up default. Set `false` for a company-only server. |
| `DEMO_ACCOUNTS_ENABLED` | `true` | Set `false` so the published demo passwords stop working. |
| `PASSWORD_MIN_LENGTH` | `10` | Passwords also need letters and numbers and must not be common. |
| `LOGIN_MAX_FAILURES`, `LOGIN_LOCK_MINUTES` | `5`, `15` | Lock an account after this many wrong passwords or codes in a row. An Administrator can unlock it in Settings → Team. |
| `SESSION_HOURS` | `12` | How long a sign-in lasts. |
| `INVITE_DAYS` | `7` | How long an invitation link works. |
| `SENTRY_DSN` | empty | Send server errors to Sentry too (errors are always stored in the database). |
| `METRICS_TOKEN` | empty | Turns on `GET /metrics` (Prometheus format) for scrapers that send `Authorization: Bearer <token>`. |
| `LOG_FORMAT` | `json` in production | One JSON line per request with its `request_id`, for log search tools. |
| `CT_MONITOR_ENABLED`, `CT_MONITOR_HOURS` | `true`, `24` | Daily look-alike domain search in certificate logs for every workspace with official domains (production only). |
| `LLM_FALLBACK` | `true` | Use every configured AI provider in turn when one fails. Set any of `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`. |
| `LLM_CACHE_SECONDS` | `3600` | Identical AI requests reuse the earlier answer within this time. |
| `OCR_DET_MAX_SIDE` | `960` | Largest side (pixels) the text-finding step of OCR works at. It sets OCR's peak memory: about 250 MB at 960, 300-400 MB at 1280, up to 1 GB uncapped. Keep 960 on a 512 MB server; use 1280 on 1 GB or more for slightly better reading of small text. |
| `OCR_MAX_SIDE`, `OCR_UPSCALE_BELOW` | `1600`, `0` | Larger images are shrunk to `OCR_MAX_SIDE` before OCR; images smaller than `OCR_UPSCALE_BELOW` are doubled first (0 = never, which saves memory). |
| `OCR_IN_SUBPROCESS` | `true` | Each OCR runs in a short-lived helper process. If an image needs more memory than the server has, only the helper stops (the user sees "needs more memory, try a smaller image") and the server keeps running; afterwards all OCR memory is returned. |
| `VISUAL_DNA_OCR` | `false` | Visual DNA checks colours and contrast; reading the text in an image is done by Creative Inspection. Set `true` (on 1 GB+ servers) to also show the text on the Visual DNA page. |

**Memory on the free plan (512 MB).** The app uses about 300 MB once started (most of it the local search model). Reading text in images (OCR) is the only heavy step (about 200-250 MB at its peak with the settings above). It runs in a separate helper process, one image at a time, so it can never take the whole server down. If the server restarts with "out of memory" in Render's Events, lower `OCR_DET_MAX_SIDE` or move to a 1 GB instance.

Health endpoints: `GET /api/v1/health` (details) and `GET /api/v1/ready` (200 only when the database answers, for load balancers). Every response has an `X-Request-ID` header; a customer quoting it lets you find the request in the logs and in Settings → System.

### Backups

`backend/scripts/backup.py` writes a portable, compressed copy of the whole database (works on SQLite and PostgreSQL):

```bash
python -m backend.scripts.backup create backups/brandvault.json.gz
python -m backend.scripts.backup verify backups/brandvault.json.gz
python -m backend.scripts.backup restore backups/brandvault.json.gz --url <EMPTY_DATABASE_URL>
```

It reads `DATABASE_URL`. Restore only writes into an empty database. Store backup files encrypted and away from the server: they contain customer data. On Neon, point-in-time restore is also available in its console.

### Legal pages

`/legal/privacy`, `/legal/terms`, `/legal/dpa` and `/legal/security` describe what the software really does, with the company-specific parts in [square brackets]. Fill those in and have a lawyer review them before customers rely on them.

