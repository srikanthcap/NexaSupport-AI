# =============================================================
# NexaSupport AI — Tests: FastAPI Endpoints
# =============================================================

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_200():
    """GET /health should return 200 with status=healthy."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
    assert "llm_provider" in data


@pytest.mark.asyncio
async def test_chat_health_endpoint():
    """GET /api/v1/chat/health should return pipeline status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/chat/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "vector_store" in data


@pytest.mark.asyncio
async def test_chat_endpoint_validation_too_short():
    """POST /api/v1/chat with too-short query should return 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={"query": "hi"})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_tickets_list_endpoint():
    """GET /api/v1/tickets should return a list (possibly with seed data)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tickets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_tickets_stats_endpoint():
    """GET /api/v1/tickets/stats should return aggregate stats."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tickets/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_tickets" in data
    assert "resolved" in data
    assert "open" in data


@pytest.mark.asyncio
async def test_create_ticket():
    """POST /api/v1/tickets should create a ticket and return 201."""
    ticket_payload = {
        "user_id": "EMP-TEST-001",
        "category": "VPN",
        "priority": "medium",
        "summary": "Test VPN issue for automated testing purposes",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/tickets", json=ticket_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "EMP-TEST-001"
    assert data["category"] == "VPN"
    assert data["status"] == "open"
    assert data["ticket_id"].startswith("TKT-")


@pytest.mark.asyncio
async def test_get_ticket_not_found():
    """GET /api/v1/tickets/{id} for a non-existent ticket should return 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tickets/TKT-DOESNOTEXIST")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ticket_search_endpoint():
    """GET /api/v1/tickets/search?q=VPN should return results or empty list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tickets/search?q=VPN+connection+error")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_docs_endpoint_available():
    """GET /docs should return 200 (Swagger UI)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/docs")
    assert response.status_code == 200
