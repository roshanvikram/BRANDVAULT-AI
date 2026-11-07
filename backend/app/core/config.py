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
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1500"))
    
    class Config:
        case_sensitive = True
        env_file = ".env"

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

