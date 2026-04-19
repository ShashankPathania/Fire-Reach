"""
config.py – Centralized configuration loaded from environment.
All services read their settings from this module.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Signal Ingestion ──────────────────────────────────────
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    SERPER_BASE_URL: str = "https://google.serper.dev/search"
    HUNTER_API_KEY: str = os.getenv("HUNTER_API_KEY", "")

    # ── LLM ──────────────────────────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Ollama fallback
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:latest")

    # ── Email ─────────────────────────────────────────────────
    EMAIL_METHOD: str = os.getenv("EMAIL_METHOD", "sendgrid")

    # SendGrid
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")

    # SMTP
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # Shared
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    FROM_NAME: str = os.getenv("FROM_NAME", "FireReach AI")

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./firereach.db"
    )

    # ── Server ────────────────────────────────────────────────
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # ── Auth ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    # ── Business Logic ────────────────────────────────────────
    SCORE_THRESHOLD: float = float(os.getenv("SCORE_THRESHOLD", "0.5"))
    DEDUP_DAYS: int = int(os.getenv("DEDUP_DAYS", "30"))

    def validate(self) -> list[str]:
        """Return list of missing critical config keys."""
        issues = []
        if not self.SERPER_API_KEY:
            issues.append("SERPER_API_KEY is not set")
        if not self.HUNTER_API_KEY:
            issues.append(
                "HUNTER_API_KEY is not set — using search fallback for contacts"
            )
        if not self.LLM_API_KEY:
            issues.append(
                "LLM_API_KEY is not set — will rely on Ollama fallback only"
            )
        if not self.SENDGRID_API_KEY and not (self.SMTP_USER and self.SMTP_PASSWORD):
            issues.append(
                "No email credentials configured (SENDGRID_API_KEY or SMTP_USER+SMTP_PASSWORD)"
            )
        return issues


settings = Settings()
