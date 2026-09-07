# =============================================================
# NexaSupport AI — Conversation Memory & Query Reformulation
# =============================================================
# PURPOSE:
#   Maintains conversation context across turns.
#   Reformulates vague follow-up queries (e.g., "Yes, Error 809")
#   into standalone, searchable queries (e.g., "VPN Error 809 connection failure").
# =============================================================

from typing import List, Dict
from loguru import logger


def reformulate_query_with_context(
    query: str,
    conversation_history: List[Dict[str, str]],
) -> str:
    """
    Combines the current user message with prior turns if the query is a follow-up.
    
    Example:
      History: [User: "VPN not connecting", Assistant: "Do you see an error code?"]
      Current: "Yes, error 809"
      Output:  "VPN not connecting error 809"
    """
    if not conversation_history:
        return query.strip()

    # If the query is already self-contained and descriptive, keep it
    q_words = query.strip().split()
    if len(q_words) > 7 and not any(w in query.lower() for w in ["it", "this", "that", "again", "same", "yes", "no"]):
        return query.strip()

    # Extract key topics from the last user question
    last_user_msgs = [m["content"] for m in conversation_history if m.get("role") == "user"]
    if not last_user_msgs:
        return query.strip()

    last_user_query = last_user_msgs[-1]
    
    # Identify domain keywords to inherit
    domain_keywords = ["vpn", "outlook", "email", "wifi", "network", "password", "sap", "jira", "mac", "windows"]
    inherited_keywords = [kw for kw in domain_keywords if kw in last_user_query.lower()]

    if inherited_keywords and not any(kw in query.lower() for kw in inherited_keywords):
        reformulated = f"{' '.join(inherited_keywords)} {query.strip()}"
        logger.info(f"Context memory reformulation: '{query}' -> '{reformulated}'")
        return reformulated

    return query.strip()
