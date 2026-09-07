# =============================================================
# NexaSupport AI — Tests: SupportAgent (Phase 14)
# =============================================================
# Tests cover:
#   1. Intent detection / tool routing heuristics
#   2. Guardrail refusal when confidence < threshold
#   3. Memory-driven query reformulation (multi-turn context)
#   4. Auto-ticket creation on escalation (mocked DB)
# =============================================================

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── 1. Intent / Tool Routing ────────────────────────────────

class TestIntentRouting:
    """Tests for _determine_intent_and_tools() heuristics."""

    def _get_agent(self):
        """Create a SupportAgent without triggering LLM client init."""
        with patch("app.agents.support_agent.get_llm_client"):
            from app.agents.support_agent import SupportAgent
            return SupportAgent()

    def test_always_includes_knowledge_base(self):
        agent = self._get_agent()
        result = agent._determine_intent_and_tools("How do I set up my work email on Outlook?")
        assert "knowledge_base" in result["tools"]

    def test_detects_service_status_for_outage_keywords(self):
        agent = self._get_agent()
        for keyword in ["down", "outage", "slow", "maintenance", "issue today"]:
            result = agent._determine_intent_and_tools(f"Is the VPN {keyword}?")
            assert "service_status" in result["tools"], f"Expected service_status for keyword '{keyword}'"

    def test_detects_previous_tickets_for_error_codes(self):
        agent = self._get_agent()
        for keyword in ["error", "809", "crash", "failed", "fix"]:
            result = agent._determine_intent_and_tools(f"My VPN shows {keyword}")
            assert "previous_tickets" in result["tools"], f"Expected previous_tickets for keyword '{keyword}'"

    def test_detects_user_access_for_permission_keywords(self):
        agent = self._get_agent()
        for keyword in ["access", "permission", "locked", "sap", "jira", "aws", "password"]:
            result = agent._determine_intent_and_tools(f"I need {keyword} help")
            assert "user_access" in result["tools"], f"Expected user_access for keyword '{keyword}'"

    def test_multiple_tools_for_complex_query(self):
        agent = self._get_agent()
        result = agent._determine_intent_and_tools(
            "My SAP access is locked and the system shows error 403 — is there an outage?"
        )
        tools = result["tools"]
        assert "knowledge_base" in tools
        assert "service_status" in tools
        assert "user_access" in tools
        assert "previous_tickets" in tools

    def test_generic_query_only_uses_knowledge_base(self):
        agent = self._get_agent()
        result = agent._determine_intent_and_tools("How do I set up the company printer?")
        # Should not trigger status/ticket/access tools for a clean generic query
        assert "knowledge_base" in result["tools"]
        assert "service_status" not in result["tools"]


# ── 2. Guardrails ───────────────────────────────────────────

class TestGuardrails:
    """Tests for evaluate_response_confidence()."""

    def test_zero_chunks_returns_zero_confidence(self):
        from app.agents.guardrails import evaluate_response_confidence
        result = evaluate_response_confidence(
            query="Completely unrelated random query",
            retrieved_chunks=[],
            has_outage=False,
            has_historical_match=False,
            has_user_access_data=False,
        )
        assert result.score == 0.0
        assert result.is_confident is False

    def test_high_similarity_chunk_returns_confident(self):
        from app.agents.guardrails import evaluate_response_confidence
        from app.rag.retriever import RetrievedChunk

        mock_chunk = RetrievedChunk(
            text="VPN Error 809 fix: check firewall settings.",
            source_file="vpn_guide.md",
            title="VPN Troubleshooting Guide",
            chunk_index=0,
            similarity_score=0.85,
        )
        result = evaluate_response_confidence(
            query="VPN Error 809",
            retrieved_chunks=[mock_chunk, mock_chunk],
            has_outage=False,
            has_historical_match=False,
            has_user_access_data=False,
        )
        assert result.score > 0.70
        assert result.is_confident is True

    def test_ticket_match_bonus_raises_confidence(self):
        from app.agents.guardrails import evaluate_response_confidence
        from app.rag.retriever import RetrievedChunk

        low_chunk = RetrievedChunk(
            text="Maybe try restarting.",
            source_file="general.md",
            title="General Tips",
            chunk_index=0,
            similarity_score=0.45,
        )
        result = evaluate_response_confidence(
            query="VPN slow",
            retrieved_chunks=[low_chunk],
            has_outage=False,
            has_historical_match=True,  # Historical match should add 0.10
            has_user_access_data=False,
        )
        # With ticket match bonus, should be 0.45 * 0.7 + 0.10 = 0.415
        assert result.score > 0.40

    def test_outage_bonus_raises_confidence(self):
        from app.agents.guardrails import evaluate_response_confidence

        result = evaluate_response_confidence(
            query="Email is down",
            retrieved_chunks=[],
            has_outage=True,   # +0.20 bonus
            has_historical_match=False,
            has_user_access_data=False,
        )
        assert result.score >= 0.20


