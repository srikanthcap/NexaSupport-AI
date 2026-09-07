# =============================================================
# NexaSupport AI — RAG Pipeline Orchestrator
# =============================================================
# PURPOSE:
#   The main entry point for a complete RAG query.
#   Orchestrates: Retriever → PromptBuilder → LLMClient
#   Returns a fully structured RAGResponse with answer, sources,
#   and a confidence score.
#
# CONCEPT — What is a pipeline?
#   A pipeline is a sequence of steps where the output of each step
#   feeds into the next. Our RAG pipeline:
#     1. RETRIEVE  : Find relevant chunks from ChromaDB.
#     2. BUILD     : Assemble a grounded prompt with those chunks.
#     3. GENERATE  : Call the LLM to produce an answer.
#     4. EVALUATE  : Compute a confidence score.
#     5. RETURN    : Package everything into a clean RAGResponse.
#
# CONFIDENCE SCORING (Phase 11 will add more sophistication):
#   For now, we use a simple heuristic:
#     - Average similarity of retrieved chunks.
#     - Penalize if fewer than 2 chunks were found.
#     - Zero confidence if no chunks found.
#
# HOW IT FITS:
#   retriever.py + prompt_builder.py + llm_client.py → [this file] → API
# =============================================================

import time
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from app.config import settings
from app.rag.llm_client import LLMClient, LLMResponse, get_llm_client
from app.rag.prompt_builder import build_rag_prompt, format_no_context_response
from app.rag.retriever import RAGRetriever, RetrievedChunk


@dataclass
class SourceCitation:
    """
    A source citation to show to the user.
    
    Attributes:
        citation_label : The [Source N] label used in the answer.
        title          : Human-readable document title.
        source_file    : Original filename.
        chunk_index    : Which section/chunk of the document.
        similarity_score: How relevant this chunk was (0.0–1.0).
    """
    citation_label: str
    title: str
    source_file: str
    chunk_index: int
    similarity_score: float


@dataclass
class RAGResponse:
    """
    The complete, structured output of one RAG query.
    
    Attributes:
        query          : The original user question.
        answer         : The LLM-generated answer text.
        sources        : List of source citations used.
        confidence     : Confidence score (0.0–1.0).
        is_grounded    : True if the answer has supporting sources.
        needs_escalation: True if confidence is below the threshold.
        llm_model      : Which LLM model was used.
        retrieval_count: How many chunks were retrieved.
        latency_ms     : Total pipeline latency in milliseconds.
        prompt_tokens  : LLM prompt token count.
        output_tokens  : LLM output token count.
    """
    query: str
    answer: str
    sources: list[SourceCitation] = field(default_factory=list)
    confidence: float = 0.0
    is_grounded: bool = False
    needs_escalation: bool = True
    llm_model: str = ""
    retrieval_count: int = 0
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0


def _compute_confidence(retrieved_chunks: list[RetrievedChunk]) -> float:
    """
    Compute a simple confidence score based on retrieval quality.
    
    Heuristic (Phase 11 will replace this with LLM-based evaluation):
    - No chunks found          → 0.0
    - 1 chunk, low similarity  → 0.2–0.4
    - 2+ chunks, good scores   → 0.6–0.9
    
    Formula:
        base_score = average similarity of top chunks
        if < 2 chunks: apply 0.7× penalty (less evidence = less confident)
        if top similarity < 0.5: apply 0.8× penalty
    """
    if not retrieved_chunks:
        return 0.0

    scores = [c.similarity_score for c in retrieved_chunks]
    avg_score = sum(scores) / len(scores)

    # Penalty for fewer chunks
    chunk_penalty = 1.0 if len(retrieved_chunks) >= 2 else 0.7

    # Penalty for low top-1 similarity
    top_score_penalty = 1.0 if scores[0] >= 0.5 else 0.8

    confidence = min(avg_score * chunk_penalty * top_score_penalty, 1.0)
    return round(confidence, 3)


def _build_source_citations(chunks: list[RetrievedChunk]) -> list[SourceCitation]:
    """Convert RetrievedChunk objects into SourceCitation objects for the API response."""
    return [
        SourceCitation(
            citation_label=f"Source {i + 1}",
            title=chunk.title,
            source_file=chunk.source_file,
            chunk_index=chunk.chunk_index,
            similarity_score=chunk.similarity_score,
        )
        for i, chunk in enumerate(chunks)
    ]


