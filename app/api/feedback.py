# =============================================================
# NexaSupport AI — Feedback API Router
# =============================================================
# PURPOSE:
#   Collects user ratings on AI responses ("helpful" / "not helpful").
#   Stored in-memory for now (Phase 17+: persist to DB for retraining loop).
#
# ENDPOINTS:
#   POST /api/v1/feedback        — Submit rating on an AI answer
#   GET  /api/v1/feedback/stats  — Aggregate feedback metrics (admin)
# =============================================================

from collections import defaultdict
from datetime import datetime
from typing import List

from fastapi import APIRouter
from loguru import logger

from app.models.schemas import FeedbackRequest

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])

# ── In-memory feedback store ───────────────────────────────────────────────────
# Each entry: {query, answer, rating, comment, confidence, timestamp}
# Phase 17+: swap this for a DB table / JSONL append-log for fine-tuning.
_feedback_log: List[dict] = []


@router.post(
    "",
    status_code=201,
    summary="Submit feedback on an AI answer",
    description=(
        "Rate whether the AI answer was helpful or not. "
        "Feedback is used to track answer quality and improve the system over time."
    ),
)
async def submit_feedback(payload: FeedbackRequest):
    """
    Submit a helpful / not_helpful rating for an AI answer.

    - **query**: The original IT question.
    - **answer**: The AI response that was shown.
    - **rating**: 'helpful' or 'not_helpful'.
    - **comment**: Optional free-text explanation.
    - **confidence**: The pipeline's confidence score at time of response.
    """
    entry = {
        "query": payload.query,
        "answer_preview": payload.answer[:200],
        "rating": payload.rating,
        "comment": payload.comment,
        "confidence": payload.confidence,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _feedback_log.append(entry)
    logger.info(
        f"Feedback received: rating={payload.rating} | "
        f"confidence={payload.confidence} | query='{payload.query[:60]}'"
    )

    return {
        "success": True,
        "message": "Thank you for your feedback! It helps us improve NexaSupport AI.",
        "total_feedback_count": len(_feedback_log),
    }


@router.get(
    "/stats",
    summary="Get aggregate feedback metrics",
    tags=["System"],
)
async def feedback_stats():
    """
    Returns aggregate feedback statistics — total responses rated,
    helpful %, not helpful %, and average confidence per category.
    """
    if not _feedback_log:
        return {
            "total": 0,
            "helpful": 0,
            "not_helpful": 0,
            "helpful_pct": 0.0,
            "avg_confidence_helpful": None,
            "avg_confidence_not_helpful": None,
            "low_confidence_not_helpful": [],
        }

    helpful = [e for e in _feedback_log if e["rating"] == "helpful"]
    not_helpful = [e for e in _feedback_log if e["rating"] == "not_helpful"]
    total = len(_feedback_log)

    def avg_conf(entries):
        scores = [e["confidence"] for e in entries if e.get("confidence") is not None]
        return round(sum(scores) / len(scores), 3) if scores else None

    # Surface the worst cases: low-confidence answers that users rated not helpful
    low_conf_bad = [
        {"query": e["query"], "confidence": e["confidence"], "comment": e.get("comment")}
        for e in not_helpful
        if e.get("confidence") is not None and e["confidence"] < 0.5
    ][-10:]  # Last 10

    return {
        "total": total,
        "helpful": len(helpful),
        "not_helpful": len(not_helpful),
        "helpful_pct": round(len(helpful) / total * 100, 1),
        "avg_confidence_helpful": avg_conf(helpful),
        "avg_confidence_not_helpful": avg_conf(not_helpful),
        "low_confidence_not_helpful": low_conf_bad,
    }
