"""Evaluation metrics for Grounded RAG vs Pure LLM (Experiment 3)."""

from typing import List, Dict, Any, Tuple
import re

from src.reasoning.ollama_client import GroundedRAGEngine
from src.knowledge.db import get_latest_sources, DEFAULT_DB_PATH


def evaluate_citation_correctness(answer: Dict[str, Any], db_sources_by_id: Dict[int, Dict[str, Any]]) -> float:
    """
    Compute citation correctness: percentage of cited facts/claims whose cited source
    actually exists and contains supporting terms.
    """
    total_claims = 0
    correct_citations = 0

    claims = []
    for f in answer.get("verified_facts", []):
        claims.append((f.get("fact", ""), f.get("source_id")))
    for c in answer.get("reported_claims", []):
        claims.append((c.get("claim", ""), c.get("source_id")))

    if not claims:
        return 1.0  # No unsupported claims made

    for text, sid in claims:
        total_claims += 1
        if sid not in db_sources_by_id:
            continue

        src = db_sources_by_id[sid]
        src_text = f"{src.get('title', '')} {src.get('summary', '')} {src.get('raw_text', '')}".lower()

        # Check keyword overlap between claim and source text
        words = [w for w in re.sub(r"\W+", " ", text.lower()).split() if len(w) > 3]
        if any(w in src_text for w in words):
            correct_citations += 1

    return correct_citations / float(total_claims) if total_claims > 0 else 1.0


def evaluate_unsupported_claim_rate(answer: Dict[str, Any], db_sources_by_id: Dict[int, Dict[str, Any]]) -> float:
    """
    Compute unsupported claim rate: percentage of claims that lack backing evidence or cite non-existent sources.
    unsupported_rate = 1.0 - citation_correctness.
    """
    return 1.0 - evaluate_citation_correctness(answer, db_sources_by_id)


def run_experiment_3_benchmark(
    questions: List[str],
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Run 20-question benchmark comparing Grounded RAG vs Pure LLM.
    Returns comparative metrics: unsupported_claim_rate, citation_correctness, and relative improvement.
    """
    engine = GroundedRAGEngine(db_path=db_path)
    engine.retriever.sync()

    # Pre-index DB sources by ID for fast ground truth lookup
    all_sources = get_latest_sources(limit=1000, db_path=db_path)
    sources_by_id = {s["id"]: s for s in all_sources}

    rag_unsupported_rates = []
    pure_unsupported_rates = []

    for q in questions:
        # Grounded RAG answer
        rag_ans = engine.answer_query(q, top_k=3)
        rag_unsupported = evaluate_unsupported_claim_rate(rag_ans, sources_by_id)
        rag_unsupported_rates.append(rag_unsupported)

        # Pure LLM baseline answer
        pure_ans = engine.pure_llm_baseline(q)
        pure_unsupported = evaluate_unsupported_claim_rate(pure_ans, sources_by_id)
        pure_unsupported_rates.append(pure_unsupported)

    avg_rag_unsupported = sum(rag_unsupported_rates) / len(rag_unsupported_rates)
    avg_pure_unsupported = sum(pure_unsupported_rates) / len(pure_unsupported_rates)

    # Reduction in unsupported claim rate: (pure - rag) / pure
    reduction = (
        (avg_pure_unsupported - avg_rag_unsupported) / avg_pure_unsupported
        if avg_pure_unsupported > 0
        else 0.0
    )

    return {
        "num_questions": len(questions),
        "grounded_rag_unsupported_rate": round(avg_rag_unsupported, 3),
        "pure_llm_unsupported_rate": round(avg_pure_unsupported, 3),
        "unsupported_claim_reduction_pct": round(reduction * 100, 1),
        "meets_acceptance_criterion": reduction >= 0.40,
    }
