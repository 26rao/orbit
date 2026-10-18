import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ORBIT_TESTING"] = "1"

from fastapi.testclient import TestClient
from src.api.app import app
from src.knowledge.db import insert_source, DEFAULT_DB_PATH


def test_discovery_card_endpoint():
    with TestClient(app) as client:
        # Get latest discovery id
        disc_res = client.get("/discoveries?limit=1")
        assert disc_res.status_code == 200
        discoveries = disc_res.json()["discoveries"]
        assert len(discoveries) > 0
        target_id = discoveries[0]["id"]

        card_res = client.get(f"/discoveries/{target_id}/card")
        assert card_res.status_code == 200
        card = card_res.json()

        assert "title" in card
        assert "classification" in card
        assert card["classification"] in ["Verified fact", "Reported claim", "Emerging signal", "AI-generated hypothesis"]
        assert "novelty_score" in card
        assert "provenance_triples" in card
        assert "extracted_entities" in card
        assert "investigation_trajectory" in card


def test_experiment_metrics_endpoint():
    with TestClient(app) as client:
        res = client.get("/experiments/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "experiments" in data
        assert "exp1_trend_detection" in data["experiments"]
        assert "exp2_novelty_deduplication" in data["experiments"]
        assert "exp3_grounded_reasoning" in data["experiments"]
        assert "exp4_autonomous_vs_scheduled" in data["experiments"]
        assert data["all_acceptance_criteria_passed"] is True


def test_html_dashboard_ui_elements():
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        html = res.text
        assert "Experiment Lab" in html
        assert "discovery-modal" in html
        assert "experiment-modal" in html
        assert "openDiscoveryModal" in html
        assert "cytoscape" in html


if __name__ == "__main__":
    print("Running Week 7 UI & API Verification...")
    test_discovery_card_endpoint()
    print("  [x] Discovery Intelligence Card endpoint verified")
    test_experiment_metrics_endpoint()
    print("  [x] Experiment Lab benchmark metrics endpoint verified")
    test_html_dashboard_ui_elements()
    print("  [x] UI components and modals verified")
    print("\nALL WEEK 7 CHECKS PASSED SUCCESSFULLY!")
