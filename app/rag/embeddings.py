# =============================================================
# NexaSupport AI — Embedding Service
# =============================================================
# PURPOSE:
#   Converts text into numerical vector representations (embeddings).
#   Supports two backends:
#     - 'local': HuggingFace sentence-transformers (free, no API key needed)
#     - 'gemini': Google Gemini embedding API (requires GEMINI_API_KEY)
#
# CONCEPT — What are embeddings?
#   An embedding is a list of numbers (e.g., 384 numbers for MiniLM) that
#   captures the MEANING of a piece of text. Similar sentences produce
#   similar vectors, so we can search by meaning — not just keywords.
#
#   Example:
#     "VPN is not working"  → [0.23, -0.41, 0.87, ...]
#     "Cannot connect VPN"  → [0.21, -0.39, 0.85, ...]  ← very similar!
#     "My printer jammed"   → [-0.12, 0.66, -0.33, ...] ← very different!
#
# HOW IT FITS:
#   text_chunker.py → [this file] → vector_store.py → ChromaDB
# =============================================================

from functools import lru_cache
from typing import Union

from loguru import logger

from app.config import settings


class EmbeddingService:
    """
    A unified embedding service that wraps either sentence-transformers
    (local) or Google Gemini (API-based) depending on configuration.

    Usage:
        service = EmbeddingService()
        vector = service.embed_text("VPN is not connecting")
        vectors = service.embed_texts(["VPN issue", "Email problem"])
    """

    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self._model = None
        self._init_model()

    def _init_model(self):
        """
        Initialize the chosen embedding backend.
        Called once during __init__.
        """
        if self.provider == "local":
            self._init_local_model()
        elif self.provider == "gemini":
            self._init_gemini_model()
        else:
            raise ValueError(
                f"Unknown EMBEDDING_PROVIDER: '{self.provider}'. "
                "Choose 'local' or 'gemini' in your .env file."
            )

    def _init_local_model(self):
        """
        Load a HuggingFace sentence-transformer model.

        'all-MiniLM-L6-v2' is the recommended starting model:
          - Fast (6-layer transformer)
          - Small (80 MB)
          - Good quality (384-dimensional embeddings)
          - Free, runs locally, no API key needed

        The model is downloaded on first use and cached to disk.
        """
        try:
            from sentence_transformers import SentenceTransformer
            model_name = settings.LOCAL_EMBEDDING_MODEL
            logger.info(f"Loading local embedding model: {model_name} (downloads on first use)...")
            self._model = SentenceTransformer(model_name)
            logger.info(f"✅ Local embedding model loaded: {model_name}")
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load local embedding model: {e}")

    def _init_gemini_model(self):
        """
        Configure the Google Gemini embedding API client.
        Requires GEMINI_API_KEY in .env.
        """
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file or switch EMBEDDING_PROVIDER=local"
            )
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = settings.GEMINI_EMBEDDING_MODEL
            logger.info(f"✅ Gemini embedding model configured: {self._model}")
        except ImportError:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            )

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string into a vector.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty or whitespace-only text.")

        if self.provider == "local":
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()

        elif self.provider == "gemini":
            import google.generativeai as genai
            result = genai.embed_content(
                model=self._model,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts. More efficient than calling embed_text() in a loop.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        # Filter out empty strings (would cause errors)
        cleaned = [t.strip() for t in texts]
        if any(not t for t in cleaned):
            raise ValueError("embed_texts received empty strings in the batch.")

        if self.provider == "local":
            # sentence-transformers handles batching natively and is faster than a loop
            embeddings = self._model.encode(
                cleaned,
                convert_to_numpy=True,
                show_progress_bar=len(cleaned) > 50,  # Show progress for large batches
            )
            return [e.tolist() for e in embeddings]

        elif self.provider == "gemini":
            # Gemini API does not support batch embedding — loop individually
            import google.generativeai as genai
            result = []
            for text in cleaned:
                response = genai.embed_content(
                    model=self._model,
                    content=text,
                    task_type="retrieval_document",
                )
                result.append(response["embedding"])
            return result

    @property
    def embedding_dimension(self) -> int:
        """
        Return the vector dimension of the current embedding model.
        Used when creating the ChromaDB collection to set the correct dimension.
        """
        if self.provider == "local":
            # all-MiniLM-L6-v2 produces 384-dimensional vectors
            return self._model.get_sentence_embedding_dimension()
        elif self.provider == "gemini":
            # Gemini embedding-001 produces 768-dimensional vectors
            return 768


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """
    Return a cached singleton EmbeddingService instance.

    Using lru_cache ensures the model is loaded only once per process.
    Loading a sentence-transformer model takes ~2-5 seconds the first time —
    we don't want to repeat that on every API request.

    Usage (anywhere in the project):
        from app.rag.embeddings import get_embedding_service
        service = get_embedding_service()
    """
    return EmbeddingService()
