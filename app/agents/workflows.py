# =============================================================
# NexaSupport AI — Realistic IT Support Workflows
# =============================================================
# PURPOSE:
#   Implements domain-tailored workflows for common IT issues:
#   1. VPN / Network Outage Workflow
#   2. Account Lockout & Access Approval Workflow
#   3. Software & Hardware Troubleshooting Workflow
#   4. Fallback Clarification & Escalation Workflow
# =============================================================

from typing import Dict, Any, List
from app.rag.retriever import RetrievedChunk


def format_vpn_workflow_response(
    service_status: Dict[str, Any],
    chunks: List[RetrievedChunk],
    similar_tickets: List[Dict[str, Any]],
) -> str:
    """Prepares structured VPN troubleshooting guidance."""
    vpn_status = service_status.get("services", {}).get("vpn", {})
    if vpn_status.get("status") in ["DEGRADED", "OUTAGE"]:
        return (
            "🚨 **Active Infrastructure Alert: Corporate VPN Gateway is currently experiencing an outage.**\n\n"
            f"- **Status**: {vpn_status.get('status')}\n"
            f"- **Details**: {vpn_status.get('active_incidents', 'IT Infrastructure team is actively investigating.')}\n\n"
            "**Recommended Action**: Please do not repeatedly attempt reconnection or reinstall clients. "
            "Our Network Engineering team has already received an alert and is working on restoration."
        )
    return None


def format_access_workflow_response(
    access_record: Dict[str, Any],
    query: str,
) -> str:
    """Prepares account status and permission guidance."""
    if not access_record.get("found"):
        return None

    if access_record.get("account_status") == "LOCKED_OUT":
        return (
            f"🔒 **Account Locked Out Detected for {access_record.get('employee_name')}**\n\n"
            "Our directory check indicates your Active Directory / SSO account has been locked due to excessive failed attempts.\n\n"
            "**Resolution Steps**:\n"
            "1. Visit the Self-Service Password Reset (SSPR) portal from your mobile browser: `https://sspr.company.com`\n"
            "2. Complete Multi-Factor Authentication via SMS / Microsoft Authenticator.\n"
            "3. If SSPR fails, reply below or use the 'Create Ticket' option to have an IT admin manually unlock your AD account."
        )

    requested_sys = access_record.get("requested_system")
    has_perm = access_record.get("has_permission")

    if requested_sys and not has_perm:
        return (
            f"⚠️ **Permission Required for {requested_sys}**\n\n"
            f"Employee **{access_record.get('employee_name')}** is currently active, but does not have provisioned access to **{requested_sys}**.\n\n"
            "**Approval Process**:\n"
            f"- Current assigned systems: {', '.join(access_record.get('assigned_systems', []))}\n"
            f"- To request access to {requested_sys}, an approval ticket with your manager's sign-off is required via the IT Access Portal."
        )
    return None
