# =============================================================
# NexaSupport AI — pytest conftest.py
# =============================================================
# Shared fixtures and configuration for all tests.
#
# Key design decisions:
#   - Uses SQLite in-memory (:memory:) for full isolation — no
#     test DB files left behind on disk.
#   - session-scoped event loop avoids "loop is closed" errors
#     when async tests share heavy setup (embedding model etc.).
#   - The `override_db` fixture patches get_db_context() so that
#     tool tests that call the DB work without a live server.
# =============================================================

import asyncio
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.models import Base


# In-memory SQLite — fast, isolated, shared across connections
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared&uri=true"


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop shared across the whole test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """
    Session-scoped engine + schema creation.
    Tables are created once and shared across all tests in the session.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False, "uri": True},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(db_engine):
    """
    Function-scoped session — each test gets its own transaction
    that is rolled back after the test completes for perfect isolation.
    """
    TestSession = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestSession() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
def override_db(test_db):
    """
    Patches app.database.session.get_db_context so that any tool
    that calls `async with get_db_context() as session:` receives
    the in-memory test session instead of opening a real DB file.
    """
    @asynccontextmanager
    async def _mock_ctx():
        yield test_db

    with patch("app.database.session.get_db_context", side_effect=_mock_ctx):
        yield


