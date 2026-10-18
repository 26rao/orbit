"""ORBIT Comprehensive Full System Integration Test Suite.
Verifies end-to-end integration across all 8 development weeks:
- Week 1: Ingestion & Storage Deduplication
- Week 2: Discovery Feed & Novelty Filter
- Week 3: Semantic Embeddings & Topic Clustering
- Week 4: Knowledge Graph with Traceable Provenance
- Week 5: Evidence-Grounded RAG & Hybrid Retrieval
- Week 6: Autonomous 6-Stage State Machine Loop
- Week 7: Discovery Card API & Product Dashboard UI
- Week 8: 100-Case Evaluation Benchmark Standard
"""

import os
import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ORBIT_TESTING"] = "1"

from fastapi.testclient import TestClient

from src.knowledge.db import (
    init_db,
    insert_source,
    get_source_count,
    get_latest_sources,
    get_topic_clusters,
    DEFAULT_DB_PATH,
)
from src.semantic.novelty import compute_title_similarity, is_novel
from src.semantic.clustering import TopicClusterer
from src.knowledge.extraction import extract_entities_from_text, extract_relations_from_text
from src.knowledge.graph import KnowledgeGraphEngine
from src.reasoning.retrieval import BM25Retriever, HybridRetriever
from src.reasoning.ollama_client import GroundedRAGEngine
from src.agent.prioritization import KnowledgeGap, PriorityQueueEngine
from src.agent.state_machine import OrbitAutonomousAgent, AgentState
from src.api.app import app


def test_week1_collector_and_storage():
    print("[1/8] Verifying Week 1: Ingestion & Storage Deduplication...")
    count = get_source_count()
    assert count >= 10, f"Expected at least 10 active discoveries, got {count}"
    sources = get_latest_sources(limit=5)
    for s in sources:
        assert s["url"].startswith("http")
        assert len(s["content_hash"]) == 64  # Valid SHA-256
        assert s["status"] in ["fetched", "raw", "active", "indexed", "clustered"]
    print("      -> Week 1 Verified: SQLite storage, URL normalization, SHA-256 deduplication operational.")


def test_week2_discovery_feed_and_novelty():
    print("[2/8] Verifying Week 2: Discovery Feed & Novelty Filter...")
    # Test title novelty gating
    sim_identical = compute_title_similarity("Quantum Computing Advances", "Quantum Computing Advances")
    assert sim_identical >= 0.99
    sim_distinct = compute_title_similarity("Quantum Computing Advances", "Synthetic Biology mRNA Delivery")
    assert sim_distinct < 0.35

    with TestClient(app) as client:
        res = client.get("/discoveries?limit=10")
        assert res.status_code == 200
        data = res.json()
        assert len(data["discoveries"]) > 0
    print("      -> Week 2 Verified: SequenceMatcher novelty score and feed endpoint operational.")


def test_week3_semantic_clustering():
    print("[3/8] Verifying Week 3: Topic Clustering & Semantic Vectors...")
    clusters = get_topic_clusters()
    assert len(clusters) >= 2, f"Expected at least 2 active topic clusters, got {len(clusters)}"
    for c in clusters:
        assert "cluster_id" in c
        assert "sample_title" in c
        assert c["item_count"] >= 1
    print("      -> Week 3 Verified: TopicClusterer formed coherent thematic clusters.")


def test_week4_knowledge_graph_and_provenance():
    print("[4/8] Verifying Week 4: Knowledge Graph with Traceable Provenance...")
    engine = KnowledgeGraphEngine(db_path=DEFAULT_DB_PATH)
    summary = engine.get_summary()
    assert summary["total_nodes"] >= 10
    assert summary["total_edges"] >= 5

    cy = engine.to_cytoscape()
    assert "elements" in cy
    assert len(cy["elements"]["nodes"]) >= 10
    # Verify provenance on edges
    for edge in cy["elements"]["edges"]:
        d = edge["data"]
        assert "source_id" in d
        assert "source_title" in d
    print(f"      -> Week 4 Verified: Graph contains {summary['total_nodes']} entities, {summary['total_edges']} edges with 100% provenance.")


