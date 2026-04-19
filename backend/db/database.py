"""
db/database.py – Async SQLAlchemy engine and session factory.
Supports SQLite (dev) and PostgreSQL (prod) via DATABASE_URL.
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# Shared engine and session factory (initialized on startup)
_engine = None
_AsyncSessionLocal: async_sessionmaker | None = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


async def init_db(database_url: str) -> None:
    """
    Initialize the database engine, create all tables.
    Called once at FastAPI startup.
    """
    global _engine, _AsyncSessionLocal

    # SQLite needs check_same_thread=False via connect_args
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    _engine = create_async_engine(
        database_url,
        echo=False,
        connect_args=connect_args,
    )
    _AsyncSessionLocal = async_sessionmaker(
        _engine, expire_on_commit=False, class_=AsyncSession
    )

    # Auto-create tables
    from db.models import OutreachRecord, User  # noqa: F401 – ensures model is registered
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight schema migration for existing SQLite databases.
        if database_url.startswith("sqlite"):
            result = await conn.execute(text("PRAGMA table_info(outreach_history)"))
            cols = {row[1] for row in result.fetchall()}
            if "user_id" not in cols:
                await conn.execute(text("ALTER TABLE outreach_history ADD COLUMN user_id INTEGER"))
            user_result = await conn.execute(text("PRAGMA table_info(users)"))
            user_cols = {row[1] for row in user_result.fetchall()}
            if "google_email" not in user_cols:
                await conn.execute(text("ALTER TABLE users ADD COLUMN google_email VARCHAR(255)"))
            if "google_refresh_token" not in user_cols:
                await conn.execute(text("ALTER TABLE users ADD COLUMN google_refresh_token TEXT"))
            if "google_connected_at" not in user_cols:
                await conn.execute(text("ALTER TABLE users ADD COLUMN google_connected_at DATETIME"))

    logger.info(f"Database initialized: {database_url.split('///')[0]}")


async def get_session() -> AsyncSession:
    """Yield an async database session."""
    if _AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _AsyncSessionLocal() as session:
        yield session


def get_session_factory() -> async_sessionmaker:
    """Return the session factory (for use outside FastAPI dependency injection)."""
    if _AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _AsyncSessionLocal
