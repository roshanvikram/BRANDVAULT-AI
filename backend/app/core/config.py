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

    # Security & AI
    SECRET_KEY: str = os.getenv("SECRET_KEY", "brandvault-enterprise-secret-key-2026")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # LLM layer (optional — the deterministic heuristic engine is always the
    # default and the automatic fallback when no provider is configured or a
    # call fails. See services/llm.py.)
    LLM_ENABLED: bool = os.getenv("LLM_ENABLED", "true").lower() != "false"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")  # auto | anthropic | openai | gemini | none
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1500"))
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