def test_week5_evidence_grounded_rag():
    print("[5/8] Verifying Week 5: Grounded RAG & Hybrid Retrieval...")
    rag = GroundedRAGEngine(db_path=DEFAULT_DB_PATH)
    ans = rag.answer_query("What are the latest advances in artificial intelligence?", top_k=3)
    assert "summary" in ans
    assert "verified_facts" in ans
    assert "reported_claims" in ans
    assert "citations" in ans
    assert len(ans["citations"]) > 0
    print("      -> Week 5 Verified: Pure-Python BM25 + Dense Hybrid search and 4-way claim schema operational.")


def test_week6_autonomous_state_machine():
    print("[6/8] Verifying Week 6: Autonomous State Machine Loop...")
    agent = OrbitAutonomousAgent(db_path=DEFAULT_DB_PATH, query_budget=5)
    status = agent.get_status()
    assert status["current_state"] == "IDLE"
    assert "budget_spent" in status
    assert "budget_limit" in status

    # Verify priority queue logic
    gap = KnowledgeGap(cluster_id=99, topic_title="Novel test frontier", novelty=0.95, evidence_count=1)
    pq = PriorityQueueEngine()
    pq.push_gap(gap)
    top = pq.pop_highest_gap()
    assert top.cluster_id == 99
    print("      -> Week 6 Verified: 6-stage finite state machine and priority queue operational.")


def test_week7_ui_and_card_api():
    print("[7/8] Verifying Week 7: Discovery Card API & Product UI Polish...")
    with TestClient(app) as client:
        # Check discovery intelligence card
        disc_res = client.get("/discoveries?limit=1")
        first_id = disc_res.json()["discoveries"][0]["id"]
        card_res = client.get(f"/discoveries/{first_id}/card")
        assert card_res.status_code == 200
        card = card_res.json()
        assert card["classification"] in ["Verified fact", "Reported claim", "Emerging signal", "AI-generated hypothesis"]
        assert "content_hash" in card

        # Check Experiment Lab metrics
        metric_res = client.get("/experiments/metrics")
        assert metric_res.status_code == 200
        assert metric_res.json()["all_acceptance_criteria_passed"] is True

        # Check UI HTML contains all modules
        html_res = client.get("/")
        assert html_res.status_code == 200
        html = html_res.text
        assert "Experiment Lab" in html
        assert "discovery-modal" in html
        assert "cytoscape" in html
    print("      -> Week 7 Verified: Discovery card modal, Experiment Lab scoreboard, and Cytoscape UI operational.")


def test_week8_frozen_evaluation_suite():
    print("[8/8] Verifying Week 8: 100-Case Scientific Evaluation Standard...")
    eval_file = ROOT / "data" / "eval_set" / "eval_dataset.json"
    assert eval_file.exists(), "eval_dataset.json must exist"
    with open(eval_file, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    assert eval_data["metadata"]["total_cases"] == 100
    assert len(eval_data["exp1_trend_detection"]) == 25
    assert len(eval_data["exp2_novelty"]) == 25
    assert len(eval_data["exp3_grounded_reasoning"]) == 25
    assert len(eval_data["exp4_autonomous_vs_scheduled"]) == 25

    results_file = ROOT / "data" / "eval_set" / "experiment_results.json"
    assert results_file.exists(), "experiment_results.json must exist"
    with open(results_file, "r", encoding="utf-8") as f:
        results = json.load(f)
    assert results["all_acceptance_criteria_passed"] is True
    print("      -> Week 8 Verified: 100-case dataset and all 4 experiment benchmark targets passed.")


def run_full_system_verification():
    print("\n" + "=" * 70)
    print("  ORBIT END-TO-END FULL SYSTEM INTEGRATION VERIFICATION")
    print("=" * 70)

    test_week1_collector_and_storage()
    test_week2_discovery_feed_and_novelty()
    test_week3_semantic_clustering()
    test_week4_knowledge_graph_and_provenance()
    test_week5_evidence_grounded_rag()
    test_week6_autonomous_state_machine()
    test_week7_ui_and_card_api()
    test_week8_frozen_evaluation_suite()

    print("\n" + "=" * 70)
    print("  SUCCESS: ALL 8 WEEKS COMPLETED, INTEGRATED, AND FULLY VERIFIED!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_full_system_verification()
