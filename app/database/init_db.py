# =============================================================
# NexaSupport AI — Database Initialization & Seed Data
# =============================================================
# PURPOSE:
#   Creates all database tables and seeds the database with
#   20 realistic synthetic past IT incidents.
#
# WHY SEED DATA?
#   We need historical tickets to demonstrate the "search previous
#   incidents" feature of the AI agent. Real-world IT support
#   systems have hundreds of past tickets — seeded data simulates
#   that so the system works without a live production database.
#
# HOW TO RUN:
#   Called automatically on startup from main.py.
#   Can also be run manually: python -c "import asyncio; from app.database.init_db import run_init; asyncio.run(run_init())"
# =============================================================

from datetime import datetime, timedelta
import random
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Base, Ticket
from app.database.session import engine, get_db_context


def _generate_ticket_id(index: int, created_at: datetime) -> str:
    """Generate a realistic ticket ID like TKT-20240001."""
    return f"TKT-{created_at.year}{index:04d}"


# ── Synthetic Seed Data ─────────────────────────────────────────────────────────
# 20 realistic historical IT support tickets covering the main categories.
# Format: (user_id, category, priority, status, summary, description, resolution, days_ago, resolved_days_after)

SEED_TICKETS = [
    (
        "EMP-1042", "VPN", "high", "resolved",
        "VPN Error 809: Cannot connect from home network",
        "Employee working from home cannot establish VPN connection. Error 809 appears immediately after entering credentials. Tried restarting the client. ISP is Jio Fiber.",
        "Changed VPN tunnel protocol from IPSec to SSL in GlobalProtect settings. Jio Fiber blocks UDP port 4500. SSL tunnel resolved the issue.",
        30, 1,
    ),
    (
        "EMP-2187", "Password", "high", "resolved",
        "Account locked out after password reset attempt",
        "Employee forgot password, attempted to reset via SSPR portal but entered wrong answers 5 times. Account is now locked.",
        "IT unlocked the AD account via Active Directory Users and Computers. Employee successfully completed SSPR verification via SMS and set new password.",
        28, 0,
    ),
    (
        "EMP-0934", "Email", "medium", "resolved",
        "Outlook stuck on 'Loading Profile' — cannot open email",
        "Outlook 365 does not open. It shows 'Loading Profile' spinner and freezes. Started happening after Windows Update KB5034441 installed last night.",
        "Ran outlook.exe /resetnavpane which cleared corrupt navigation pane data. Outlook opened normally. Identified as a known issue with that KB update.",
        25, 1,
    ),
    (
        "EMP-3301", "Access", "medium", "resolved",
        "Cannot access HR portal — AADSTS50105 error",
        "New employee joined last week. Cannot log into Workday HR portal. Gets AADSTS50105 error code. Manager confirmed access should have been provisioned.",
        "User was not added to the 'Workday-Users' Azure AD security group during onboarding. Added to group. Access restored within 15 minutes.",
        22, 0,
    ),
    (
        "EMP-1567", "Network", "high", "resolved",
        "Connected to ACME-CORP Wi-Fi but cannot reach internal applications",
        "Laptop shows connected to ACME-CORP but SharePoint, JIRA, and all internal apps are unreachable. Browser shows DNS_PROBE_FINISHED_NXDOMAIN. Internet sites work fine.",
        "DNS server was incorrectly set to 8.8.8.8 (Google) instead of 10.0.0.10 (internal). Reset DNS via ipconfig /flushdns and set correct DNS. Internal DNS resolved immediately.",
        20, 0,
    ),
    (
        "EMP-4422", "Software", "medium", "resolved",
        "Microsoft 365 showing 'Subscription expired' on work laptop",
        "Word, Excel, and Outlook are all showing 'Subscription expired — activate product'. Employee is a full-time employee with a valid M365 E3 license.",
        "Employee's M365 license had been incorrectly deactivated during a license cleanup audit. Re-assigned E3 license via Microsoft Admin Center. Apps activated within 30 minutes.",
        18, 0,
    ),
    (
        "EMP-0011", "Hardware", "high", "resolved",
        "Laptop display cracked — unable to work",
        "Laptop screen cracked after accidental fall. External monitor working as workaround but employee cannot work mobile. Needs replacement.",
        "Issued Dell loaner laptop same day. Original laptop sent to hardware repair. Under 3-year warranty — no cost to employee. Repair took 5 business days.",
        15, 5,
    ),
    (
        "EMP-2903", "VPN", "medium", "resolved",
        "VPN connects successfully but shared drives not accessible",
        "VPN shows green connected status in GlobalProtect. Can reach internal websites. But F: and G: drives show 'Network path not found'. Running on Windows 11.",
        "Split tunnel routing issue. Network drives use SMB over port 445 which was being sent through split tunnel. IT added \\\\fileserver.internal.acmecorp.com to full-tunnel routes. Drives accessible after VPN reconnect.",
        14, 1,
    ),
    (
        "EMP-5514", "Email", "low", "resolved",
        "Emails stuck in Outbox — not sending",
        "Employee has 3 emails in Outbox for 2 days. Status shows 'Sending'. Outlook is online (not offline mode).",
        "One of the stuck emails had a 38 MB attachment exceeding the 25 MB limit. Deleted the large attachment from Outbox. Employee re-sent via SharePoint link. Other two emails sent immediately after.",
        12, 0,
    ),
    (
        "EMP-6677", "Password", "medium", "resolved",
        "MFA code always invalid when logging in from new phone",
        "Employee got a new iPhone and reinstalled Microsoft Authenticator. MFA codes generated by the app are rejected every time.",
        "New phone's clock was off by 3 minutes due to incorrect timezone setting. TOTP codes are time-based; even 30-second drift causes failure. Set phone to automatic time. Codes started working immediately.",
        10, 0,
    ),
    (
        "EMP-1830", "Access", "medium", "resolved",
        "Cannot access JIRA project board — permission denied",
        "Employee transferred from Engineering to Product team. Can log into JIRA via SSO but gets 'Permission denied' when trying to access PROJ-MOBILE board.",
        "Employee's JIRA user was in 'Engineering-Users' group but not 'Product-Users' group. JIRA project permissions are role-based. Added to Product-Users group. Access granted.",
        9, 0,
    ),
    (
        "EMP-7788", "Network", "medium", "resolved",
        "Cannot print to floor printer — shows offline",
        "Printer on Floor 4 showing offline status on this employee's laptop only. Other employees on same floor can print fine.",
        "Printer driver had become corrupted. Removed and reinstalled printer using Add a printer wizard with the floor printer's IP (10.4.0.50). Print queue cleared. Printing restored.",
        7, 0,
    ),
    (
        "EMP-3390", "Software", "low", "resolved",
        "Python not found in PATH after installation from Company Portal",
        "Installed Python 3.11 from Company Portal successfully. But running 'python' in Command Prompt gives 'command not recognized'.",
        "Python installer via Intune does not add to PATH for all users by default. Added Python path manually: C:\\Program Files\\Python311\\ and C:\\Program Files\\Python311\\Scripts\\ to System Environment Variables. Verified with python --version.",
        6, 0,
    ),
    (
        "EMP-9901", "Email", "medium", "resolved",
        "Cannot receive external emails — mailbox showing full",
        "Employee reports not receiving emails from external senders for 3 days. Mailbox shows 49.8 GB used out of 50 GB quota.",
        "Mailbox was 99.6% full causing send/receive block. Archived emails older than 1 year to local PST file (freed 12 GB). Emptied Deleted Items and Junk. Email reception restored within 5 minutes.",
        5, 0,
    ),
    (
        "EMP-4401", "VPN", "critical", "escalated",
        "All remote employees in Bangalore office cannot connect to VPN",
        "Multiple employees report VPN failure simultaneously starting 9 AM IST. Error: 'VPN gateway not responding'. VPN gateway status page shows Degraded.",
        "Escalated to Infrastructure team. VPN gateway certificate expired unexpectedly. Certificate renewed by Infrastructure team. All connections restored by 11:30 AM IST. 18 employees impacted for 2.5 hours.",
        4, 0,
    ),
    (
        "EMP-2256", "Access", "high", "resolved",
        "AWS console access denied after role change",
        "Employee promoted from Junior to Senior Engineer role. AWS console shows 'AccessDenied' for S3, EC2, and Lambda. Previous Junior role had restricted access.",
        "IAM permissions for SeniorEngineer role in AWS were not updated to include S3 and EC2 write permissions. Cloud team updated the SeniorEngineer IAM policy. Employee tested and confirmed access.",
        3, 1,
    ),
    (
        "EMP-5523", "Hardware", "medium", "open",
        "Docking station not detecting external monitors",
        "Dell WD22TB4 docking station connected via Thunderbolt 4. Laptop charges via dock but neither external monitor shows signal. Monitors work when connected directly to laptop HDMI.",
        None,  # Unresolved — open ticket
        2, None,
    ),
    (
        "EMP-8834", "Software", "low", "open",
        "VS Code extensions not installing — proxy error",
        "VS Code shows 'XHR failed' when trying to install extensions from the marketplace. Network connection is fine. Browser works normally.",
        None,  # Unresolved — open
        1, None,
    ),
    (
        "EMP-0098", "Password", "high", "resolved",
        "Cannot complete MFA — lost access to phone number and authenticator app",
        "Employee phone was stolen. Has no access to registered mobile number, authenticator app, or backup email (which was also on the stolen phone).",
        "Employee verified identity in person at IT desk (Employee ID + government ID). IT Security reset MFA registration. Employee set up new authenticator on new phone. Account secured.",
        1, 0,
    ),
    (
        "EMP-6612", "Network", "medium", "in_progress",
        "Wi-Fi drops every 20 minutes on Floor 2, Building B",
        "Multiple employees on Floor 2 Building B reporting intermittent Wi-Fi drops since Monday. Drops last ~2 minutes and reconnect automatically. ACME-CORP SSID on 2.4 GHz seems most affected.",
        None,  # In progress
        0, None,
    ),
]


