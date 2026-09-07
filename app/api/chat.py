# =============================================================
# NexaSupport AI — Chat API Router
# =============================================================
# PURPOSE:
#   FastAPI router for the chat endpoint.
#   Accepts employee questions, runs the RAG pipeline, and returns answers.
#
# ENDPOINT:
#   POST /api/v1/chat
#
# HOW IT FITS:
#   Employee → HTTP POST → [this file] → RAGPipeline → Response
# =============================================================

from fastapi import APIRouter, HTTPException, status
from loguru import logger

from app.models.schemas import ChatResponse, QueryRequest, SourceCitationResponse
from app.rag.pipeline import RAGResponse, get_rag_pipeline

# Create a router — think of this as a mini FastAPI app just for chat routes.
# The prefix /api/v1 is added when registering this router in main.py
router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask the IT Support AI",
    description=(
        "Submit an IT support question. "
        "The AI will retrieve relevant knowledge base documents and generate a grounded answer. "
        "Returns the answer, source citations, confidence score, and escalation recommendation."
    ),
    status_code=status.HTTP_200_OK,
)
async def chat(request: QueryRequest) -> ChatResponse:
    """
    Main chat endpoint. Runs the full RAG pipeline for the given query.

    - **query**: The employee's IT support question (3–2000 characters).
    - **top_k**: How many knowledge chunks to retrieve (default 5).
    - **conversation_history**: Optional prior turns for context.
    - **filter_source**: Optional filename to restrict retrieval scope.

    Returns a structured response with:
    - **answer**: AI-generated, grounded answer.
    - **sources**: Knowledge base citations.
    - **confidence**: 0.0–1.0 reliability score.
    - **needs_escalation**: Whether to recommend a human engineer.
    """
    logger.info(f"Chat request received: '{request.query[:80]}...' " 
                if len(request.query) > 80 else f"Chat request: '{request.query}'")

    try:
        # Use the Agentic Support Orchestrator with tool-augmented workflows
        from app.agents.support_agent import get_support_agent
        agent = get_support_agent()

        rag_response: RAGResponse = await agent.execute_plan(
            query=request.query,
            employee_id=request.employee_id,
            top_k=request.top_k,
            conversation_history=request.conversation_history or None,
        )

        # Convert internal RAGResponse to the API response schema
        return ChatResponse(
            query=rag_response.query,
            answer=rag_response.answer,
            sources=[
                SourceCitationResponse(
                    citation_label=s.citation_label,
                    title=s.title,
                    source_file=s.source_file,
                    chunk_index=s.chunk_index,
                    similarity_score=s.similarity_score,
                )
                for s in rag_response.sources
            ],
            confidence=rag_response.confidence,
            is_grounded=rag_response.is_grounded,
            needs_escalation=rag_response.needs_escalation,
            retrieval_count=rag_response.retrieval_count,
            llm_model=rag_response.llm_model,
            latency_ms=rag_response.latency_ms,
            prompt_tokens=rag_response.prompt_tokens,
            output_tokens=rag_response.output_tokens,
        )

    except Exception as e:
        # Log the full exception for debugging but return a safe error to the client
        logger.exception(f"Unhandled error in /chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"An internal error occurred while processing your request. "
                f"Please try again. If the problem persists, contact IT support. "
                f"(Error: {type(e).__name__})"
            ),
        )


@router.get(
    "/chat/health",
    summary="Check RAG pipeline readiness",
    tags=["System"],
)
async def chat_health():
    """
    Check if the RAG pipeline is initialized and the knowledge base is indexed.
    
    Returns the number of chunks in the vector store.
    """
    try:
        pipeline = get_rag_pipeline()
        stats = pipeline._retriever.get_store_stats()
        return {
            "status": "ready" if stats["total_chunks"] > 0 else "empty_index",
            "vector_store": stats,
            "message": (
                "RAG pipeline is ready." if stats["total_chunks"] > 0
                else "ChromaDB index is empty. Run python scripts/build_index.py"
            ),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
