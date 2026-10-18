"""Knowledge gap identification and priority queue engine for autonomous investigations."""

import math
import heapq
from typing import List, Dict, Any, Optional

from src.knowledge.db import get_topic_clusters, get_latest_sources, DEFAULT_DB_PATH
from src.knowledge.graph import KnowledgeGraphEngine


class KnowledgeGap:
    """Represents an emerging discovery with high novelty but low evidence density."""

    def __init__(
        self,
        cluster_id: int,
        topic_title: str,
        novelty: float,
        evidence_count: int,
        graph_degree: int = 1,
    ):
        self.cluster_id = cluster_id
        self.topic_title = topic_title
        self.novelty = max(0.0, min(1.0, novelty))
        self.evidence_count = max(1, evidence_count)
        self.graph_degree = max(1, graph_degree)

        # Priority formula: High Novelty * (1 / Evidence Density) * Connectedness
        density_factor = 1.0 / (1.0 + math.log(1.0 + self.evidence_count))
        connectedness = 1.0 + 0.15 * math.log(1.0 + self.graph_degree)
        self.score = round(self.novelty * density_factor * connectedness, 4)

    def __lt__(self, other: "KnowledgeGap") -> bool:
        # Max-heap behavior for PriorityQueue
        return self.score > other.score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "topic_title": self.topic_title,
            "novelty": self.novelty,
            "evidence_count": self.evidence_count,
            "graph_degree": self.graph_degree,
            "priority_score": self.score,
        }


class PriorityQueueEngine:
    """Maintains prioritized queue of active knowledge gaps for ORBIT to investigate."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.queue: List[KnowledgeGap] = []

    def refresh_gaps(self) -> List[KnowledgeGap]:
        """Scan clusters and knowledge graph to populate priority queue."""
        clusters = get_topic_clusters(self.db_path)
        graph_engine = KnowledgeGraphEngine(db_path=self.db_path)
        graph = graph_engine.sync_from_db()

        self.queue.clear()
        gaps = []

        for c in clusters:
            c_id = c["cluster_id"]
            title = c["sample_title"]
            novelty = c["avg_novelty"] or 0.8
            count = c["item_count"]

            # Estimate entity graph connectivity
            matched_nodes = [n for n in graph.nodes if n.lower() in title.lower()]
            degree = max((graph.degree(n) for n in matched_nodes), default=1)

            gap = KnowledgeGap(
                cluster_id=c_id,
                topic_title=title,
                novelty=novelty,
                evidence_count=count,
                graph_degree=degree,
            )
            gaps.append(gap)

        # Heapify as max-priority
        self.queue = gaps
        heapq.heapify(self.queue)
        return self.queue

    def push_gap(self, gap: KnowledgeGap) -> None:
        """Push a knowledge gap onto the priority queue."""
        heapq.heappush(self.queue, gap)

    def pop_highest_gap(self) -> Optional[KnowledgeGap]:
        """Pop the most urgent knowledge gap to investigate."""
        if not self.queue:
            self.refresh_gaps()
        if self.queue:
            return heapq.heappop(self.queue)
        return None

    def peek_top_gaps(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """Peek at top prioritized gaps without popping."""
        if not self.queue:
            self.refresh_gaps()
        sorted_gaps = sorted(self.queue, key=lambda g: g.score, reverse=True)
        return [g.to_dict() for g in sorted_gaps[:top_k]]
