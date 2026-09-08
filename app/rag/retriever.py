# =============================================================
# NexaSupport AI — RAG Retriever
# =============================================================
# PURPOSE:
#   Retrieves the most relevant knowledge base chunks for a given query.
#   Applies a similarity threshold filter to drop low-quality results.
#
# CONCEPT — How retrieval works:
#   1. The user asks: "My VPN shows Error 809"
#   2. We embed this query into a vector.
#   3. We find the k chunks in ChromaDB whose vectors are closest.
#   4. We filter out chunks with similarity below the threshold.
#   5. We return the surviving chunks as context for the LLM.
#
# WHY THRESHOLD?
#   If no relevant docs exist (e.g., user asks about a coffee machine),
#   ChromaDB will still return SOMETHING — just with low scores.
#   The threshold ensures we don't pass irrelevant garbage to the LLM.
#
# HOW IT FITS:
#   vector_store.py → [this file] → prompt_builder.py → llm_client.py
# =============================================================

from dataclasses import dataclass
from typing import Optional

from loguru import logger

from app.config import settings
from app.rag.vector_store import SearchResult, VectorStoreService


@dataclass
class RetrievedChunk:
    """
    A retrieved knowledge chunk, enriched with citation information.
    
    Attributes:
        chunk_id        : Unique identifier for this chunk.
        text            : The chunk content that will be fed to the LLM.
        source_file     : Original document filename (e.g., '01_vpn_troubleshooting.md').
        title           : Human-readable document title.
        chunk_index     : Chunk position in the source document (0-indexed).
        total_chunks    : Total chunks in the source document.
        similarity_score: Relevance score (0.0–1.0, higher = more relevant).
        citation        : Formatted citation string for display to the user.
    """
    chunk_id: str = ""
    text: str = ""
    source_file: str = ""
    title: str = ""
    chunk_index: int = 0
    total_chunks: int = 1
    similarity_score: float = 0.0
    citation: str = ""


def _format_citation(title: str, source_file: str, chunk_index: int) -> str:
    """
    Format a human-readable citation string.

    Example: "VPN Troubleshooting Guide [01_vpn_troubleshooting.md, section 1]"
    """
    return f"{title} [{source_file}, section {chunk_index + 1}]"


class RAGRetriever:
    """
    Retrieves relevant IT knowledge base chunks for a user query.

    Wraps VectorStoreService with threshold filtering and richer metadata.

    Usage:
        retriever = RAGRetriever()
        chunks = retriever.retrieve("How do I fix Error 809 VPN?")
        for chunk in chunks:
            print(chunk.citation, chunk.similarity_score)
    """

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ):
        """
        Args:
            vector_store        : VectorStoreService instance (created if not provided).
            top_k               : Max number of chunks to retrieve. Defaults to settings.RAG_TOP_K.
            similarity_threshold: Min similarity to include a chunk. Defaults to settings.RAG_SIMILARITY_THRESHOLD.
        """
        self._vector_store = vector_store or VectorStoreService()
        self._top_k = top_k or settings.RAG_TOP_K
        self._threshold = similarity_threshold or settings.RAG_SIMILARITY_THRESHOLD

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_source: Optional[str] = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve the most relevant chunks for the given query.

        Args:
            query        : The user's IT support question.
            top_k        : Override the default top_k for this request.
            filter_source: Optional source file to restrict search to.
                           Example: "01_vpn_troubleshooting.md"

        Returns:
            List of RetrievedChunk objects, sorted by similarity (best first).
            May be empty if no chunks exceed the similarity threshold.
        """
        if not query or not query.strip():
            logger.warning("retrieve() called with empty query.")
            return []

        k = top_k or self._top_k

        # Build optional metadata filter
        metadata_filter = None
        if filter_source:
            metadata_filter = {"source_file": {"$eq": filter_source}}

        logger.debug(
            f"Retrieving top-{k} chunks for query: '{query[:80]}...' "
            f"(threshold={self._threshold})"
        )

        # Retrieve raw search results from ChromaDB
        raw_results: list[SearchResult] = self._vector_store.similarity_search(
            query=query,
            k=k,
            filter_metadata=metadata_filter,
        )

        if not raw_results:
            logger.debug("No results from ChromaDB. Is the index built?")
            return []

        # Apply similarity threshold filter
        filtered = [r for r in raw_results if r.similarity_score >= self._threshold]

        if not filtered:
            logger.info(
                f"All {len(raw_results)} results below threshold {self._threshold}. "
                f"Best score was {raw_results[0].similarity_score:.3f}."
            )
            return []

        logger.info(
            f"Retrieved {len(filtered)}/{len(raw_results)} chunks above threshold "
            f"(best score: {filtered[0].similarity_score:.3f})"
        )

        # Convert to RetrievedChunk with citation
        retrieved = []
        for r in filtered:
            retrieved.append(
                RetrievedChunk(
                    chunk_id=r.chunk_id,
                    text=r.text,
                    source_file=r.source_file,
                    title=r.title,
                    chunk_index=r.chunk_index,
                    total_chunks=int(r.metadata.get("total_chunks", 0)),
                    similarity_score=r.similarity_score,
                    citation=_format_citation(r.title, r.source_file, r.chunk_index),
                )
            )

        return retrieved

    def get_store_stats(self) -> dict:
        """Return ChromaDB collection statistics."""
        return self._vector_store.get_collection_stats()
