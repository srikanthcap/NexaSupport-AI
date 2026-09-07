# =============================================================
# NexaSupport AI — Tickets API Router
# =============================================================
# PURPOSE:
#   FastAPI router for ticket CRUD operations.
#
# ENDPOINTS:
#   GET  /api/v1/tickets              — List tickets (with filters)
#   POST /api/v1/tickets              — Create a new ticket
#   GET  /api/v1/tickets/{ticket_id}  — Get a single ticket
#   PATCH /api/v1/tickets/{ticket_id}/status — Update ticket status
#   GET  /api/v1/tickets/search       — Search similar historical incidents
#   GET  /api/v1/tickets/stats        — Aggregate stats for admin dashboard
# =============================================================

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.schemas import TicketCreate, TicketResponse, TicketStatusUpdate
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])


@router.get(
    "",
    response_model=list[TicketResponse],
    summary="List all tickets",
)
async def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category (VPN, Email, etc.)"),
    user_id: Optional[str] = Query(None, description="Filter by employee ID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> list[TicketResponse]:
    """
    List IT support tickets with optional filtering.
    
    - **status**: open | in_progress | resolved | escalated | closed
    - **category**: VPN | Email | Password | Network | Software | Hardware | Access | Other
    - **user_id**: Employee ID (e.g., EMP-1042)
    """
    service = TicketService(db)
    tickets = await service.list_tickets(
        status=status_filter,
        category=category,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return tickets


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new IT support ticket",
)
async def create_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """
    Create a new IT support ticket.
    
    Tickets are created when:
    - The AI cannot resolve an issue confidently.
    - The employee explicitly requests a ticket.
    - An agent tool calls create_ticket().
    """
    service = TicketService(db)
    try:
        ticket = await service.create_ticket(data)
        logger.info(f"Ticket created: {ticket.ticket_id}")
        return ticket
    except Exception as e:
        logger.exception(f"Error creating ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ticket: {str(e)}",
        )


@router.get(
    "/stats",
    summary="Get ticket statistics for admin dashboard",
    tags=["Admin"],
)
async def get_ticket_stats(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregate ticket statistics:
    - Total tickets, open, resolved, escalated counts.
    - Resolution rate percentage.
    
    Used by the IT Admin Dashboard in the Streamlit frontend.
    """
    service = TicketService(db)
    return await service.get_stats()


@router.get(
    "/search",
    response_model=list[TicketResponse],
    summary="Search historical incidents by keyword",
)
async def search_tickets(
    q: str = Query(..., min_length=3, description="Search query"),
    category: Optional[str] = Query(None, description="Restrict to category"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> list[TicketResponse]:
    """
    Search resolved historical tickets by keyword.
    
    Used by the AI agent to find past incident resolutions.
    Example: Search for "VPN Error 809" to find how previous VPN issues were solved.
    """
    service = TicketService(db)
    tickets = await service.search_similar_incidents(q, category=category, limit=limit)
    return tickets


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
    summary="Get a specific ticket by ID",
)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """
    Retrieve a single ticket by its ID (e.g., TKT-20240001).
    
    Returns 404 if the ticket does not exist.
    """
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )
    return ticket


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    summary="Update ticket status",
)
async def update_ticket_status(
    ticket_id: str,
    update: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """
    Update the status of a ticket.
    
    - **status**: open | in_progress | resolved | escalated | closed
    - **resolution**: Required notes when marking as resolved.
    
    Used by IT engineers to update ticket progress.
    """
    service = TicketService(db)
    ticket = await service.update_ticket_status(ticket_id, update)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )
    logger.info(f"Ticket {ticket_id} updated to status: {update.status}")
    return ticket
