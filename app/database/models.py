# =============================================================
# NexaSupport AI — SQLAlchemy ORM Models (Database Tables)
# =============================================================
# PURPOSE:
#   Defines the database table structure using SQLAlchemy ORM.
#   ORM = Object-Relational Mapper: lets us work with database rows
#   as Python objects instead of writing raw SQL.
#
# CONCEPT — What is an ORM?
#   Instead of:
#     INSERT INTO tickets (user_id, summary) VALUES ('EMP-001', 'VPN issue')
#   We write:
#     ticket = Ticket(user_id='EMP-001', summary='VPN issue')
#     session.add(ticket)
#
#   SQLAlchemy translates Python objects → SQL for us.
#   This also means we can swap SQLite (dev) for PostgreSQL (prod)
#   by just changing the DATABASE_URL in .env — no code changes needed.
#
# HOW IT FITS:
#   [this file] → session.py → ticket_service.py → tickets API
# =============================================================

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    All models inherit from this — SQLAlchemy uses it to track table definitions.
    """
    pass


class Ticket(Base):
    """
    Represents an IT support ticket.
    
    Maps to the 'tickets' table in the database.
    
    Fields:
        id         : Auto-incremented primary key (internal).
        ticket_id  : Human-readable ID, e.g., 'TKT-20240001'.
        user_id    : Employee ID of the requester, e.g., 'EMP-1042'.
        category   : Issue type: VPN, Email, Password, Network, Software, Hardware, Access, Other.
        priority   : low | medium | high | critical
        status     : open | in_progress | resolved | escalated | closed
        summary    : One-line description of the issue.
        description: Full description (optional, can be long).
        resolution : How the issue was resolved (filled when status → resolved).
        is_escalated: Whether this ticket was escalated to a human engineer.
        created_at : Timestamp when ticket was created.
        updated_at : Timestamp when ticket was last modified.
        resolved_at: Timestamp when ticket was marked resolved.
        ai_answer  : The AI response that was given when the ticket was created.
        ai_confidence: The AI's confidence score at ticket creation time.
    """
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ai_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<Ticket id={self.ticket_id} user={self.user_id} status={self.status}>"


class ConversationMessage(Base):
    """
    Stores individual messages in a conversation session.
    
    Maps to the 'conversation_messages' table.
    Used in Phase 12 (conversation memory) to persist chat history.
    
    Fields:
        id            : Auto-incremented primary key.
        session_id    : UUID identifying the conversation session.
        role          : 'user' or 'assistant'.
        content       : The message text.
        confidence    : Confidence score (for assistant messages).
        sources_count : Number of sources cited in this message.
        created_at    : When this message was sent.
    """
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sources_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage session={self.session_id} role={self.role}>"


class FeedbackEntry(Base):
    """
    Stores user feedback (thumbs up/down) on AI responses.
    
    Maps to the 'feedback_entries' table.
    Used in Phase 17 (feedback system) and Phase 18 (RAGAS evaluation).
    
    Fields:
        id         : Auto-incremented primary key.
        query      : The original question.
        answer     : The AI answer that was rated.
        rating     : 'helpful' or 'not_helpful'.
        comment    : Optional user comment.
        confidence : AI confidence at time of answer.
        created_at : Timestamp.
    """
    __tablename__ = "feedback_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<FeedbackEntry rating={self.rating}>"
