"""Semantic intelligence pipeline: clustering, novelty scoring, and DB synchronization."""

import logging
from typing import Dict, Any, List

from src.knowledge.db import (
    get_all_sources_for_clustering,
    update_source_clusters,
    get_topic_clusters,
    DEFAULT_DB_PATH,
)
from src.semantic.clustering import TopicClusterer

logger = logging.getLogger("orbit.semantic")


def run_semantic_pipeline(
    limit: int = 500,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Run topic clustering and novelty scoring across all recent sources in DB.
    Updates SQLite database records with cluster IDs and novelty scores.
    """
    items = get_all_sources_for_clustering(limit=limit, db_path=db_path)
    if not items:
        return {"total_clustered": 0, "topics_count": 0, "topics": []}

    logger.info(f"Running semantic topic clustering on {len(items)} discoveries...")
    clusterer = TopicClusterer(distance_threshold=0.92)
    clustered_items = clusterer.cluster_items(items)

    # Prepare DB updates: (cluster_id, novelty_score, id)
    updates = [
        (it["cluster_id"], it["novelty_score"], it["id"])
        for it in clustered_items
        if "cluster_id" in it and "id" in it
    ]

    update_source_clusters(updates, db_path=db_path)
    topics = clusterer.get_topics_summary()
    logger.info(f"Clustering complete: {len(topics)} topic clusters identified.")

    return {
        "total_clustered": len(items),
        "topics_count": len(topics),
        "topics": topics,
    }
