# =============================================================
# NexaSupport AI — IT Tools Suite
# =============================================================
# PURPOSE:
#   Safe, structured tools available for the Agent to call.
#   Never executes raw arbitrary commands; every tool has validated
#   inputs, deterministic behavior, error handling, and logging.
# =============================================================

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

from app.rag.pipeline import get_rag_pipeline
from app.services.ticket_service import (
    create_ticket,
    search_tickets_fulltext,
    get_ticket_by_id,
)
from app.database.session import get_db_context


# ── Schemas for Tool Inputs & Outputs ──────────────────────────

class KnowledgeSearchInput(BaseModel):
    query: str = Field(..., description="The IT troubleshooting question or keywords to search in company documentation.")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of document chunks to retrieve.")


class TicketSearchInput(BaseModel):
    query: str = Field(..., description="Keywords to match in historical IT tickets (e.g. 'VPN 809', 'Outlook crash').")
    limit: int = Field(default=3, ge=1, le=10, description="Maximum historical tickets to return.")


class ServiceStatusInput(BaseModel):
    service_name: Optional[str] = Field(
        default=None,
        description="Specific service name to check: 'vpn', 'email', 'sso', 'wifi', 'jira', 'sap'. If empty, checks all.",
    )


class UserAccessInput(BaseModel):
    user_id: str = Field(..., description="Employee ID to check (e.g. 'EMP-1042').")
    system_name: str = Field(..., description="Name of the target system (e.g. 'SAP', 'AWS', 'Jira', 'VPN').")


class CreateTicketInput(BaseModel):
    user_id: str = Field(..., description="Employee ID of the requester.")
    category: str = Field(..., description="Incident category: 'VPN', 'Email', 'Password', 'Network', 'Software', 'Hardware', 'Access', 'Other'.")
    priority: str = Field(default="medium", description="Priority level: 'low', 'medium', 'high', 'critical'.")
    summary: str = Field(..., description="Brief summary of the issue.")
    description: Optional[str] = Field(default=None, description="Detailed troubleshooting notes or symptoms.")


# ── Mock Live IT Service Status Store ─────────────────────────

MOCK_SERVICE_STATUS = {
    "vpn": {"status": "OPERATIONAL", "uptime": "99.98%", "active_incidents": "None", "gateway": "gw-us-east.company.com"},
    "email": {"status": "OPERATIONAL", "uptime": "99.95%", "active_incidents": "None", "service": "Microsoft 365 Exchange"},
    "sso": {"status": "OPERATIONAL", "uptime": "100.0%", "active_incidents": "None", "provider": "Okta SSO"},
    "wifi": {"status": "DEGRADED", "uptime": "97.40%", "active_incidents": "Building B 3rd Floor AP-04 experiencing packet loss", "affected_locations": ["BLR-Campus-B"]},
    "jira": {"status": "OPERATIONAL", "uptime": "99.99%", "active_incidents": "None"},
    "sap": {"status": "MAINTENANCE", "uptime": "95.00%", "active_incidents": "Scheduled patch maintenance window until 14:00 IST"},
}

MOCK_USER_PERMISSIONS = {
    "EMP-1042": {"name": "Alex Mercer", "dept": "Engineering", "systems": ["VPN", "Jira", "AWS-Dev", "GitHub"], "status": "ACTIVE"},
    "EMP-2187": {"name": "Priya Sharma", "dept": "Finance", "systems": ["VPN", "SAP", "Excel-Cloud"], "status": "LOCKED_OUT"},
    "EMP-3041": {"name": "David Miller", "dept": "Marketing", "systems": ["VPN", "HubSpot", "Slack"], "status": "ACTIVE"},
}


# ── Tools Implementation ──────────────────────────────────────

async def tool_search_knowledge_base(params: KnowledgeSearchInput) -> Dict[str, Any]:
    """Search the internal IT knowledge base (ChromaDB vector store) via RAG pipeline."""
    logger.info(f"[Tool: search_knowledge_base] Query: '{params.query}'")
    pipeline = get_rag_pipeline()
    chunks = pipeline._retriever.retrieve(query=params.query, top_k=params.top_k)

    results = []
    for idx, c in enumerate(chunks):
        results.append({
            "citation": f"Source {idx + 1}",
            "title": c.title,
            "source_file": c.source_file,
            "similarity": round(c.similarity_score, 3),
            "content": c.text,
        })
    return {
        "tool": "search_knowledge_base",
        "results_count": len(results),
        "documents": results,
    }


async def tool_search_previous_tickets(params: TicketSearchInput) -> Dict[str, Any]:
    """Search previous solved IT tickets in the relational database."""
    logger.info(f"[Tool: search_previous_tickets] Query: '{params.query}'")
    async with get_db_context() as session:
        tickets = await search_tickets_fulltext(session, query=params.query, limit=params.limit)

    results = []
    for t in tickets:
        results.append({
            "ticket_id": t.ticket_id,
            "category": t.category,
            "summary": t.summary,
            "resolution": t.resolution or "In progress / Pending",
            "status": t.status,
        })
    return {
        "tool": "search_previous_tickets",
        "matches_count": len(results),
        "incidents": results,
    }


async def tool_check_service_status(params: ServiceStatusInput) -> Dict[str, Any]:
    """Check the real-time operational status of corporate IT infrastructure."""
    logger.info(f"[Tool: check_service_status] Target: {params.service_name or 'ALL'}")
    if params.service_name:
        key = params.service_name.lower().strip()
        matched = {k: v for k, v in MOCK_SERVICE_STATUS.items() if key in k}
        return {
            "tool": "check_service_status",
            "timestamp": datetime.utcnow().isoformat(),
            "services": matched if matched else {key: {"status": "UNKNOWN_SERVICE"}},
        }
    return {
        "tool": "check_service_status",
        "timestamp": datetime.utcnow().isoformat(),
        "services": MOCK_SERVICE_STATUS,
    }


async def tool_check_user_access(params: UserAccessInput) -> Dict[str, Any]:
    """Verify an employee's access status and assigned system permissions."""
    logger.info(f"[Tool: check_user_access] User: {params.user_id}, Target: {params.system_name}")
    user_record = MOCK_USER_PERMISSIONS.get(params.user_id.upper())
    if not user_record:
        return {
            "tool": "check_user_access",
            "found": False,
            "message": f"Employee ID '{params.user_id}' not found in Active Directory.",
        }

    has_permission = any(params.system_name.lower() in sys.lower() for sys in user_record["systems"])
    return {
        "tool": "check_user_access",
        "found": True,
        "employee_name": user_record["name"],
        "account_status": user_record["status"],
        "requested_system": params.system_name,
        "has_permission": has_permission,
        "assigned_systems": user_record["systems"],
    }


async def tool_create_ticket(params: CreateTicketInput) -> Dict[str, Any]:
    """Create a new IT incident/service ticket in the database."""
    logger.info(f"[Tool: create_ticket] User: {params.user_id}, Category: {params.category}")
    async with get_db_context() as session:
        ticket = await create_ticket(
            session=session,
            user_id=params.user_id,
            category=params.category,
            priority=params.priority,
            summary=params.summary,
            description=params.description,
        )
    return {
        "tool": "create_ticket",
        "success": True,
        "ticket_id": ticket.ticket_id,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    }
