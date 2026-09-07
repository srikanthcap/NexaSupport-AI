# =============================================================
# NexaSupport AI — Pydantic API Schemas
# =============================================================
# PURPOSE:
#   Defines the data shapes for all API request and response bodies.
#
# CONCEPT — Why Pydantic schemas?
#   FastAPI uses Pydantic models to:
#   1. Validate incoming request data (wrong types → automatic 422 error).
#   2. Document the API in Swagger UI automatically.
#   3. Serialize response data to clean JSON.
#
#   Example:
#     If the client sends {"query": 123} but we expect a string,
#     Pydantic catches it and returns a clear validation error.
#     The endpoint code never even runs with bad data.
# =============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Chat / RAG Schemas ─────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """
    Request body for POST /api/v1/chat.
    
    The employee sends their IT support question here.
    """
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The IT support question from the employee.",
        example="My VPN keeps disconnecting with Error 809. How do I fix it?",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of knowledge base chunks to retrieve.",
    )
    conversation_history: list[dict] = Field(
        default_factory=list,
        description=(
            "Optional prior conversation turns. "
            "Format: [{'role': 'user'|'assistant', 'content': '...'}]"
        ),
    )
    filter_source: Optional[str] = Field(
        default=None,
        description="Restrict retrieval to a specific document file (optional).",
        example="01_vpn_troubleshooting.md",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "My VPN shows Error 809 and cannot connect. What should I do?",
                "top_k": 5,
                "conversation_history": [],
            }
        }


class SourceCitationResponse(BaseModel):
    """A single source citation shown alongside the AI answer."""
    citation_label: str = Field(description="[Source 1], [Source 2], etc.")
    title: str = Field(description="Document title.")
    source_file: str = Field(description="Original filename.")
    chunk_index: int = Field(description="Section number within the document.")
    similarity_score: float = Field(description="Relevance score (0.0–1.0).")


class ChatResponse(BaseModel):
    """
    Response body for POST /api/v1/chat.
    
    Contains the AI answer, source citations, and quality metadata.
    """
    query: str = Field(description="The original question.")
    answer: str = Field(description="The AI-generated grounded answer.")
    sources: list[SourceCitationResponse] = Field(
        default_factory=list,
        description="Knowledge base sources used to generate the answer.",
    )
    confidence: float = Field(
        description="Answer confidence score (0.0–1.0). Below 0.7 triggers escalation recommendation.",
    )
    is_grounded: bool = Field(
        description="True if the answer is backed by retrieved knowledge base sources.",
    )
    needs_escalation: bool = Field(
        description="True if confidence is below the threshold. User should consider creating a ticket.",
    )
    retrieval_count: int = Field(description="Number of knowledge base chunks retrieved.")
    llm_model: str = Field(description="LLM model used to generate the answer.")
    latency_ms: float = Field(description="Total end-to-end response time in milliseconds.")
    prompt_tokens: int = Field(default=0, description="Approximate LLM prompt token count.")
    output_tokens: int = Field(default=0, description="Approximate LLM output token count.")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "My VPN shows Error 809",
                "answer": "Error 809 is a VPN connection timeout. Try switching to SSL mode...",
                "sources": [
                    {
                        "citation_label": "Source 1",
                        "title": "VPN Troubleshooting Guide",
                        "source_file": "01_vpn_troubleshooting.md",
                        "chunk_index": 2,
                        "similarity_score": 0.87,
                    }
                ],
                "confidence": 0.83,
                "is_grounded": True,
                "needs_escalation": False,
                "retrieval_count": 3,
                "llm_model": "gemini-1.5-flash",
                "latency_ms": 1243.5,
            }
        }


# ── Ticket Schemas ─────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    """Request body for POST /api/v1/tickets."""
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Employee ID of the user creating the ticket.",
        example="EMP-1042",
    )
    category: str = Field(
        ...,
        description="Issue category.",
        example="VPN",
    )
    priority: str = Field(
        default="medium",
        pattern="^(low|medium|high|critical)$",
        description="Ticket priority: low, medium, high, or critical.",
    )
    summary: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Brief description of the IT issue.",
        example="VPN Error 809: Cannot connect from home network. Tried SSL mode, still fails.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Detailed description of the issue (optional).",
    )
    related_query: Optional[str] = Field(
        default=None,
        description="The original AI chat query that led to ticket creation.",
    )


class TicketResponse(BaseModel):
    """Response body for ticket operations."""
    id: int
    ticket_id: str
    user_id: str
    category: str
    priority: str
    status: str
    summary: str
    description: Optional[str]
    resolution: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy ORM objects


class TicketStatusUpdate(BaseModel):
    """Request body for PATCH /api/v1/tickets/{ticket_id}/status."""
    status: str = Field(
        ...,
        pattern="^(open|in_progress|resolved|escalated|closed)$",
        description="New ticket status.",
    )
    resolution: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Resolution notes (required when status is 'resolved').",
    )


# ── Feedback Schemas ───────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    """Request body for POST /api/v1/feedback."""
    query: str = Field(..., description="The original question.")
    answer: str = Field(..., description="The AI answer that was shown.")
    rating: str = Field(
        ...,
        pattern="^(helpful|not_helpful)$",
        description="User rating: 'helpful' or 'not_helpful'.",
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional free-text feedback from the user.",
    )
    confidence: Optional[float] = Field(
        default=None,
        description="The confidence score at time of response.",
    )


# ── Health / System Schemas ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Response body for GET /health."""
    status: str
    app: str
    version: str
    llm_provider: str
    vector_store_chunks: Optional[int] = None