async def create_tables() -> None:
    """
    Create all database tables defined in models.py.
    Safe to call multiple times — only creates tables that don't exist yet.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created/verified")


async def seed_tickets(db: AsyncSession) -> int:
    """
    Seed the database with synthetic historical IT tickets.
    Skips seeding if tickets already exist (idempotent).
    
    Returns:
        Number of tickets seeded (0 if already seeded).
    """
    # Check if already seeded
    result = await db.execute(text("SELECT COUNT(*) FROM tickets"))
    count = result.scalar()
    if count > 0:
        logger.info(f"Database already has {count} ticket(s). Skipping seed.")
        return 0

    logger.info("Seeding database with synthetic historical tickets...")
    now = datetime.utcnow()
    seeded = 0

    for i, ticket_data in enumerate(SEED_TICKETS, start=1):
        (user_id, category, priority, status,
         summary, description, resolution,
         days_ago, resolved_days_after) = ticket_data

        created_at = now - timedelta(days=days_ago)
        resolved_at = None
        if resolved_days_after is not None and status == "resolved":
            resolved_at = created_at + timedelta(days=resolved_days_after)
        elif resolved_days_after is not None and status == "escalated":
            resolved_at = created_at + timedelta(days=resolved_days_after)

        ticket = Ticket(
            ticket_id=_generate_ticket_id(i, created_at),
            user_id=user_id,
            category=category,
            priority=priority,
            status=status,
            summary=summary,
            description=description,
            resolution=resolution,
            is_escalated=(status == "escalated"),
            created_at=created_at,
            updated_at=now if status in ("open", "in_progress") else (resolved_at or created_at),
            resolved_at=resolved_at,
            ai_confidence=round(random.uniform(0.35, 0.95), 2),
        )
        db.add(ticket)
        seeded += 1

    await db.commit()
    logger.info(f"✅ Seeded {seeded} historical tickets into the database")
    return seeded


async def run_init() -> None:
    """
    Full database initialization: create tables + seed data.
    Called on FastAPI startup.
    """
    await create_tables()
    async with get_db_context() as db:
        await seed_tickets(db)
