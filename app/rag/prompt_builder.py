# =============================================================
# NexaSupport AI — Prompt Builder
# =============================================================
# PURPOSE:
#   Constructs the final prompt that is sent to the LLM.
#   Combines the user's question with retrieved context chunks.
#
# CONCEPT — Why a separate prompt builder?
#   The prompt is the most important part of a RAG system.
#   It:
#     1. Instructs the LLM to ONLY answer from provided context.
#     2. Shows the retrieved chunks as numbered context sections.
#     3. Adds citation instructions so the LLM references sources.
#     4. Adds guardrails: "If you don't know, say so — don't guess."
#   Separating this into its own module makes it easy to:
#     - Experiment with different prompt templates.
#     - Add conversation history in a later phase.
#     - Test prompt quality independently.
#
# KEY DESIGN DECISION — Grounding vs. Hallucination:
#   Without explicit instructions, LLMs will answer from their training
#   data even if no relevant context is provided. Our prompt explicitly
#   tells the model: "Your ONLY knowledge source is the context below."
# =============================================================

from app.rag.retriever import RetrievedChunk


# ── System Prompt ──────────────────────────────────────────────────────────────
# This is the core instruction set for the LLM.
# It defines the AI's role, rules, and expected output format.

SYSTEM_PROMPT = """You are NexaSupport AI, an intelligent IT support assistant for Acme Corp.

## Your Role
You help employees resolve IT issues quickly and accurately. You are helpful, professional, and concise.

## Critical Rules
1. **Context-Only Answers**: Answer ONLY using the information provided in the CONTEXT SECTIONS below. 
   Do NOT use any knowledge from your training data about the outside world.
2. **Honest Uncertainty**: If the provided context does not contain enough information to answer the question, 
   say exactly: "I don't have enough information in the knowledge base to answer this question confidently."
   Then suggest the employee contacts IT Helpdesk at it-helpdesk@acmecorp.com.
3. **No Hallucination**: Never invent error codes, file paths, server names, IP addresses, phone numbers, 
   or steps that are not explicitly mentioned in the context.
4. **Source Citations**: When you use information from the context, cite the source using [Source N] notation.
5. **Structured Responses**: Format your answers clearly. Use numbered steps for procedures.
   Use bullet points for lists. Use bold for important warnings.
6. **Escalation Awareness**: If the context suggests the issue is complex, or if the employee has 
   already tried the documented steps, recommend creating a support ticket.

## Tone
- Professional but friendly.
- Concise: get to the resolution quickly.
- If steps are needed, number them clearly.
- Acknowledge the frustration of IT problems without being dismissive.
"""


def build_rag_prompt(
    query: str,
    retrieved_chunks: list[RetrievedChunk],
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Build the full grounded prompt to send to the LLM.

    Args:
        query              : The user's current IT support question.
        retrieved_chunks   : Relevant chunks retrieved from ChromaDB.
        conversation_history: Optional list of prior turns.
                              Format: [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        A complete prompt string ready to be sent to the LLM.

    Prompt structure:
        [System instructions]
        [Conversation history (if any)]
        [Numbered context sections]
        [Employee Question]
        [Response instructions]
    """
    sections = []

    # ── 1. System instructions ─────────────────────────────────
    sections.append(SYSTEM_PROMPT)

    # ── 2. Conversation history (Phase 12 — memory) ───────────
    # Even now, we include the parameter so the pipeline signature is stable.
    if conversation_history:
        history_text = "\n## Conversation History\n"
        for turn in conversation_history[-6:]:  # Limit to last 6 turns to control token usage
            role = "Employee" if turn["role"] == "user" else "NexaSupport AI"
            history_text += f"\n**{role}:** {turn['content']}\n"
        sections.append(history_text)

    # ── 3. Context sections ────────────────────────────────────
    if retrieved_chunks:
        context_text = "\n## Knowledge Base Context\n"
        context_text += (
            "The following sections are retrieved from Acme Corp's IT knowledge base. "
            "Use ONLY this information to answer the employee's question.\n"
        )
        for i, chunk in enumerate(retrieved_chunks, start=1):
            context_text += (
                f"\n---\n"
                f"**[Source {i}]** {chunk.citation}\n"
                f"Relevance Score: {chunk.similarity_score:.2f}\n\n"
                f"{chunk.text}\n"
            )
        sections.append(context_text)
    else:
        # No relevant context found — instruct the LLM explicitly
        sections.append(
            "\n## Knowledge Base Context\n"
            "**No relevant information was found in the IT knowledge base for this query.**\n"
            "You MUST respond with the standard low-confidence message and suggest escalation.\n"
        )

    # ── 4. Employee question ───────────────────────────────────
    sections.append(f"\n## Employee Question\n{query.strip()}")

    # ── 5. Response instructions ───────────────────────────────
    if retrieved_chunks:
        sections.append(
            "\n## Your Response\n"
            "Provide a clear, grounded answer using the context above. "
            "Cite sources as [Source 1], [Source 2], etc. where applicable. "
            "If resolution steps are needed, number them clearly. "
            "End with a note about creating a ticket if the steps don't resolve the issue."
        )
    else:
        sections.append(
            "\n## Your Response\n"
            "You have no relevant context. Respond with the standard low-confidence message. "
            "Do NOT attempt to answer from general knowledge."
        )

    return "\n".join(sections)


def format_no_context_response() -> str:
    """
    Return a standard response string when no relevant knowledge is found.
    Used as a fallback before even calling the LLM.
    """
    return (
        "I couldn't find relevant information in the IT knowledge base for your question. "
        "This may be because:\n\n"
        "1. Your issue is outside the scope of documented IT procedures.\n"
        "2. The knowledge base may not yet cover this topic.\n\n"
        "**Recommended next steps:**\n"
        "- Check our IT portal: https://itportal.acmecorp.com\n"
        "- Email IT Helpdesk: it-helpdesk@acmecorp.com\n"
        "- Call IT support: +1-800-IT-ACME Ext. 1001 (Mon–Fri, 8 AM–6 PM IST)\n\n"
        "Would you like me to create a support ticket for this issue?"
    )
