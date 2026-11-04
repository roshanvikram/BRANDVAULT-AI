import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BRANDVAULT AI"
    PROJECT_TAGLINE: str = "Protect Every Word. Preserve Every Identity."
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./brandvault.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "*"
    ]
    
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