# ── 3. Memory / Query Reformulation ────────────────────────

class TestMemoryReformulation:
    """Tests for reformulate_query_with_context()."""

    def test_standalone_query_unchanged(self):
        from app.agents.memory import reformulate_query_with_context
        query = "How do I reset my Okta password from my mobile phone?"
        result = reformulate_query_with_context(query, [])
        assert result == query.strip()

    def test_empty_history_returns_original(self):
        from app.agents.memory import reformulate_query_with_context
        result = reformulate_query_with_context("Yes", [])
        assert result == "Yes"

    def test_follow_up_inherits_vpn_context(self):
        from app.agents.memory import reformulate_query_with_context
        history = [
            {"role": "user", "content": "My VPN is not connecting, what should I do?"},
            {"role": "assistant", "content": "Please check if you see an error code."},
        ]
        result = reformulate_query_with_context("Yes, error 809", history)
        assert "vpn" in result.lower()
        assert "809" in result

    def test_follow_up_inherits_email_context(self):
        from app.agents.memory import reformulate_query_with_context
        history = [
            {"role": "user", "content": "Outlook email keeps crashing on startup"},
        ]
        result = reformulate_query_with_context("It still happens", history)
        assert "outlook" in result.lower() or "email" in result.lower()

    def test_long_descriptive_query_is_not_reformulated(self):
        from app.agents.memory import reformulate_query_with_context
        history = [
            {"role": "user", "content": "VPN disconnects randomly"},
        ]
        long_query = "My laptop battery drains very fast and performance is degraded"
        result = reformulate_query_with_context(long_query, history)
        # More than 7 words, no follow-up indicators → should not inherit VPN context
        assert result == long_query.strip()


# ── 4. Category Inference ───────────────────────────────────

class TestCategoryInference:
    """Tests for _infer_category() helper."""

    def test_vpn_category(self):
        from app.agents.support_agent import _infer_category
        assert _infer_category("My VPN keeps disconnecting") == "VPN"
        assert _infer_category("Cisco AnyConnect error") == "VPN"

    def test_email_category(self):
        from app.agents.support_agent import _infer_category
        assert _infer_category("Outlook not syncing emails") == "Email"

    def test_password_category(self):
        from app.agents.support_agent import _infer_category
        assert _infer_category("I forgot my SSO password") == "Password"
        assert _infer_category("MFA authenticator not working") == "Password"

    def test_access_category(self):
        from app.agents.support_agent import _infer_category
        assert _infer_category("Need access to SAP portal") == "Access"

    def test_hardware_category(self):
        from app.agents.support_agent import _infer_category
        assert _infer_category("Printer not found on network") == "Hardware"

    def test_software_category(self):
        from app.agents.support_agent import _infer_category
        assert _infer_category("App crashes after the latest update") == "Software"

    def test_other_category_fallback(self):
        from app.agents.support_agent import _infer_category
        assert _infer_category("Random unrecognised query about something else") == "Other"
