"""Hybrid BM25 and dense semantic retrieval engine for ORBIT."""

import math
import re
from collections import Counter
from typing import List, Dict, Any, Tuple
import numpy as np

from src.knowledge.db import get_all_sources_for_clustering, DEFAULT_DB_PATH
from src.semantic.embeddings import SemanticEmbedder


class BM25Retriever:
    """
    Zero-dependency Okapi BM25 implementation for lexical keyword retrieval.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_freqs: Dict[str, int] = Counter()
        self.doc_lens: List[int] = []
        self.doc_tokens: List[List[str]] = []
        self.idf: Dict[str, float] = {}
        self.items: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"\W+", " ", text.lower()).strip()
        return [w for w in cleaned.split() if len(w) > 2]

    def fit(self, items: List[Dict[str, Any]]) -> None:
        """Index corpus items."""
        self.items = items
        self.corpus_size = len(items)
        if self.corpus_size == 0:
            return

        self.doc_tokens = []
        self.doc_lens = []
        self.doc_freqs.clear()

        total_len = 0
        for item in items:
            combined_text = f"{item.get('title', '')} {item.get('summary', '')} {item.get('raw_text', '')[:600]}"
            tokens = self._tokenize(combined_text)
            self.doc_tokens.append(tokens)
            l = len(tokens)
            self.doc_lens.append(l)
            total_len += l

            # Track unique tokens per doc for DF
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freqs[t] += 1

        self.avg_doc_len = total_len / float(self.corpus_size) if self.corpus_size > 0 else 0.0

        # Calculate IDF for all indexed terms
        self.idf.clear()
        for term, df in self.doc_freqs.items():
            # Standard Lucene/Okapi IDF formula with smoothing
            self.idf[term] = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """Retrieve top_k items scored by BM25."""
        if not self.corpus_size:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = [0.0] * self.corpus_size

        for term in query_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]

            for i, tokens in enumerate(self.doc_tokens):
                tf = tokens.count(term)
                if tf == 0:
                    continue
                doc_len = self.doc_lens[i]
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[i] += idf_val * (num / denom)

        ranked_indices = sorted(range(self.corpus_size), key=lambda idx: scores[idx], reverse=True)[:top_k]
        return [(self.items[idx], float(scores[idx])) for idx in ranked_indices if scores[idx] > 0]


class HybridRetriever:
    """
    Hybrid retriever combining BM25 lexical search with dense vector similarity.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH, alpha: float = 0.5):
        """
        alpha: weight for dense retrieval (1.0 = pure dense, 0.0 = pure BM25).
        """
        self.db_path = db_path
        self.alpha = alpha
        self.bm25 = BM25Retriever()
        self.embedder = SemanticEmbedder()
        self.dense_embeddings: np.ndarray = np.empty((0, 0))
        self.items: List[Dict[str, Any]] = []

    def sync(self, limit: int = 500) -> None:
        """Index database sources for hybrid retrieval."""
        self.items = get_all_sources_for_clustering(limit=limit, db_path=self.db_path)
        if not self.items:
            return

        self.bm25.fit(self.items)

        # Build dense embeddings
        texts = [f"{it.get('title', '')}. {it.get('summary', '')}" for it in self.items]
        self.dense_embeddings = self.embedder.fit_transform(texts)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve and rank top_k sources using hybrid score:
        score = alpha * dense_sim + (1 - alpha) * normalized_bm25
        """
        if not self.items:
            self.sync()
        if not self.items:
            return []

        # 1. BM25 scores keyed by item ID
        bm25_matches = self.bm25.search(query, top_k=len(self.items))
        bm25_by_id = {item["id"]: score for item, score in bm25_matches}
        max_bm25 = max(bm25_by_id.values(), default=1.0)
        if max_bm25 == 0.0:
            max_bm25 = 1.0

        # 2. Dense semantic scores
        q_vec = self.embedder.transform([query])[0]
        dense_scores = np.dot(self.dense_embeddings, q_vec)

        # 3. Combine scores
        combined = []
        for i, item in enumerate(self.items):
            item_id = item["id"]
            bm25_val = bm25_by_id.get(item_id, 0.0) / max_bm25
            dense_val = float(dense_scores[i])

            hybrid_score = (self.alpha * dense_val) + ((1.0 - self.alpha) * bm25_val)
            combined.append({
                "source_id": item["id"],
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "summary": item.get("summary", ""),
                "raw_text": item.get("raw_text", "")[:400],
                "published": item.get("published", ""),
                "source_name": item.get("source_name", ""),
                "dense_score": round(dense_val, 4),
                "bm25_score": round(bm25_val, 4),
                "hybrid_score": round(hybrid_score, 4),
            })

        combined.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return combined[:top_k]
