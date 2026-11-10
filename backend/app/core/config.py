import os
from pydantic_settings import BaseSettings

# Default development CORS origins. Production origins come from the
# BACKEND_CORS_ORIGINS env var (comma-separated). We intentionally do NOT ship
# a "*" default: the API is stateless-token based, so allow_credentials is off
# and explicit origins keep production tight.
_DEV_CORS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://localhost:5173",
]


def _parse_cors(raw: str | None) -> list[str]:
    if not raw:
        return list(_DEV_CORS)
    return [o.strip() for o in raw.split(",") if o.strip()]


class Settings(BaseSettings):
    PROJECT_NAME: str = "BRANDVAULT AI"
    PROJECT_TAGLINE: str = "Protect Every Word. Preserve Every Identity."
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development | production

    # Database — SQLite by default; set DATABASE_URL to a Postgres DSN in prod,
    # e.g. postgresql+psycopg2://user:pass@host:5432/brandvault
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./brandvault.db")

    # CORS — a computed property, NOT an env-bound list field (pydantic-settings
    # would try to JSON-decode a list field). Reads comma-separated origins.
    @property
    def BACKEND_CORS_ORIGINS(self) -> list[str]:
        return _parse_cors(os.getenv("BACKEND_CORS_ORIGINS"))

    # Public URL of the frontend (used for OAuth redirects back to the SPA).
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Google OAuth 2.0 (optional). The "Sign in with Google" button is only
    # functional when BOTH the client id and secret are supplied via env — the
    # frontend queries /auth/google/status and keeps the button disabled with a
    # clear "configure to enable" note otherwise. We never ship credentials and
    # never expose the secret to the browser; the token exchange is server-side.
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    # Must exactly match an Authorized redirect URI in the Google Cloud console.
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/auth/google/callback"
    )

    @property
    def GOOGLE_OAUTH_CONFIGURED(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    # Security & AI
    # Token-signing key. No hardcoded fallback (anyone could forge tokens with a
    # published default). See _resolve_secret_key() below.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    # Rate limits (requests per minute per client IP).
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() != "false"
    RATE_LIMIT_AUTH_PER_MIN: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "20"))
    RATE_LIMIT_AI_PER_MIN: int = int(os.getenv("RATE_LIMIT_AI_PER_MIN", "30"))
    # Brand Fraud Intelligence: fetch reported URLs from the server (off by default: SSRF risk).
    FRAUD_URL_FETCH_ENABLED: bool = os.getenv("FRAUD_URL_FETCH_ENABLED", "false").lower() == "true"
    # Demo campaigns for an empty NOVA TECH workspace (fresh deploys). Set to false for real use.
    SEED_DEMO_CONTENT: bool = os.getenv("SEED_DEMO_CONTENT", "true").lower() != "false"
    # Seeded demo sign-ins (published in DEPLOYMENT.md). Set to false to block them in real use.
    DEMO_ACCOUNTS_ENABLED: bool = os.getenv("DEMO_ACCOUNTS_ENABLED", "true").lower() != "false"
    # Optional email notifications (left empty = email shown as "not configured").
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")
    # Improvement 3 — dense embeddings for evidence retrieval (see services/embeddings.py).
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "auto")  # auto | local | openai | none
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "")
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")
    EMBEDDING_CACHE_DIR: str = os.getenv("EMBEDDING_CACHE_DIR", "")
    RAG_MODE: str = os.getenv("RAG_MODE", "hybrid")  # hybrid (BM25 + TF-IDF + dense, RRF) | tfidf
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # LLM layer (optional — the deterministic heuristic engine is always the
    # default and the automatic fallback when no provider is configured or a
    # call fails. See services/llm.py.)
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "true").lower() != "false"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")  # auto | anthropic | groq | openai | gemini | none
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
    # Groq — OpenAI-compatible API serving fast open models (Llama etc.).
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # When the first provider fails (rate limit, outage), try the next configured one.
    LLM_FALLBACK: bool = os.getenv("LLM_FALLBACK", "true").lower() != "false"
    # Identical AI requests within this many seconds reuse the earlier answer (0 = off).
    LLM_CACHE_SECONDS: int = int(os.getenv("LLM_CACHE_SECONDS", "3600"))

    # --- Company readiness: accounts, security, operations ---
    # Sign-up may create a brand-new company workspace (the person becomes its Administrator).
    ALLOW_NEW_WORKSPACES: bool = os.getenv("ALLOW_NEW_WORKSPACES", "true").lower() != "false"
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "10"))
    LOGIN_MAX_FAILURES: int = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
    LOGIN_LOCK_MINUTES: int = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))
    SESSION_HOURS: int = int(os.getenv("SESSION_HOURS", "12"))
    INVITE_DAYS: int = int(os.getenv("INVITE_DAYS", "7"))
    # Error tracking (optional): Sentry-compatible DSN. Errors are always kept in the database too.
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    # Prometheus scraping: /metrics answers only with this bearer token (unset = endpoint off).
    METRICS_TOKEN: str = os.getenv("METRICS_TOKEN", "")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "")  # json | text (default: json in production)
    # Certificate Transparency monitoring for lookalike domains (public crt.sh logs).
    CT_MONITOR_ENABLED: bool = os.getenv("CT_MONITOR_ENABLED", "true").lower() != "false"
    CT_MONITOR_HOURS: int = int(os.getenv("CT_MONITOR_HOURS", "24"))
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1500"))
    
    # Neon's direct (non-pooled) connection, written by `neon deploy`. Used for schema
    # changes at startup; requests use the pooled DATABASE_URL.
    DATABASE_URL_UNPOOLED: str = os.getenv("DATABASE_URL_UNPOOLED", "")

    class Config:
        case_sensitive = True
        # .env.local (written by tools such as the Neon CLI) overrides .env.
        env_file = (".env", ".env.local")
        # Other tools add their own variables to these files (NEON_BRANCH, NEON_REALTIME_URL, ...);
        # ignore names this app does not use instead of refusing to start.
        extra = "ignore"

_DEV_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".secret_key")


def _resolve_secret_key(s: "Settings") -> str:
    """Return the signing key.

    Production refuses to start without SECRET_KEY. Development generates a
    random key once and stores it in backend/.secret_key (git-ignored), so
    tokens survive restarts without ever using a shared default.
    """
    if s.SECRET_KEY:
        return s.SECRET_KEY
    if s.ENVIRONMENT.lower() == "production":
        raise RuntimeError("SECRET_KEY must be set when ENVIRONMENT=production.")
    try:
        with open(_DEV_SECRET_FILE, "r", encoding="utf-8") as f:
            key = f.read().strip()
        if key:
            return key
    except FileNotFoundError:
        pass
    import secrets
    key = secrets.token_hex(32)
    with open(_DEV_SECRET_FILE, "w", encoding="utf-8") as f:
        f.write(key)
    return key


settings = Settings()
settings.SECRET_KEY = _resolve_secret_key(settings)

