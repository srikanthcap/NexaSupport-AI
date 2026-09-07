# =============================================================
# NexaSupport AI — Hybrid Retriever (Semantic + Keyword BM25)
# =============================================================
# PURPOSE:
#   Combines dense semantic vector retrieval (ChromaDB) with
#   exact lexical matching (BM25 / keyword overlap).
#   Particularly essential for exact IT error codes like "809", "0x80070005".
# =============================================================

import math
import re
from collections import Counter
from typing import List, Optional, Dict
from loguru import logger

from app.config import settings
from app.rag.retriever import RetrievedChunk, RAGRetriever


class BM25Scorer:
    """
    Lightweight, fast in-memory BM25 ranker for exact IT term matching.
    Avoids heavy external dependencies while delivering robust lexical scoring.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())

    def score(self, query: str, document: str, avg_doc_len: float = 150.0) -> float:
        query_tokens = self.tokenize(query)
        doc_tokens = self.tokenize(document)
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_len = len(doc_tokens)
        doc_counts = Counter(doc_tokens)

        score = 0.0
        for token in query_tokens:
            freq = doc_counts.get(token, 0)
            if freq > 0:
                # BM25 term frequency saturation
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / avg_doc_len))
                score += numerator / max(denominator, 0.001)

                # Heavy bonus for exact numerical error codes (e.g. 809)
                if token.isdigit() and len(token) >= 3:
                    score += 2.0

        return score


class HybridRetriever:
    """
    Hybrid retriever that blends:
    1. Dense semantic search results from ChromaDB.
    2. Exact keyword BM25 scoring over retrieved candidates.
    3. Reciprocal Rank Fusion (RRF) reranking.
    """

    def __init__(self, base_retriever: Optional[RAGRetriever] = None):
        self.base_retriever = base_retriever or RAGRetriever()
        self.bm25 = BM25Scorer()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_source: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        k = top_k or settings.RAG_TOP_K
        
        # 1. Fetch a broader candidate pool (2x) using semantic search
        semantic_pool = self.base_retriever.retrieve(
            query=query,
            top_k=min(k * 2, 10),
            filter_source=filter_source,
        )

        if not semantic_pool:
            return []

        # 2. Score candidates with BM25
        scored_candidates = []
        for rank, chunk in enumerate(semantic_pool):
            lexical_score = self.bm25.score(query, chunk.text)
            
            # Reciprocal Rank Fusion formula: 1 / (60 + rank) + normalized BM25
            rrf_score = (1.0 / (60.0 + rank + 1.0)) + (min(lexical_score, 10.0) / 20.0)
            
            # Weighted hybrid similarity
            hybrid_score = round(min(1.0, 0.65 * chunk.similarity_score + 0.35 * min(1.0, lexical_score / 3.0)), 3)
            
            # Update chunk similarity score with hybrid score
            chunk.similarity_score = max(chunk.similarity_score, hybrid_score)
            scored_candidates.append((rrf_score, chunk))

        # 3. Rerank by blended RRF score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # 4. Return top-K reranked chunks
        final_chunks = [item[1] for item in scored_candidates[:k]]
        logger.info(f"HybridRetriever: Evaluated {len(semantic_pool)} candidates -> Selected top {len(final_chunks)}")
        return final_chunks
