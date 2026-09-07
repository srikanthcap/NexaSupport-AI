# =============================================================
# NexaSupport AI — pytest conftest.py
# =============================================================
# Shared fixtures and configuration for all tests.

import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database.models import Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///./data/test_nexasupport.db"


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the whole test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """
    Provide a fresh async database session for each test.
    Creates tables, runs the test, then drops all tables for isolation.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with TestSession() as session:
        yield session

    # Drop all tables after test for clean state
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
