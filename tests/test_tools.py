# =============================================================
# NexaSupport AI — Tests: IT Tools Suite (Phase 14)
# =============================================================
# Tests cover:
#   1. tool_check_service_status — known, unknown, all services
#   2. tool_check_user_access — active, locked, unknown, no-permission
#   3. tool_create_ticket — via service layer (DB integration)
# =============================================================

import pytest
from datetime import datetime


# ── 1. Service Status Tool ──────────────────────────────────

@pytest.mark.asyncio
class TestToolCheckServiceStatus:
    """Tests for tool_check_service_status()."""

    async def test_known_service_vpn_returns_operational(self):
        from app.tools.it_tools import tool_check_service_status, ServiceStatusInput
        result = await tool_check_service_status(ServiceStatusInput(service_name="vpn"))
        assert result["tool"] == "check_service_status"
        assert "vpn" in result["services"]
        assert result["services"]["vpn"]["status"] == "OPERATIONAL"

    async def test_known_service_wifi_returns_degraded(self):
        from app.tools.it_tools import tool_check_service_status, ServiceStatusInput
        result = await tool_check_service_status(ServiceStatusInput(service_name="wifi"))
        assert result["services"]["wifi"]["status"] == "DEGRADED"

    async def test_known_service_sap_returns_maintenance(self):
        from app.tools.it_tools import tool_check_service_status, ServiceStatusInput
        result = await tool_check_service_status(ServiceStatusInput(service_name="sap"))
        assert result["services"]["sap"]["status"] == "MAINTENANCE"

    async def test_unknown_service_returns_unknown(self):
        from app.tools.it_tools import tool_check_service_status, ServiceStatusInput
        result = await tool_check_service_status(ServiceStatusInput(service_name="aws-s3"))
        # Should return UNKNOWN_SERVICE rather than raising
        services = result["services"]
        statuses = list(services.values())
        assert any(s.get("status") == "UNKNOWN_SERVICE" for s in statuses)

    async def test_all_services_returned_when_no_filter(self):
        from app.tools.it_tools import tool_check_service_status, ServiceStatusInput
        result = await tool_check_service_status(ServiceStatusInput(service_name=None))
        assert "vpn" in result["services"]
        assert "email" in result["services"]
        assert "sso" in result["services"]
        assert len(result["services"]) >= 5

    async def test_result_has_timestamp(self):
        from app.tools.it_tools import tool_check_service_status, ServiceStatusInput
        result = await tool_check_service_status(ServiceStatusInput(service_name="vpn"))
        assert "timestamp" in result
        # Should be a valid ISO timestamp
        datetime.fromisoformat(result["timestamp"])


# ── 2. User Access Tool ────────────────────────────────────

@pytest.mark.asyncio
class TestToolCheckUserAccess:
    """Tests for tool_check_user_access()."""

    async def test_known_active_user_returns_found(self):
        from app.tools.it_tools import tool_check_user_access, UserAccessInput
        result = await tool_check_user_access(UserAccessInput(user_id="EMP-1042", system_name="VPN"))
        assert result["found"] is True
        assert result["account_status"] == "ACTIVE"
        assert result["employee_name"] == "Alex Mercer"

    async def test_active_user_with_permission(self):
        from app.tools.it_tools import tool_check_user_access, UserAccessInput
        result = await tool_check_user_access(UserAccessInput(user_id="EMP-1042", system_name="Jira"))
        assert result["found"] is True
        assert result["has_permission"] is True

    async def test_active_user_without_permission_for_sap(self):
        from app.tools.it_tools import tool_check_user_access, UserAccessInput
        # EMP-1042 (Engineering) does not have SAP access
        result = await tool_check_user_access(UserAccessInput(user_id="EMP-1042", system_name="SAP"))
        assert result["found"] is True
        assert result["has_permission"] is False

    async def test_locked_out_user_detected(self):
        from app.tools.it_tools import tool_check_user_access, UserAccessInput
        result = await tool_check_user_access(UserAccessInput(user_id="EMP-2187", system_name="SAP"))
        assert result["found"] is True
        assert result["account_status"] == "LOCKED_OUT"

    async def test_unknown_user_returns_not_found(self):
        from app.tools.it_tools import tool_check_user_access, UserAccessInput
        result = await tool_check_user_access(UserAccessInput(user_id="EMP-9999", system_name="VPN"))
        assert result["found"] is False
        assert "not found" in result["message"].lower()

    async def test_case_insensitive_user_id_lookup(self):
        from app.tools.it_tools import tool_check_user_access, UserAccessInput
        # Tool normalises to uppercase internally
        result = await tool_check_user_access(UserAccessInput(user_id="emp-1042", system_name="VPN"))
        assert result["found"] is True