class RAGPipeline:
    """
    Orchestrates the complete Retrieve → Augment → Generate pipeline.
    
    This is the main class used by API endpoints and the agent.
    
    Usage:
        pipeline = RAGPipeline()
        response = pipeline.query("How do I fix VPN Error 809?")
        print(response.answer)
        print(response.confidence)
        for source in response.sources:
            print(source.citation_label, source.title)
    """

    def __init__(
        self,
        retriever: Optional[RAGRetriever] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        """
        Args:
            retriever  : RAGRetriever instance (created if not provided).
            llm_client : LLMClient instance (created if not provided).
        """
        self._retriever = retriever or RAGRetriever()
        self._llm = llm_client or get_llm_client()

    def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        conversation_history: Optional[list[dict]] = None,
        filter_source: Optional[str] = None,
    ) -> RAGResponse:
        """
        Execute a complete RAG query and return a structured response.
        
        Args:
            query               : The employee's IT support question.
            top_k               : Override default number of chunks to retrieve.
            conversation_history: Prior conversation turns for context.
            filter_source       : Restrict retrieval to a specific document file.
        
        Returns:
            RAGResponse with answer, sources, confidence, and metadata.
        """
        if not query or not query.strip():
            return RAGResponse(
                query=query,
                answer="Please provide a question so I can help you.",
                confidence=0.0,
                needs_escalation=True,
            )

        start_time = time.time()
        logger.info(f"RAG query: '{query[:100]}...' " if len(query) > 100 else f"RAG query: '{query}'")

        # ── Step 1: Retrieve relevant chunks ──────────────────
        retrieved_chunks = self._retriever.retrieve(
            query=query,
            top_k=top_k,
            filter_source=filter_source,
        )
        logger.debug(f"Retrieved {len(retrieved_chunks)} chunk(s) above threshold")

        # ── Step 2: Compute confidence ─────────────────────────
        confidence = _compute_confidence(retrieved_chunks)
        is_grounded = len(retrieved_chunks) > 0
        needs_escalation = confidence < settings.CONFIDENCE_THRESHOLD

        # ── Step 3: Handle no-context case ────────────────────
        if not retrieved_chunks:
            elapsed = (time.time() - start_time) * 1000
            logger.warning(f"No relevant context found for query. Confidence=0.0")
            return RAGResponse(
                query=query,
                answer=format_no_context_response(),
                sources=[],
                confidence=0.0,
                is_grounded=False,
                needs_escalation=True,
                llm_model=settings.GEMINI_MODEL,
                retrieval_count=0,
                latency_ms=round(elapsed, 2),
            )

        # ── Step 4: Build grounded prompt ─────────────────────
        prompt = build_rag_prompt(
            query=query,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history,
        )

        # ── Step 5: Generate LLM response ─────────────────────
        try:
            llm_response: LLMResponse = self._llm.generate(prompt)
        except RuntimeError as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"LLM generation failed: {e}")
            return RAGResponse(
                query=query,
                answer=(
                    f"I encountered an error generating a response. "
                    f"Please try again or contact IT Helpdesk. (Error: {e})"
                ),
                sources=_build_source_citations(retrieved_chunks),
                confidence=0.0,
                is_grounded=True,
                needs_escalation=True,
                retrieval_count=len(retrieved_chunks),
                latency_ms=round(elapsed, 2),
            )

        # ── Step 6: Package response ───────────────────────────
        elapsed = (time.time() - start_time) * 1000
        logger.info(
            f"RAG pipeline complete: confidence={confidence:.3f}, "
            f"escalate={needs_escalation}, latency={elapsed:.0f}ms"
        )

        return RAGResponse(
            query=query,
            answer=llm_response.text,
            sources=_build_source_citations(retrieved_chunks),
            confidence=confidence,
            is_grounded=is_grounded,
            needs_escalation=needs_escalation,
            llm_model=llm_response.model,
            retrieval_count=len(retrieved_chunks),
            latency_ms=round(elapsed, 2),
            prompt_tokens=llm_response.prompt_tokens,
            output_tokens=llm_response.output_tokens,
        )


# ── Singleton instance ────────────────────────────────────────────────────────
# Lazily initialized when first accessed. This avoids loading the embedding
# model and Gemini client at import time.
_pipeline_instance: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Return the singleton RAGPipeline instance.
    
    The pipeline is expensive to initialize (loads embedding model, connects
    to ChromaDB, configures LLM client). We initialize it once and reuse it
    across all API requests.
    
    Usage:
        from app.rag.pipeline import get_rag_pipeline
        pipeline = get_rag_pipeline()
        response = pipeline.query("My email is not working")
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        logger.info("Initializing RAGPipeline (first request)...")
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
