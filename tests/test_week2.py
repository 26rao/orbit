import os
os.environ["ORBIT_TESTING"] = "1"

import tempfile
from fastapi.testclient import TestClient

from src.semantic.novelty import compute_title_similarity, is_novel
from src.knowledge.db import init_db, insert_source
from src.api.app import app

def test_novelty_scoring():
    # 1. High similarity (reprint syndication / near duplicates)
    t1 = "DeepSeek Releases Open Source Multimodal Model"
    t2 = "DeepSeek Releases Open-Source Multimodal Model"
    sim_high = compute_title_similarity(t1, t2)
    assert sim_high > 0.90, f"Expected >0.90 similarity for near-identical titles, got {sim_high}"

    # 2. Distinct developments
    t3 = "Breakthrough in Room Temperature Sodium Ion Battery Density"
    sim_low = compute_title_similarity(t1, t3)
    assert sim_low < 0.35, f"Expected <0.35 similarity for distinct titles, got {sim_low}"

    # 3. is_novel thresholding
    existing = [t1]
    novel, score, match = is_novel(t2, existing, similarity_threshold=0.90)
    assert not novel, "Candidate should be flagged as duplicate/reprint"

    novel_other, score_other, _ = is_novel(t3, existing, similarity_threshold=0.90)
    assert novel_other, "Candidate should be recognized as genuinely novel"


def test_api_endpoints():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name
    try:
        init_db(temp_db)
        insert_source(
            url="https://example.com/test-ai-paper",
            title="Efficient Attention with Sparse Latents",
            published="2026-10-17T00:00:00Z",
            raw_text="Paper body text explaining sparse attention.",
            summary="Sparse attention paper.",
            fetched_at="2026-10-17T00:00:00Z",
            source_name="arXiv CS.AI",
            content_hash="test_hash_1",
            db_path=temp_db,
        )

        # Override DB_PATH for testing
        import src.api.app as api_module
        original_db = api_module.DB_PATH
        api_module.DB_PATH = temp_db

        with TestClient(app) as client:
            # 1. Health check
            res = client.get("/health")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "healthy"
            assert data["total_discoveries"] >= 1

            # 2. Discoveries list
            res = client.get("/discoveries?limit=10")
            assert res.status_code == 200
            data = res.json()
            assert data["count"] >= 1
            assert "Sparse Latents" in data["discoveries"][0]["title"]

            # 3. Filter by search
            res = client.get("/discoveries?search=Sparse")
            assert res.status_code == 200
            assert res.json()["count"] == 1

            # 4. Sources breakdown
            res = client.get("/sources")
            assert res.status_code == 200
            sources = res.json()["sources"]
            assert len(sources) >= 1
            assert sources[0]["source_name"] == "arXiv CS.AI"

            # 5. HTML Dashboard
            res = client.get("/")
            assert res.status_code == 200
            assert "ORBIT" in res.text
            assert "Live Discovery Stream" in res.text

        api_module.DB_PATH = original_db
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


if __name__ == "__main__":
    print("Running ORBIT Week 2 verification checks...")
    test_novelty_scoring()
    print("  [x] Title similarity & novelty thresholding verified")
    test_api_endpoints()
    print("  [x] FastAPI endpoints & dashboard verified")
    print("\nALL ORBIT WEEK 2 CHECKS PASSED SUCCESSFULLY!")
