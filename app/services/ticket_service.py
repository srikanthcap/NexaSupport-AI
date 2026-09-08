# =============================================================
# NexaSupport AI — Ticket Service (Business Logic)
# =============================================================
# PURPOSE:
#   All database operations for tickets in one place.
#   API routes call this service — they don't write SQL themselves.
#   This separation makes it easy to test business logic independently.
#
# PATTERN — Service Layer:
#   Route (HTTP layer) → Service (business logic) → Database (persistence)
#   Each layer has one job. The service doesn't know about HTTP requests,
#   and routes don't know about SQL queries.
# =============================================================

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Ticket
from app.models.schemas import TicketCreate, TicketStatusUpdate


def _next_ticket_id(count: int) -> str:
    """Generate the next ticket ID. Format: TKT-YYYY{N:04d}"""
    year = datetime.utcnow().year
    return f"TKT-{year}{count + 1:04d}"


class TicketService:
    """
    Handles all ticket CRUD operations.
    
    Usage:
        service = TicketService(db)
        ticket = await service.create_ticket(ticket_data)
        tickets = await service.list_tickets()
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(self, data: TicketCreate) -> Ticket:
        """
        Create a new IT support ticket.
        
        Generates a unique ticket_id and persists the ticket to the database.
        """
        # Get current count to generate next sequential ID
        result = await self.db.execute(select(func.count()).select_from(Ticket))
        count = result.scalar() or 0

        ticket = Ticket(
            ticket_id=_next_ticket_id(count),
            user_id=data.user_id,
            category=data.category,
            priority=data.priority,
            status="open",
            summary=data.summary,
            description=data.description,
            is_escalated=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            ai_answer=None,  # Set externally if created from chat
        )
        self.db.add(ticket)
        await self.db.flush()  # Get the auto-generated ID without committing
        await self.db.refresh(ticket)

        logger.info(f"Created ticket {ticket.ticket_id} for user {data.user_id}")
        return ticket

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get a single ticket by its ticket_id (e.g., 'TKT-20240001')."""
        result = await self.db.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def list_tickets(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Ticket]:
        """
        List tickets with optional filtering.
        
        Args:
            status  : Filter by status (open, in_progress, resolved, etc.)
            category: Filter by category (VPN, Email, etc.)
            user_id : Filter by employee ID.
            limit   : Maximum number of results (default 50).
            offset  : Pagination offset.
        
        Returns:
            List of Ticket objects, newest first.
        """
        query = select(Ticket).order_by(Ticket.created_at.desc())

        if status:
            query = query.where(Ticket.status == status)
        if category:
            query = query.where(Ticket.category == category)
        if user_id:
            query = query.where(Ticket.user_id == user_id)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_ticket_status(
        self, ticket_id: str, update: TicketStatusUpdate
    ) -> Optional[Ticket]:
        """
        Update the status (and optional resolution) of a ticket.
        
        Automatically sets resolved_at timestamp when status → resolved.
        """
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return None

        ticket.status = update.status
        ticket.updated_at = datetime.utcnow()

        if update.resolution:
            ticket.resolution = update.resolution

        if update.status == "resolved" and ticket.resolved_at is None:
            ticket.resolved_at = datetime.utcnow()

        if update.status == "escalated":
            ticket.is_escalated = True

        await self.db.flush()
        await self.db.refresh(ticket)
        logger.info(f"Updated ticket {ticket_id} status → {update.status}")
        return ticket

    async def search_similar_incidents(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> list[Ticket]:
        """
        Search historical resolved tickets for similar incidents.
        
        Simple keyword search across summary and resolution fields.
        (Phase 13 will upgrade this to semantic/hybrid search.)
        
        Args:
            query   : Keywords to search for.
            category: Optionally restrict to a specific category.
            limit   : Maximum results.
        
        Returns:
            List of resolved Ticket objects most relevant to the query.
        """
        # Extract keywords (split query into individual words, filter short ones)
        keywords = [kw.strip() for kw in query.lower().split() if len(kw.strip()) > 3]

        if not keywords:
            return []

        # Build OR search across summary, description, and resolution
        # This is a simple keyword search — good enough for Phase 7
        search_filter = or_(
            *[
                or_(
                    Ticket.summary.ilike(f"%{kw}%"),
                    Ticket.description.ilike(f"%{kw}%"),
                    Ticket.resolution.ilike(f"%{kw}%"),
                )
                for kw in keywords[:5]  # Limit to first 5 keywords
            ]
        )

        db_query = (
            select(Ticket)
            .where(search_filter)
            .where(Ticket.status.in_(["resolved", "escalated"]))
        )

        if category:
            db_query = db_query.where(Ticket.category == category)

        db_query = db_query.order_by(Ticket.created_at.desc()).limit(limit)
        result = await self.db.execute(db_query)
        tickets = list(result.scalars().all())

        logger.debug(f"Found {len(tickets)} similar incident(s) for query: '{query[:60]}'")
        return tickets

    async def get_stats(self) -> dict:
        """
        Return aggregate statistics for the admin dashboard.
        
        Returns:
            Dict with total, open, resolved, escalated, and by-category counts.
        """
        total_result = await self.db.execute(select(func.count()).select_from(Ticket))
        total = total_result.scalar() or 0

        open_result = await self.db.execute(
            select(func.count()).select_from(Ticket).where(Ticket.status == "open")
        )
        open_count = open_result.scalar() or 0

        resolved_result = await self.db.execute(
            select(func.count()).select_from(Ticket).where(Ticket.status == "resolved")
        )
        resolved_count = resolved_result.scalar() or 0

        escalated_result = await self.db.execute(
            select(func.count()).select_from(Ticket).where(Ticket.is_escalated == True)
        )
        escalated_count = escalated_result.scalar() or 0

        return {
            "total_tickets": total,
            "open": open_count,
            "resolved": resolved_count,
            "escalated": escalated_count,
            "in_progress": total - open_count - resolved_count - escalated_count,
            "resolution_rate": round(resolved_count / total * 100, 1) if total > 0 else 0.0,
        }


# ── Standalone Helper Functions (Convenience Wrappers) ───────────────────────

async def create_ticket(
    session: AsyncSession,
    user_id: str,
    category: str,
    priority: str = "medium",
    summary: str = "",
    description: str = "",
) -> Ticket:
    """Convenience wrapper around TicketService.create_ticket."""
    service = TicketService(session)
    data = TicketCreate(
        user_id=user_id,
        category=category,
        priority=priority,
        summary=summary,
        description=description,
    )
    return await service.create_ticket(data)


async def search_tickets_fulltext(
    session: AsyncSession,
    query: str,
    category: Optional[str] = None,
    limit: int = 5,
) -> list[Ticket]:
    """Convenience wrapper around TicketService.search_similar_incidents."""
    service = TicketService(session)
    return await service.search_similar_incidents(query=query, category=category, limit=limit)


async def get_ticket_by_id(
    session: AsyncSession,
    ticket_id: str,
) -> Optional[Ticket]:
    """Convenience wrapper around TicketService.get_ticket."""
    service = TicketService(session)
    return await service.get_ticket(ticket_id)