# ── 3. Ticket Creation Tool ────────────────────────────────

@pytest.mark.asyncio
class TestToolCreateTicket:
    """Tests for tool_create_ticket() — requires DB (uses SQLite in-memory for tests)."""

    async def test_create_ticket_returns_ticket_id(self):
        from app.tools.it_tools import tool_create_ticket, CreateTicketInput
        result = await tool_create_ticket(CreateTicketInput(
            user_id="EMP-1042",
            category="VPN",
            priority="high",
            summary="VPN Error 809 on Windows laptop",
            description="Repeatable error on every connection attempt.",
        ))
        assert result["success"] is True
        assert result["ticket_id"].startswith("TKT-")
        assert result["status"] == "open"

    async def test_create_ticket_with_defaults(self):
        from app.tools.it_tools import tool_create_ticket, CreateTicketInput
        result = await tool_create_ticket(CreateTicketInput(
            user_id="EMP-3041",
            category="Software",
            summary="Slack crashes on startup after macOS update",
        ))
        assert result["success"] is True
        assert result["ticket_id"].startswith("TKT-")
        # Default priority should be medium
        assert result["priority"] == "medium"

    async def test_create_ticket_has_created_at_timestamp(self):
        from app.tools.it_tools import tool_create_ticket, CreateTicketInput
        result = await tool_create_ticket(CreateTicketInput(
            user_id="EMP-1042",
            category="Network",
            summary="Office WiFi intermittent drops on 5GHz band",
        ))
        assert result["created_at"] is not None
        # Should be a valid ISO datetime
        datetime.fromisoformat(result["created_at"])


# ── 4. Workflow Responses ──────────────────────────────────

class TestWorkflowResponses:
    """Tests for workflow response formatters."""

    def test_vpn_outage_workflow_triggers_on_degraded(self):
        from app.agents.workflows import format_vpn_workflow_response
        service_status = {
            "services": {
                "vpn": {"status": "DEGRADED", "active_incidents": "Gateway packet loss"}
            }
        }
        response = format_vpn_workflow_response(service_status, [], [])
        assert response is not None
        assert "outage" in response.lower() or "alert" in response.lower()
        assert "DEGRADED" in response

    def test_vpn_workflow_returns_none_when_operational(self):
        from app.agents.workflows import format_vpn_workflow_response
        service_status = {
            "services": {"vpn": {"status": "OPERATIONAL", "active_incidents": "None"}}
        }
        response = format_vpn_workflow_response(service_status, [], [])
        assert response is None

    def test_access_workflow_detects_lockout(self):
        from app.agents.workflows import format_access_workflow_response
        access_record = {
            "found": True,
            "employee_name": "Priya Sharma",
            "account_status": "LOCKED_OUT",
            "requested_system": "SAP",
            "has_permission": True,
            "assigned_systems": ["VPN", "SAP"],
        }
        response = format_access_workflow_response(access_record, "I can't login to SAP")
        assert response is not None
        assert "locked" in response.lower()
        assert "Priya Sharma" in response

    def test_access_workflow_detects_no_permission(self):
        from app.agents.workflows import format_access_workflow_response
        access_record = {
            "found": True,
            "employee_name": "Alex Mercer",
            "account_status": "ACTIVE",
            "requested_system": "SAP",
            "has_permission": False,
            "assigned_systems": ["VPN", "Jira", "AWS-Dev"],
        }
        response = format_access_workflow_response(access_record, "Need SAP access")
        assert response is not None
        assert "SAP" in response
        assert "permission" in response.lower() or "access" in response.lower()

    def test_access_workflow_returns_none_when_not_found(self):
        from app.agents.workflows import format_access_workflow_response
        response = format_access_workflow_response({"found": False}, "some query")
        assert response is None
