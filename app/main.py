# =============================================================
# NexaSupport AI — FastAPI Application Entry Point
# This is the main backend server. Run with: uvicorn app.main:app --reload
# =============================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    
    Replaces the old @app.on_event("startup") / ("shutdown") approach.
    Code before 'yield' runs on startup. Code after 'yield' runs on shutdown.
    
    On startup we:
    1. Create all database tables (idempotent — safe to re-run).
    2. Seed synthetic ticket data (skipped if data already exists).
    """
    # ── Startup ────────────────────────────────────────────────
    logger.info("🚀 Starting NexaSupport AI backend...")

    # Initialize database tables and seed data
    try:
        from app.database.init_db import run_init
        await run_init()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't crash the whole app — the API can still serve RAG queries
        # without ticket functionality

    logger.info(f"✅ {settings.APP_NAME} v{settings.API_VERSION} ready")
    logger.info(f"📡 LLM: {settings.LLM_PROVIDER}/{settings.GEMINI_MODEL}")
    logger.info(f"📚 Embedding: {settings.EMBEDDING_PROVIDER}/{settings.LOCAL_EMBEDDING_MODEL}")
    logger.info(f"🗄️  Database: {settings.DATABASE_URL}")

    yield  # Application runs here

    # ── Shutdown ───────────────────────────────────────────────
    logger.info("👋 NexaSupport AI shutting down...")


def create_app() -> FastAPI:
    """
    Application factory pattern.
    Creates and configures the FastAPI application instance.
    
    Why a factory pattern?
    - Easier to test: each test can create a fresh app instance.
    - Clean separation of configuration from runtime logic.
    """

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=(
            "AI-Powered IT Support & Incident Resolution Agent. "
            "Resolves employee IT issues using RAG, Agentic AI, and Tool Calling."
        ),
        docs_url="/docs",      # Swagger UI: http://localhost:8000/docs
        redoc_url="/redoc",    # ReDoc UI:   http://localhost:8000/redoc
        lifespan=lifespan,
    )

    # ── CORS Middleware ────────────────────────────────────────
    # Allows the Streamlit frontend (port 8501) to call this API.
    # In production, replace "*" with the actual frontend domain.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register API Routers ───────────────────────────────────
    # Each router handles a specific domain (chat, tickets, etc.)
    # Adding them here keeps main.py clean and focused.

    from app.api.chat import router as chat_router
    app.include_router(chat_router)

    from app.api.tickets import router as tickets_router
    app.include_router(tickets_router)

    from app.api.feedback import router as feedback_router
    app.include_router(feedback_router)

    # ── Health Check Route ────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health_check():
        """
        Basic health check endpoint.
        Used by load balancers, monitoring tools, and the React/Streamlit frontend.
        """
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.API_VERSION,
            "llm_provider": settings.LLM_PROVIDER,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
        }

    # ── Static Files (React 18 Frontend) ──────────────────────
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend-react")
    if os.path.exists(frontend_dir):
        app.mount("/frontend-react", StaticFiles(directory=frontend_dir), name="frontend-react")

        @app.get("/", include_in_schema=False)
        async def serve_react_app():
            return FileResponse(os.path.join(frontend_dir, "index.html"))


    return app


# Create the app instance (imported by uvicorn)
app = create_app()


# ── Run directly with: python -m app.main ────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
