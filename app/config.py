# =============================================================
# NexaSupport AI — Central Configuration
# Reads all settings from the .env file automatically.
# =============================================================

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    All application configuration in one place.
    Values are loaded from the .env file via pydantic-settings.
    
    Why pydantic-settings?
    - Automatic type validation (if LLM_TEMPERATURE should be a float, it enforces that).
    - Clean, readable config access: settings.GEMINI_API_KEY
    - Centralized: no scattered os.getenv() calls throughout the codebase.
    """

    # ── LLM Configuration ─────────────────────────────────────
    LLM_PROVIDER: str = Field(default="gemini", description="LLM provider: 'gemini' or 'openai'")
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key (optional fallback)")

    # Gemini model names - use a fast model for production
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash", description="Gemini model name")
    GEMINI_EMBEDDING_MODEL: str = Field(default="models/embedding-001", description="Gemini embedding model")

    # LLM generation parameters
    LLM_TEMPERATURE: float = Field(default=0.1, description="LLM response randomness (0=deterministic, 1=creative)")
    LLM_MAX_TOKENS: int = Field(default=2048, description="Max tokens in LLM response")

    # ── Embedding Configuration ────────────────────────────────
    # Which embedding backend to use: 'local' = sentence-transformers, 'gemini' = Gemini API
    EMBEDDING_PROVIDER: str = Field(default="local", description="'local' or 'gemini'")
    LOCAL_EMBEDDING_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="HuggingFace sentence-transformer model name"
    )

    # ── Vector Database (ChromaDB) ─────────────────────────────
    CHROMA_PERSIST_DIR: str = Field(default="./data/chroma_db", description="ChromaDB storage directory")
    CHROMA_COLLECTION_NAME: str = Field(default="it_knowledge_base", description="ChromaDB collection name")

    # ── Relational Database ────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/nexasupport.db",
        description="Database connection string. Use PostgreSQL URL in production."
    )

    # ── RAG Retrieval Configuration ───────────────────────────
    RAG_TOP_K: int = Field(default=5, description="Number of chunks to retrieve from vector DB")
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.4, description="Minimum similarity score for a chunk to be included")

    # ── Confidence & Guardrails ───────────────────────────────
    # If answer confidence is below this threshold, the system escalates to a human engineer
    CONFIDENCE_THRESHOLD: float = Field(default=0.70, description="Minimum confidence to give an answer without escalation")

    # ── Chunking Configuration ────────────────────────────────
    CHUNK_SIZE: int = Field(default=512, description="Target chunk size in characters/tokens")
    CHUNK_OVERLAP: int = Field(default=50, description="Overlap between consecutive chunks to preserve context")

    # ── FastAPI Configuration ─────────────────────────────────
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port")
    API_TITLE: str = Field(default="NexaSupport AI", description="API title shown in Swagger docs")
    API_VERSION: str = Field(default="1.0.0", description="API version")
    DEBUG: bool = Field(default=True, description="Enable debug mode (disable in production)")

    # ── Application Metadata ──────────────────────────────────
    APP_NAME: str = Field(default="NexaSupport AI", description="Application display name")
    COMPANY_NAME: str = Field(default="Acme Corp", description="Company name shown in the UI")

    class Config:
        # Tells pydantic-settings to read from a file named .env in the project root
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields without raising errors (useful during development)
        extra = "ignore"


# Create a single shared instance.
# Import this anywhere in the project: from app.config import settings
settings = Settings()
