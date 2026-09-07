# =============================================================
# NexaSupport AI — Async Database Session Factory
# =============================================================
# PURPOSE:
#   Creates the SQLAlchemy async engine and session factory.
#   Provides get_db() dependency for FastAPI route handlers.
#
# CONCEPT — Sync vs Async database:
#   Traditional SQLAlchemy is synchronous — it blocks the server
#   while waiting for a database query to finish. FastAPI is async,
#   meaning it can handle thousands of requests concurrently if we
#   don't block. By using sqlalchemy[asyncio] + aiosqlite (for SQLite)
#   or asyncpg (for PostgreSQL), database calls are non-blocking.
#
# HOW IT FITS:
#   database/models.py → [this file] → ticket_service.py → tickets API
# =============================================================

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────────
# The "engine" is the core connection to the database.
# For SQLite in dev: sqlite+aiosqlite:///./data/nexasupport.db
# For PostgreSQL in prod: postgresql+asyncpg://user:password@host/dbname
#
# echo=False in production (echo=True prints every SQL query — useful for debugging)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,   # Log SQL queries in debug mode
    future=True,           # Use SQLAlchemy 2.0-style behavior
    # SQLite-specific: allow multiple threads to share the connection
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# ── Session Factory ────────────────────────────────────────────────────────────
# async_sessionmaker creates AsyncSession instances.
# expire_on_commit=False: keeps ORM objects accessible after commit
# (prevents "detached instance" errors in async code)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields a database session for a single request.
    
    Usage in a route:
        @router.get("/tickets")
        async def get_tickets(db: AsyncSession = Depends(get_db)):
            ...
    
    The 'async with' block ensures the session is properly closed
    even if an exception occurs during request handling.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager version of get_db().
    
    Use this in scripts and services that run outside a FastAPI request.
    
    Example:
        async with get_db_context() as db:
            result = await db.execute(select(Ticket))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
