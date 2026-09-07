# =============================================================
# NexaSupport AI — Agentic Support Orchestrator
# =============================================================
# PURPOSE:
#   Orchestrates intelligent reasoning and tool calling.
#   1. Analyzes user query intent (Troubleshooting, Status check, Access inquiry, Escalation).
#   2. Determines required tools:
#      - Knowledge Base (RAG chunks)
#      - Past incident resolutions
#      - Live system health (outage checking)
#      - Permission / Account check
#   3. Executes selected tools concurrently.
#   4. Synthesizes a structured, grounded answer with source attribution
#      and confidence scoring.
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


class SupportAgent:
    """
    Intelligent IT Support Agent orchestrator with tool-augmented reasoning.
    """

    def __init__(self):
        self.llm = get_llm_client()

    def _determine_intent_and_tools(self, query: str) -> Dict[str, Any]:
        """
        Deterministic + heuristic routing for tool selection.
        Enables lightning-fast decisions without unnecessary LLM hops when obvious,
        while maintaining multi-tool invocation capability.
        """
        q_lower = query.lower()
        tools_to_run = ["knowledge_base"]  # Always search knowledge base by default

        # Outage / Service status detection
        status_keywords = ["down", "outage", "status", "slow", "maintenance", "working", "issue today"]
        if any(k in q_lower for k in status_keywords):
            tools_to_run.append("service_status")

        # Previous ticket search detection (error codes, recurring problems)
        ticket_keywords = ["error", "code", "failed", "809", "crash", "stuck", "again", "fix"]
        if any(k in q_lower for k in ticket_keywords):
            tools_to_run.append("previous_tickets")

        # Access / permission inquiry detection
        access_keywords = ["access", "permission", "portal", "locked", "sap", "jira", "aws", "login failed"]
        if any(k in q_lower for k in access_keywords):
            tools_to_run.append("user_access")

        return {
            "tools": list(set(tools_to_run))
        }

    async def execute_plan(
        self,
        query: str,
        employee_id: str = "EMP-1042",
        top_k: int = 4,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> RAGResponse:
        """
        Execute tool-augmented resolution workflow.
        """
        start_time = time.time()
        routing = self._determine_intent_and_tools(query)
        selected_tools = routing["tools"]
        logger.info(f"SupportAgent triggered. Active tools for query: {selected_tools}")

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
            # Extract possible service name
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

        # Extract knowledge base citations
        sources: List[SourceCitation] = []
        kb_context_text = ""
        kb_data = results_map.get("knowledge_base", {})
        if "documents" in kb_data:
            for d in kb_data["documents"]:
                sources.append(
                    SourceCitation(
                        citation_label=d["citation"],
                        title=d["title"],
                        source_file=d["source_file"],
                        chunk_index=0,
                        similarity_score=d["similarity"],
                    )
                )
                kb_context_text += f"\n[{d['citation']}] (From {d['title']}):\n{d['content']}\n"

        # Format historical incidents context
        tickets_context = ""
        ticket_data = results_map.get("previous_tickets", {})
        if "incidents" in ticket_data and ticket_data["incidents"]:
            tickets_context += "\n--- SIMILAR HISTORICAL RESOLVED INCIDENTS ---\n"
            for t in ticket_data["incidents"]:
                tickets_context += (
                    f"Ticket: {t['ticket_id']} | Category: {t['category']} | Status: {t['status']}\n"
                    f"Summary: {t['summary']}\n"
                    f"Proven Resolution: {t['resolution']}\n\n"
                )

        # Format service status context
        status_context = ""
        status_data = results_map.get("service_status", {})
        if "services" in status_data:
            status_context += f"\n--- LIVE SERVICE STATUS ---\n{json.dumps(status_data['services'], indent=2)}\n"

        # Format user permission context
        access_context = ""
        access_data = results_map.get("user_access", {})
        if access_data and not access_data.get("error"):
            access_context += f"\n--- USER ACCESS STATUS ({employee_id}) ---\n{json.dumps(access_data, indent=2)}\n"

        # Build Synthesis Prompt
        synthesis_prompt = f"""You are the NexaSupport AI Tier-1 IT Support Agent.
Your goal is to provide a clear, step-by-step resolution to the employee's problem.

EMPLOYEE QUERY:
"{query}"

EVIDENCE GATHERED BY AGENT TOOLS:
1. OFFICIAL KNOWLEDGE BASE:
{kb_context_text if kb_context_text else "No specific documents found."}

2. SYSTEM HEALTH & OUTAGE CHECKS:
{status_context if status_context else "No active outages reported."}

3. PREVIOUS INCIDENTS & PAST RESOLUTIONS:
{tickets_context if tickets_context else "No matching historical tickets."}

4. USER PERMISSION RECORD:
{access_context if access_context else "Standard access."}

INSTRUCTIONS:
- Directly answer the employee's issue using the gathered evidence.
- If a relevant service is degraded or in maintenance (e.g. WiFi or SAP), inform them immediately.
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

        # Calculate confidence
        confidence = 0.5
        if sources:
            confidence = max([s.similarity_score for s in sources])
            if results_map.get("previous_tickets", {}).get("matches_count", 0) > 0:
                confidence = min(1.0, confidence + 0.1)
        elif status_context or access_context:
            confidence = 0.85

        needs_escalation = confidence < settings.CONFIDENCE_THRESHOLD
        elapsed = (time.time() - start_time) * 1000

        return RAGResponse(
            query=query,
            answer=answer,
            sources=sources,
            confidence=round(confidence, 2),
            is_grounded=len(sources) > 0 or bool(tickets_context),
            needs_escalation=needs_escalation,
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
