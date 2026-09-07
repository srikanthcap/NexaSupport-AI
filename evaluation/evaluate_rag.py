# =============================================================
# NexaSupport AI — Offline RAG Evaluation Suite (Phase 13)
# =============================================================
# PURPOSE:
#   Evaluates the RAG pipeline quality against a curated golden
#   Q&A dataset without needing the live FastAPI server.
#
#   Scoring dimensions:
#     1. Context Recall     — Did the retriever find the right doc?
#     2. Answer Relevance   — Do expected keywords appear in the answer?
#     3. Confidence Score   — What did the pipeline's own confidence meter report?
#     4. Escalation Rate    — How often did the pipeline give up? (lower = better)
#     5. Latency            — Average time to answer in milliseconds
#
# HOW TO RUN (from the project root, with venv activated):
#   python evaluation/evaluate_rag.py
#
# OUTPUT:
#   - Live progress to console
#   - evaluation/results/eval_report_<timestamp>.json (raw data)
#   - evaluation/results/eval_report_<timestamp>.md  (human-readable summary)
#
# REQUIRES:
#   - ChromaDB index must already be built (run scripts/build_index.py first)
#   - GEMINI_API_KEY must be set in .env
# =============================================================

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Ensure the project root is on sys.path so `app.*` imports work
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Load .env before importing settings
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from loguru import logger

GOLDEN_DATASET_PATH = ROOT / "evaluation" / "golden_dataset.json"
RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ── Scoring Helpers ────────────────────────────────────────

def score_context_recall(sources: List[Dict], expected_source_contains: str) -> float:
    """
    Checks if at least one retrieved source file name contains the
    expected document identifier (e.g. 'vpn', 'email', 'password').

    Returns 1.0 if found, 0.0 otherwise.
    """
    if not expected_source_contains:
        return 1.0
    for src in sources:
        src_file = src.get("source_file", "").lower()
        if expected_source_contains.lower() in src_file:
            return 1.0
    return 0.0


def score_answer_relevance(answer: str, expected_keywords: List[str]) -> float:
    """
    Keyword-overlap relevance: what fraction of the expected keywords
    appear (case-insensitive) in the generated answer?

    A score of 1.0 means all expected keywords were present.
    """
    if not expected_keywords:
        return 1.0
    answer_lower = answer.lower()
    matched = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return round(matched / len(expected_keywords), 3)


def classify_quality(recall: float, relevance: float, confidence: float) -> str:
    """Overall quality label for a single evaluation item."""
    avg = (recall + relevance + confidence) / 3
    if avg >= 0.75:
        return "✅ PASS"
    elif avg >= 0.50:
        return "⚠️  MARGINAL"
    else:
        return "❌ FAIL"


# ── Main Evaluation Runner ─────────────────────────────────

