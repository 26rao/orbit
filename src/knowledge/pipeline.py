"""Knowledge graph ingestion pipeline: parses entities, relations, and provenance."""

import logging
from typing import Dict, Any, List

from src.knowledge.db import (
    get_all_sources_for_clustering,
    upsert_entity,
    insert_relation,
    DEFAULT_DB_PATH,
)
from src.knowledge.extraction import extract_relations_from_text
from src.knowledge.graph import KnowledgeGraphEngine

logger = logging.getLogger("orbit.knowledge")


def run_knowledge_pipeline(
    limit: int = 500,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Extract entities and relations from sources, persist into SQLite, and update NetworkX graph.
    """
    items = get_all_sources_for_clustering(limit=limit, db_path=db_path)
    if not items:
        return {"nodes_count": 0, "edges_count": 0, "sources_processed": 0}

    logger.info(f"Extracting entities & relations from {len(items)} sources...")

    entities_cache = {}  # canonical_name -> entity_id
    total_triples = 0

    for item in items:
        source_id = item["id"]
        title = item.get("title", "")
        summary = item.get("summary", "")
        published = item.get("published", "")
        combined_text = f"{title}. {summary}"

        triples = extract_relations_from_text(
            combined_text, source_id=source_id, published=published
        )

        for t in triples:
            s_name, s_type = t["source_name"], t["source_type"]
            o_name, o_type = t["target_name"], t["target_type"]

            # Upsert entities
            if s_name not in entities_cache:
                entities_cache[s_name] = upsert_entity(s_name, s_type, db_path=db_path)
            if o_name not in entities_cache:
                entities_cache[o_name] = upsert_entity(o_name, o_type, db_path=db_path)

            s_id = entities_cache[s_name]
            o_id = entities_cache[o_name]

            # Insert relation
            rel_id = insert_relation(
                source_entity_id=s_id,
                target_entity_id=o_id,
                relation_type=t["relation_type"],
                source_id=source_id,
                confidence=t["confidence"],
                occurred_at=published,
                db_path=db_path,
            )
            if rel_id:
                total_triples += 1

    # Sync into NetworkX
    engine = KnowledgeGraphEngine(db_path=db_path)
    summary = engine.get_summary()

    logger.info(
        f"Knowledge graph updated: {summary['total_nodes']} nodes, {summary['total_edges']} edges."
    )

    return {
        "nodes_count": summary["total_nodes"],
        "edges_count": summary["total_edges"],
        "sources_processed": len(items),
        "new_relations_ingested": total_triples,
    }
