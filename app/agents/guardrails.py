# =============================================================
# NexaSupport AI — Confidence & Hallucination Guardrails
# =============================================================
# PURPOSE:
#   Evaluates retrieval quality and determines whether the AI
#   has sufficient grounded evidence to safely answer.
#   Prevents LLM hallucinations on out-of-domain or ambiguous queries.
# =============================================================

from dataclasses import dataclass
from typing import List
from loguru import logger

from app.config import settings
from app.rag.retriever import RetrievedChunk


@dataclass
class ConfidenceEvaluation:
    score: float                # 0.0 to 1.0
    is_confident: bool          # True if >= settings.CONFIDENCE_THRESHOLD
    has_outage_context: bool    # True if live system status detected issue
    has_incident_context: bool  # True if historical tickets matched
    refusal_reason: str = ""    # Explanation if low confidence


def evaluate_response_confidence(
    query: str,
    retrieved_chunks: List[RetrievedChunk],
    has_outage: bool = False,
    has_historical_match: bool = False,
    has_user_access_data: bool = False,
) -> ConfidenceEvaluation:
    """
    Multi-signal confidence scoring:
    1. Maximum chunk similarity (0.0 to 1.0)
    2. Number of supporting chunks
    3. Live IT infrastructure status signal
    4. Historical incident match bonus
    """
    if not retrieved_chunks and not has_outage and not has_user_access_data:
        return ConfidenceEvaluation(
            score=0.0,
            is_confident=False,
            has_outage_context=has_outage,
            has_incident_context=has_historical_match,
            refusal_reason="No relevant company IT documentation or historical incidents found for this issue.",
        )

    # Base score from best retrieval chunk
    top_score = retrieved_chunks[0].similarity_score if retrieved_chunks else 0.0

    # Multi-chunk corroboration bonus
    corroboration_bonus = 0.05 if len(retrieved_chunks) >= 2 else 0.0

    # Historical ticket resolution match bonus
    ticket_bonus = 0.10 if has_historical_match else 0.0

    # Live service status confirmation
    outage_bonus = 0.20 if has_outage else 0.0

    # Access check confirmation
    access_bonus = 0.15 if has_user_access_data else 0.0

    calculated_score = min(
        1.0,
        top_score + corroboration_bonus + ticket_bonus + outage_bonus + access_bonus
    )

    # Threshold comparison
    threshold = settings.CONFIDENCE_THRESHOLD
    is_confident = calculated_score >= threshold

    refusal_reason = ""
    if not is_confident:
        refusal_reason = (
            f"Confidence score ({calculated_score:.0%}) is below the required threshold ({threshold:.0%}). "
            "Escalation to a human IT engineer is recommended to ensure accurate resolution."
        )

    logger.info(
        f"Guardrail Evaluation: Score={calculated_score:.2f} | Confident={is_confident} | "
        f"Outage={has_outage} | HistMatch={has_historical_match}"
    )

    return ConfidenceEvaluation(
        score=round(calculated_score, 2),
        is_confident=is_confident,
        has_outage_context=has_outage,
        has_incident_context=has_historical_match,
        refusal_reason=refusal_reason,
    )
