# =============================================================
# NexaSupport AI — Vector Store Service (ChromaDB)
# =============================================================
# PURPOSE:
#   Manages the ChromaDB vector database.
#   Provides methods to add, search, and inspect chunks stored as vectors.
#
# CONCEPT — What is a vector store?
#   After converting text to embeddings (numbers), we need a place to
#   store them so we can search efficiently. ChromaDB is a specialized
#   database built specifically for storing and searching vectors.
#
#   Think of it like a library where books are organized not by title
#   or author, but by "meaning" — similar books are shelved near each other.
#   When you ask a question, the library gives you the closest books
#   by meaning, not by exact word match.
#
#   ChromaDB extras we use:
#     - Persistent storage: vectors survive application restarts
#     - Metadata filtering: e.g., "only search VPN documents"
#     - Returns distance scores: lets us filter low-quality results
#
# HOW IT FITS:
#   embeddings.py → [this file] → retriever.py → RAG pipeline
# =============================================================

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from app.config import settings
from app.rag.embeddings import get_embedding_service
from app.utils.text_chunker import Chunk


@dataclass
class SearchResult:
    """
    A single document chunk retrieved from ChromaDB vector search.

    Attributes:
        chunk_id       : Unique ID of the chunk.
        text           : The raw chunk text (returned to the LLM as context).
        source_file    : The original document filename.
        title          : The document title.
        chunk_index    : Position of this chunk in the source document.
        similarity_score: Cosine similarity score (0.0–1.0, higher = more relevant).
        metadata       : Full metadata dict stored alongside the vector.
    """
    chunk_id: str
    text: str
    source_file: str
    title: str
    chunk_index: int
    similarity_score: float
    metadata: dict


class VectorStoreService:
    """
    Wraps ChromaDB to provide a clean interface for indexing and searching
    IT knowledge base chunks.

    ChromaDB stores:
      - Vector embeddings (the numbers representing text meaning)
      - Raw text documents (the actual chunk text)
      - Metadata (filename, title, chunk_index, etc.)

    Usage:
        store = VectorStoreService()
        store.add_chunks(all_chunks)
        results = store.similarity_search("VPN Error 809", k=5)
    """

    def __init__(self):
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None
        self._embedding_service = get_embedding_service()

    def _get_client(self) -> chromadb.PersistentClient:
        """
        Lazily initialize and return the ChromaDB persistent client.
        
        PersistentClient stores the vector database to disk at CHROMA_PERSIST_DIR.
        This means the index survives application restarts — you only need to
        run build_index.py once (or when documents change).
        """
        if self._client is None:
            persist_path = Path(self.persist_dir)
            persist_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Initializing ChromaDB at {persist_path.resolve()}")
            self._client = chromadb.PersistentClient(
                path=str(persist_path.resolve()),
            )
        return self._client

    def _get_collection(self):
        """
        Get or create the ChromaDB collection.
        
        A ChromaDB "collection" is like a table in a SQL database.
        We have one collection: 'it_knowledge_base'.
        
        We use embedding_function=None because we generate our own embeddings
        externally using EmbeddingService, giving us more control.
        """
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                # embedding_function=None means we pass pre-computed embeddings
                # This gives us control over the embedding model
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )
            logger.debug(
                f"ChromaDB collection '{self.collection_name}' ready. "
                f"Current count: {self._collection.count()} documents"
            )
        return self._collection

    def add_chunks(self, chunks: list[Chunk], batch_size: int = 50) -> int:
        """
        Embed and add a list of Chunk objects to ChromaDB.
        
        Processes chunks in batches to avoid memory issues with large corpora.
        Already-existing chunk IDs are skipped (upsert behavior).
        
        Args:
            chunks    : List of Chunk objects from text_chunker.py
            batch_size: Number of chunks to process in one batch.
        
        Returns:
            Number of chunks successfully added.
        """
        if not chunks:
            logger.warning("add_chunks called with empty list — nothing to do.")
            return 0

        collection = self._get_collection()
        total_added = 0

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            
            ids = [c.chunk_id for c in batch]
            texts = [c.text for c in batch]
            metadatas = [c.metadata for c in batch]

            # Generate embeddings for the batch
            logger.debug(f"Embedding batch {i//batch_size + 1} ({len(batch)} chunks)...")
            embeddings = self._embedding_service.embed_texts(texts)

            # Upsert into ChromaDB (insert new, update existing)
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            total_added += len(batch)
            logger.info(f"Indexed {total_added}/{len(chunks)} chunks...")

        logger.info(f"✅ ChromaDB indexing complete. Total documents in collection: {collection.count()}")
        return total_added

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> list[SearchResult]:
        """
        Search the vector store for chunks most semantically similar to the query.
        
        Args:
            query          : The user's IT support question.
            k              : Number of results to return.
            filter_metadata: Optional ChromaDB metadata filter dict.
                             Example: {"source_file": "01_vpn_troubleshooting.md"}
        
        Returns:
            List of SearchResult objects, sorted by similarity (best first).
        
        How ChromaDB search works:
          1. Embed the query into a vector.
          2. Use HNSW (approximate nearest neighbor) index to find the k vectors
             in the collection closest to the query vector.
          3. Return those vectors' associated documents and metadata.
        """
        collection = self._get_collection()

        if collection.count() == 0:
            logger.warning("ChromaDB collection is empty. Run build_index.py first.")
            return []

        # Embed the user query
        query_embedding = self._embedding_service.embed_text(query)

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),  # Cannot request more than exists
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"] or not results["ids"][0]:
            return []

        search_results = []
        for idx, chunk_id in enumerate(results["ids"][0]):
            raw_distance = results["distances"][0][idx]
            
            # ChromaDB with cosine space returns distance (0=identical, 2=opposite).
            # Convert to similarity score (1=identical, -1=opposite).
            # We normalize to 0.0–1.0 range: similarity = 1 - (distance / 2)
            similarity_score = round(1.0 - (raw_distance / 2.0), 4)

            meta = results["metadatas"][0][idx] or {}
            text = results["documents"][0][idx] or ""

            search_results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    text=text,
                    source_file=meta.get("source_file", "unknown"),
                    title=meta.get("title", "Unknown Document"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    similarity_score=similarity_score,
                    metadata=meta,
                )
            )

        return search_results

    def get_collection_stats(self) -> dict:
        """
        Return statistics about the current ChromaDB collection.
        
        Useful for health checks and admin dashboard.
        """
        collection = self._get_collection()
        count = collection.count()
        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "persist_directory": str(Path(self.persist_dir).resolve()),
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": (
                settings.LOCAL_EMBEDDING_MODEL
                if settings.EMBEDDING_PROVIDER == "local"
                else settings.GEMINI_EMBEDDING_MODEL
            ),
        }

    def delete_collection(self):
        """
        Delete and recreate the ChromaDB collection (full reset).
        
        Use this when re-ingesting all documents from scratch.
        WARNING: This permanently deletes all indexed vectors.
        """
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
            logger.warning(f"Deleted ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.debug(f"Collection did not exist (safe to ignore): {e}")
        
        # Reset cached collection reference
        self._collection = None
        self._get_collection()  # Recreate empty collection
        logger.info(f"Created fresh ChromaDB collection: {self.collection_name}")
