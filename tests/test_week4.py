import os
os.environ["ORBIT_TESTING"] = "1"

import tempfile
import networkx as nx

from src.knowledge.extraction import resolve_entity, extract_entities_from_text, extract_relations_from_text
from src.knowledge.graph import KnowledgeGraphEngine
from src.knowledge.pipeline import run_knowledge_pipeline
from src.knowledge.db import init_db, insert_source, get_all_entities_and_relations


def test_entity_resolution():
    canon1, type1 = resolve_entity("OpenAI Inc")
    assert canon1 == "OpenAI"
    assert type1 == "Company"

    canon2, type2 = resolve_entity("solid state battery cell")
    assert canon2 == "Solid-State Battery"
    assert type2 == "Technology"

    canon3, type3 = resolve_entity("DeepSeek-AI")
    assert canon3 == "DeepSeek"
    assert type3 == "Company"


def test_relation_extraction():
    text = "NVIDIA unveiled Blackwell Ultra architecture to accelerate large language models."
    triples = extract_relations_from_text(text, source_id=101, published="2026-10-18T00:00:00Z")
    assert len(triples) >= 1
    t = triples[0]
    assert t["source_name"] == "NVIDIA"
    assert t["relation_type"] in ("develops", "improves", "mentions")
    assert t["source_id"] == 101
    assert t["confidence"] > 0.6