def run_evaluation() -> Dict[str, Any]:
    """
    Loads the golden dataset and runs each question through the
    RAG pipeline. Computes scoring dimensions and aggregates results.
    """
    logger.info("=" * 60)
    logger.info("NexaSupport AI — RAG Evaluation Suite")
    logger.info("=" * 60)

    # Load golden dataset
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        golden_dataset = json.load(f)

    logger.info(f"Loaded {len(golden_dataset)} golden Q&A pairs")

    # Late import — triggers embedding model load and ChromaDB connection
    logger.info("Initialising RAG pipeline (this may take a moment)...")
    from app.rag.pipeline import get_rag_pipeline
    pipeline = get_rag_pipeline()
    logger.info("Pipeline ready.")

    results = []
    total_latency = 0.0
    escalation_count = 0

    for item in golden_dataset:
        qid = item["id"]
        query = item["query"]
        expected_keywords = item.get("expected_keywords", [])
        expected_source = item.get("expected_source_contains", "")

        logger.info(f"\n[{qid}] Query: {query[:80]}...")

        try:
            response = pipeline.query(query=query, top_k=5)
        except Exception as e:
            logger.error(f"[{qid}] Pipeline error: {e}")
            results.append({
                "id": qid,
                "category": item.get("category", "Unknown"),
                "query": query,
                "error": str(e),
                "quality": "❌ FAIL",
            })
            continue

        # Compute scores
        recall = score_context_recall(
            [{"source_file": s.source_file} for s in response.sources],
            expected_source,
        )
        relevance = score_answer_relevance(response.answer, expected_keywords)
        confidence = response.confidence
        quality = classify_quality(recall, relevance, confidence)
        total_latency += response.latency_ms

        if response.needs_escalation:
            escalation_count += 1

        matched_keywords = [
            kw for kw in expected_keywords if kw.lower() in response.answer.lower()
        ]
        missing_keywords = [
            kw for kw in expected_keywords if kw.lower() not in response.answer.lower()
        ]

        result_entry = {
            "id": qid,
            "category": item.get("category", "Unknown"),
            "query": query,
            "quality": quality,
            "scores": {
                "context_recall": recall,
                "answer_relevance": relevance,
                "pipeline_confidence": round(confidence, 3),
            },
            "retrieval_count": response.retrieval_count,
            "latency_ms": response.latency_ms,
            "needs_escalation": response.needs_escalation,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "sources": [
                {"title": s.title, "file": s.source_file, "score": s.similarity_score}
                for s in response.sources
            ],
            "answer_preview": response.answer[:300] + ("..." if len(response.answer) > 300 else ""),
        }
        results.append(result_entry)

        logger.info(
            f"  Quality: {quality} | "
            f"Recall: {recall:.0%} | "
            f"Relevance: {relevance:.0%} | "
            f"Confidence: {confidence:.0%} | "
            f"Latency: {response.latency_ms:.0f}ms"
        )
        if missing_keywords:
            logger.warning(f"  Missing keywords: {missing_keywords}")

    # ── Aggregate Metrics ──────────────────────────────────
    n = len([r for r in results if "error" not in r])
    avg_recall = sum(r["scores"]["context_recall"] for r in results if "scores" in r) / max(n, 1)
    avg_relevance = sum(r["scores"]["answer_relevance"] for r in results if "scores" in r) / max(n, 1)
    avg_confidence = sum(r["scores"]["pipeline_confidence"] for r in results if "scores" in r) / max(n, 1)
    avg_latency = total_latency / max(n, 1)
    escalation_rate = escalation_count / max(n, 1)
    pass_count = sum(1 for r in results if r["quality"] == "✅ PASS")
    marginal_count = sum(1 for r in results if "MARGINAL" in r["quality"])
    fail_count = sum(1 for r in results if "FAIL" in r["quality"])

    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_questions": len(golden_dataset),
        "evaluated": n,
        "pass": pass_count,
        "marginal": marginal_count,
        "fail": fail_count,
        "avg_context_recall": round(avg_recall, 3),
        "avg_answer_relevance": round(avg_relevance, 3),
        "avg_pipeline_confidence": round(avg_confidence, 3),
        "avg_latency_ms": round(avg_latency, 1),
        "escalation_rate": round(escalation_rate, 3),
    }

    full_report = {"summary": summary, "results": results}

    # ── Save JSON Report ───────────────────────────────────
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = RESULTS_DIR / f"eval_report_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
    logger.info(f"\n📄 JSON report saved: {json_path}")

    # ── Save Markdown Report ───────────────────────────────
    md_path = RESULTS_DIR / f"eval_report_{ts}.md"
    _write_markdown_report(md_path, summary, results)
    logger.info(f"📝 Markdown report saved: {md_path}")

    # ── Print Summary to Console ───────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"  Total Questions  : {summary['total_questions']}")
    logger.info(f"  ✅ PASS          : {pass_count}")
    logger.info(f"  ⚠️  MARGINAL      : {marginal_count}")
    logger.info(f"  ❌ FAIL          : {fail_count}")
    logger.info(f"  Context Recall   : {avg_recall:.1%}")
    logger.info(f"  Answer Relevance : {avg_relevance:.1%}")
    logger.info(f"  Avg Confidence   : {avg_confidence:.1%}")
    logger.info(f"  Avg Latency      : {avg_latency:.0f}ms")
    logger.info(f"  Escalation Rate  : {escalation_rate:.1%}")
    logger.info("=" * 60)

    return full_report


def _write_markdown_report(
    path: Path,
    summary: Dict[str, Any],
    results: List[Dict[str, Any]],
) -> None:
    """Write a human-readable markdown evaluation report."""
    lines = [
        "# NexaSupport AI — RAG Evaluation Report\n",
        f"**Generated**: {summary['timestamp']} UTC\n",
        "---\n",
        "## Summary\n",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Questions | {summary['total_questions']} |",
        f"| ✅ PASS | {summary['pass']} |",
        f"| ⚠️ MARGINAL | {summary['marginal']} |",
        f"| ❌ FAIL | {summary['fail']} |",
        f"| Avg Context Recall | {summary['avg_context_recall']:.1%} |",
        f"| Avg Answer Relevance | {summary['avg_answer_relevance']:.1%} |",
        f"| Avg Pipeline Confidence | {summary['avg_pipeline_confidence']:.1%} |",
        f"| Avg Latency | {summary['avg_latency_ms']:.0f}ms |",
        f"| Escalation Rate | {summary['escalation_rate']:.1%} |",
        "\n---\n",
        "## Question-Level Results\n",
        "| ID | Category | Quality | Recall | Relevance | Confidence | Latency |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in results:
        if "error" in r:
            lines.append(
                f"| {r['id']} | {r['category']} | ❌ ERROR | — | — | — | — |"
            )
        else:
            s = r["scores"]
            lines.append(
                f"| {r['id']} | {r['category']} | {r['quality']} "
                f"| {s['context_recall']:.0%} "
                f"| {s['answer_relevance']:.0%} "
                f"| {s['pipeline_confidence']:.0%} "
                f"| {r['latency_ms']:.0f}ms |"
            )

    lines.append("\n---\n")
    lines.append("## Answer Previews\n")
    for r in results:
        if "error" not in r:
            lines.append(f"### {r['id']} — {r['category']}")
            lines.append(f"> **Query**: {r['query']}\n")
            lines.append(f"**Missing keywords**: {r.get('missing_keywords', [])} | "
                         f"**Sources**: {[s['file'] for s in r.get('sources', [])]}\n")
            lines.append(f"```\n{r['answer_preview']}\n```\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── Entry Point ────────────────────────────────────────────

if __name__ == "__main__":
    report = run_evaluation()
    # Exit with non-zero code if majority of questions fail
    fail_rate = report["summary"]["fail"] / max(report["summary"]["total_questions"], 1)
    sys.exit(1 if fail_rate > 0.5 else 0)
