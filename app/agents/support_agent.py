# =============================================================
# NexaSupport AI — Agentic Support Orchestrator (Upgraded)
# =============================================================

import asyncio
import json
import time
from typing import Any, Dict, List, Optional
from loguru import logger

from app.config import settings
from app.rag.llm_client import get_llm_client
from app.rag.pipeline import SourceCitation, RAGResponse
from app.tools.it_tools import (
    tool_search_knowledge_base,
    tool_search_previous_tickets,
    tool_check_service_status,
    tool_check_user_access,
    KnowledgeSearchInput,
    TicketSearchInput,
    ServiceStatusInput,
    UserAccessInput,
)
from app.agents.guardrails import evaluate_response_confidence
from app.agents.workflows import (
    format_vpn_workflow_response,
    format_access_workflow_response,
)


class SupportAgent:
    """
    Intelligent IT Support Agent orchestrator with tool-augmented reasoning
    and multi-signal confidence guardrails.
    """

    def __init__(self):
        self.llm = get_llm_client()

    def _determine_intent_and_tools(self, query: str) -> Dict[str, Any]:
        """
        Deterministic + heuristic routing for tool selection.
        """
        q_lower = query.lower()
        tools_to_run = ["knowledge_base"]

        # Outage / Service status detection
        status_keywords = ["down", "outage", "status", "slow", "maintenance", "working", "issue today"]
        if any(k in q_lower for k in status_keywords):
            tools_to_run.append("service_status")

        # Previous ticket search detection (error codes, recurring problems)
        ticket_keywords = ["error", "code", "failed", "809", "crash", "stuck", "again", "fix"]
        if any(k in q_lower for k in ticket_keywords):
            tools_to_run.append("previous_tickets")

        # Access / permission inquiry detection
        access_keywords = ["access", "permission", "portal", "locked", "sap", "jira", "aws", "login failed", "password"]
        if any(k in q_lower for k in access_keywords):
            tools_to_run.append("user_access")

        return {"tools": list(set(tools_to_run))}

    async def execute_plan(
        self,
        query: str,
        employee_id: str = "EMP-1042",
        top_k: int = 4,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RAGResponse:
        """
        Execute tool-augmented resolution workflow with confidence guardrails.
        """
        start_time = time.time()
        routing = self._determine_intent_and_tools(query)
        selected_tools = routing["tools"]
        logger.info(f"SupportAgent triggered. Active tools: {selected_tools}")

        tasks = []
        task_names = []

        # 1. Knowledge Base
        if "knowledge_base" in selected_tools:
            tasks.append(tool_search_knowledge_base(KnowledgeSearchInput(query=query, top_k=top_k)))
            task_names.append("knowledge_base")

        # 2. Previous Tickets
        if "previous_tickets" in selected_tools:
            tasks.append(tool_search_previous_tickets(TicketSearchInput(query=query, limit=3)))
            task_names.append("previous_tickets")

        # 3. Live Service Status
        if "service_status" in selected_tools:
            service_target = None
            for s in ["vpn", "email", "wifi", "sso", "jira", "sap"]:
                if s in query.lower():
                    service_target = s
                    break
            tasks.append(tool_check_service_status(ServiceStatusInput(service_name=service_target)))
            task_names.append("service_status")

        # 4. User Access Check
        if "user_access" in selected_tools:
            target_sys = "VPN"
            for s in ["sap", "jira", "aws", "vpn", "hubspot"]:
                if s in query.lower():
                    target_sys = s.upper()
                    break
            tasks.append(tool_check_user_access(UserAccessInput(user_id=employee_id, system_name=target_sys)))
            task_names.append("user_access")

        # Concurrently execute tools
        tool_outputs = await asyncio.gather(*tasks, return_exceptions=True)
        results_map = {}
        for name, output in zip(task_names, tool_outputs):
            if isinstance(output, Exception):
                logger.error(f"Tool {name} encountered error: {output}")
                results_map[name] = {"error": str(output)}
            else:
                results_map[name] = output

        # ── Phase 10: Check Domain Workflows First ──────────────
        # Check Access Workflow (Lockout, Permissions)
        access_override = None
        if "user_access" in results_map and not results_map["user_access"].get("error"):
            access_override = format_access_workflow_response(results_map["user_access"], query)

        # Check VPN Outage Workflow
        vpn_override = None
        if "service_status" in results_map and not results_map["service_status"].get("error"):
            vpn_override = format_vpn_workflow_response(
                results_map["service_status"],
                [],
                results_map.get("previous_tickets", {}).get("incidents", []),
            )

        if vpn_override:
            elapsed = (time.time() - start_time) * 1000
            return RAGResponse(
                query=query,
                answer=vpn_override,
                sources=[],
                confidence=0.95,
                is_grounded=True,
                needs_escalation=False,
                llm_model="system-rule",
                retrieval_count=0,
                latency_ms=round(elapsed, 1),
            )

        if access_override:
            elapsed = (time.time() - start_time) * 1000
            return RAGResponse(
                query=query,
                answer=access_override,
                sources=[],
                confidence=0.92,
                is_grounded=True,
                needs_escalation=False,
                llm_model="system-rule",
                retrieval_count=0,
                latency_ms=round(elapsed, 1),
            )

        # Extract knowledge base citations
        sources: List[SourceCitation] = []
        kb_context_text = ""
        kb_data = results_map.get("knowledge_base", {})
        retrieved_raw_chunks = []
        if "documents" in kb_data:
            from app.rag.retriever import RetrievedChunk
            for idx, d in enumerate(kb_data["documents"]):
                sources.append(
                    SourceCitation(
                        citation_label=d["citation"],
                        title=d["title"],
                        source_file=d["source_file"],
                        chunk_index=0,
                        similarity_score=d["similarity"],
                    )
                )
                retrieved_raw_chunks.append(
                    RetrievedChunk(
                        text=d["content"],
                        source_file=d["source_file"],
                        title=d["title"],
                        chunk_index=0,
                        similarity_score=d["similarity"],
                    )
                )
                kb_context_text += f"\n[{d['citation']}] (From {d['title']}):\n{d['content']}\n"

        # Check historical tickets
        tickets_context = ""
        ticket_data = results_map.get("previous_tickets", {})
        has_ticket_match = False
        if "incidents" in ticket_data and ticket_data["incidents"]:
            has_ticket_match = True
            tickets_context += "\n--- SIMILAR HISTORICAL RESOLVED INCIDENTS ---\n"
            for t in ticket_data["incidents"]:
                tickets_context += (
                    f"Ticket: {t['ticket_id']} | Category: {t['category']} | Status: {t['status']}\n"
                    f"Summary: {t['summary']}\n"
                    f"Proven Resolution: {t['resolution']}\n\n"
                )

        # ── Phase 11: Multi-Signal Guardrail Evaluation ─────────
        guardrail_eval = evaluate_response_confidence(
            query=query,
            retrieved_chunks=retrieved_raw_chunks,
            has_outage=False,
            has_historical_match=has_ticket_match,
            has_user_access_data=bool(results_map.get("user_access", {}).get("found")),
        )

        # If completely ungrounded, refuse to hallucinate
        if guardrail_eval.score < 0.35 and not has_ticket_match:
            elapsed = (time.time() - start_time) * 1000
            refusal_msg = (
                "⚠️ **Unable to find reliable IT documentation for this issue.**\n\n"
                "To ensure your system is not misconfigured, I will not attempt to guess troubleshooting steps. "
                "Please submit an IT Support Ticket using the form below or contact the Service Desk directly."
            )
            return RAGResponse(
                query=query,
                answer=refusal_msg,
                sources=[],
                confidence=guardrail_eval.score,
                is_grounded=False,
                needs_escalation=True,
                llm_model=settings.GEMINI_MODEL,
                retrieval_count=0,
                latency_ms=round(elapsed, 1),
            )

        # Build Synthesis Prompt
        synthesis_prompt = f"""You are the NexaSupport AI Tier-1 IT Support Agent.
Provide a clear, step-by-step resolution to the employee's problem.

EMPLOYEE QUERY:
"{query}"

EVIDENCE GATHERED BY AGENT TOOLS:
1. OFFICIAL KNOWLEDGE BASE:
{kb_context_text if kb_context_text else "No specific documents found."}

2. PREVIOUS INCIDENTS & PAST RESOLUTIONS:
{tickets_context if tickets_context else "No matching historical tickets."}

INSTRUCTIONS:
- Directly answer the employee's issue using the gathered evidence.
- If historical tickets have solved this exact error code or issue, cite that proven resolution.
- Reference official knowledge base citations like [Source 1], [Source 2] where appropriate.
- If you don't have enough information, honestly state it and offer to escalate to an IT engineer.
- Be concise, structured (use bullet points/numbered steps), and professional.
"""

        try:
            llm_res = self.llm.generate(synthesis_prompt)
            answer = llm_res.text
            prompt_tokens = llm_res.prompt_tokens
            output_tokens = llm_res.output_tokens
        except Exception as e:
            logger.error(f"LLM synthesis failure: {e}")
            answer = (
                f"I investigated your issue across our knowledge base and incident history, "
                f"but encountered an error generating the final response. "
                f"Please escalate this to the IT Helpdesk."
            )
            prompt_tokens = 0
            output_tokens = 0

        elapsed = (time.time() - start_time) * 1000

        return RAGResponse(
            query=query,
            answer=answer,
            sources=sources,
            confidence=guardrail_eval.score,
            is_grounded=len(sources) > 0 or has_ticket_match,
            needs_escalation=not guardrail_eval.is_confident,
            llm_model=settings.GEMINI_MODEL,
            retrieval_count=len(sources),
            latency_ms=round(elapsed, 1),
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
        )


_agent_instance: Optional[SupportAgent] = None

def get_support_agent() -> SupportAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SupportAgent()
    return _agent_instance