def test_networkx_graph_engine():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name
    try:
        init_db(temp_db)
        # Seed 2 sources
        s1 = insert_source(
            url="https://example.com/s1",
            title="Google Quantum AI demonstrates logical qubit memory",
            published="2026-10-18T00:00:00Z",
            raw_text="Google Quantum AI created error-corrected qubit memory.",
            summary="Quantum breakthrough.",
            fetched_at="2026-10-18T00:00:00Z",
            source_name="Nature",
            content_hash="hash_q1",
            db_path=temp_db,
        )
        s2 = insert_source(
            url="https://example.com/s2",
            title="MIT researchers test quantum circuits with AI agents",
            published="2026-10-18T01:00:00Z",
            raw_text="MIT researchers developed quantum circuits using AI agents.",
            summary="Quantum circuit AI.",
            fetched_at="2026-10-18T01:00:00Z",
            source_name="MIT News",
            content_hash="hash_q2",
            db_path=temp_db,
        )

        res = run_knowledge_pipeline(limit=10, db_path=temp_db)
        assert res["nodes_count"] >= 3
        assert res["edges_count"] >= 1

        engine = KnowledgeGraphEngine(db_path=temp_db)
        summary = engine.get_summary()
        assert summary["total_nodes"] >= 3
        assert summary["total_edges"] >= 1

        # Cytoscape export
        cy_data = engine.to_cytoscape()
        assert "elements" in cy_data
        assert len(cy_data["elements"]["nodes"]) >= 3
        assert len(cy_data["elements"]["edges"]) >= 1

        # Key entities
        key_entities = engine.get_key_entities(top_k=5)
        assert len(key_entities) >= 1
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_20_article_tech_graph_acceptance():
    """
    Week 4 Acceptance Criterion:
    Given 20 related articles about one tech domain, the graph shows
    the main entities and at least 3 meaningful cross-links with source provenance.
    """
    articles = [
        ("https://news.com/a1", "OpenAI releases lightweight reasoning model for autonomous AI agents", "OpenAI developed new AI agents."),
        ("https://news.com/a2", "Anthropic challenges OpenAI with computer use capability", "Anthropic competes with OpenAI in AI agents."),
        ("https://news.com/a3", "Google Quantum AI develops quantum circuits for large language models", "Google Quantum AI unveiled quantum circuits."),
        ("https://news.com/a4", "MIT engineers test quantum computing with AI agents", "MIT tested AI agents with quantum computing."),
        ("https://news.com/a5", "NVIDIA partners with OpenAI to accelerate Blackwell Ultra", "NVIDIA partners with OpenAI on large language models."),
        ("https://news.com/a6", "Meta open sources Llama 4 family challenging OpenAI models", "Meta competes with OpenAI in large language models."),
        ("https://news.com/a7", "DeepSeek develops mixture-of-experts architecture for AI agents", "DeepSeek released mixture-of-experts for AI agents."),
        ("https://news.com/a8", "Microsoft collaborates with Anthropic on enterprise AI agents", "Microsoft partners with Anthropic on AI agents."),
        ("https://news.com/a9", "Toyota tests solid-state battery for robotic manipulation systems", "Toyota developed solid-state battery robotics."),
        ("https://news.com/a10", "Tesla deploys AI agents in autonomous vehicles fleet", "Tesla deployed AI agents in autonomous vehicles."),
        ("https://news.com/a11", "Apple incorporates on-device large language models in Xcode", "Apple released large language models."),
        ("https://news.com/a12", "Waymo integrates DeepMind algorithms in robotaxi systems", "Waymo partners with DeepMind on autonomous vehicles."),
        ("https://news.com/a13", "ASML develops high-NA lithography for NVIDIA next-gen chips", "ASML develops EUV lithography for NVIDIA."),
        ("https://news.com/a14", "CERN utilizes large language models for particle tracking", "CERN deployed large language models."),
        ("https://news.com/a15", "Replit partners with Google on developer AI agents", "Replit partners with Google on AI agents."),
        ("https://news.com/a16", "SpaceX applies quantum computing algorithms to orbital trajectories", "SpaceX tested quantum computing."),
        ("https://news.com/a17", "Neuralink integrates AI agents for robotic cursor decoding", "Neuralink develops AI agents for brain interfaces."),
        ("https://news.com/a18", "Moderna applies AlphaFold models to mRNA vaccine discovery", "Moderna utilizes AlphaFold for mRNA vaccine."),
        ("https://news.com/a19", "GNOME partners with DeepSeek on desktop AI integration", "GNOME partners with DeepSeek on AI agents."),
        ("https://news.com/a20", "Google Quantum AI and MIT demonstrate fault-tolerant qubit memory", "Google Quantum AI partners with MIT on qubit memory."),
    ]

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name
    try:
        init_db(temp_db)
        for i, (url, title, body) in enumerate(articles):
            insert_source(
                url=url,
                title=title,
                published=f"2026-10-18T{i:02d}:00:00Z",
                raw_text=body,
                summary=title,
                fetched_at=f"2026-10-18T{i:02d}:00:00Z",
                source_name="Tech Dispatch",
                content_hash=f"hash_20_{i}",
                db_path=temp_db,
            )

        # Run pipeline
        res = run_knowledge_pipeline(limit=25, db_path=temp_db)
        print(f"\n20-Article Graph Result: Nodes={res['nodes_count']}, Edges={res['edges_count']}")

        assert res["nodes_count"] >= 10, f"Expected >=10 entities, got {res['nodes_count']}"
        assert res["edges_count"] >= 3, f"Expected >=3 cross-links, got {res['edges_count']}"

        # Verify source provenance on edges
        engine = KnowledgeGraphEngine(db_path=temp_db)
        cy = engine.to_cytoscape()
        edges = cy["elements"]["edges"]
        provenance_count = 0
        for edge in edges:
            d = edge["data"]
            if d.get("source_url") and d.get("source_title"):
                provenance_count += 1

        print(f"Verified edges with traceable source provenance: {provenance_count}/{len(edges)}")
        assert provenance_count >= 3, f"Expected at least 3 edges with source provenance, got {provenance_count}"

        # Verify API /graph endpoint works with test DB
        from fastapi.testclient import TestClient
        from src.api.app import app
        import src.api.app as api_module
        orig_db = api_module.DB_PATH
        api_module.DB_PATH = temp_db
        with TestClient(app) as client:
            api_res = client.get("/graph")
            assert api_res.status_code == 200
            assert api_res.json()["summary"]["total_nodes"] >= 10
        api_module.DB_PATH = orig_db

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


if __name__ == "__main__":
    print("Running ORBIT Week 4 Knowledge Graph checks...")
    test_entity_resolution()
    print("  [x] Entity resolution verified")
    test_relation_extraction()
    print("  [x] Directed relation extraction verified")
    test_networkx_graph_engine()
    print("  [x] NetworkX graph engine and Cytoscape export verified")
    test_20_article_tech_graph_acceptance()
    print("  [x] 20-article acceptance benchmark with traceable provenance verified (>=3 cross-links)")
    print("\nALL ORBIT WEEK 4 CHECKS PASSED SUCCESSFULLY!")
