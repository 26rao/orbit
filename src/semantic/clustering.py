"""Topic clustering and novelty scoring engine."""

import math
import datetime
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize

from src.semantic.embeddings import SemanticEmbedder


class TopicClusterer:
    """
    Groups discoveries into thematic clusters using Agglomerative Clustering on semantic embeddings.
    Extracts representative centroids and computes cluster-relative novelty scores.
    """

    def __init__(self, distance_threshold: float = 0.92, decay_rate: float = 0.05):
        """
        distance_threshold: maximum cosine distance for items to merge into the same cluster.
        decay_rate: lambda parameter for exponential recency decay (per day).
        """
        self.distance_threshold = distance_threshold
        self.decay_rate = decay_rate
        self.embedder = SemanticEmbedder()
        self.cluster_centroids: Dict[int, np.ndarray] = {}
        self.cluster_metadata: Dict[int, Dict[str, Any]] = {}

    def cluster_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster discovery items.
        Returns items with 'cluster_id' and 'novelty_score' added.
        """
        if not items:
            return []

        if len(items) == 1:
            item = dict(items[0])
            item["cluster_id"] = 0
            item["novelty_score"] = 1.0
            return [item]

        # Combine title + summary for semantic density
        texts = [f"{it.get('title', '')}. {it.get('summary', '')}" for it in items]
        embeddings = self.embedder.fit_transform(texts)

        # Hierarchical agglomerative clustering with cosine distance
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=self.distance_threshold,
            metric="cosine",
            linkage="average",
        )
        labels = clustering.fit_predict(embeddings)

        # Calculate centroids and cluster metadata
        unique_labels = set(labels)
        self.cluster_centroids.clear()
        self.cluster_metadata.clear()

        for label in unique_labels:
            indices = [i for i, lbl in enumerate(labels) if lbl == label]
            cluster_vecs = embeddings[indices]
            centroid = normalize(np.mean(cluster_vecs, axis=0, keepdims=True), norm="l2")[0]
            self.cluster_centroids[label] = centroid

            # Cluster label from highest-degree or shortest title
            cluster_items = [items[i] for i in indices]
            rep_title = min(cluster_items, key=lambda x: len(x.get("title", ""))).get("title", f"Topic #{label}")
            
            self.cluster_metadata[label] = {
                "id": int(label),
                "label": rep_title,
                "size": len(indices),
                "source_names": list(set(it.get("source_name", "") for it in cluster_items)),
                "latest_update": max((it.get("published") or it.get("fetched_at", "") for it in cluster_items), default=""),
            }

        # Assign cluster_id and novelty score to items
        now = datetime.datetime.now(datetime.timezone.utc)
        results = []
        for i, item in enumerate(items):
            item_copy = dict(item)
            c_id = int(labels[i])
            item_copy["cluster_id"] = c_id

            # Novelty: 1 - max similarity to other clusters
            vec = embeddings[i]
            other_centroids = [
                (lbl, cent) for lbl, cent in self.cluster_centroids.items() if lbl != c_id
            ]

            if not other_centroids:
                # Sole cluster
                item_copy["novelty_score"] = 0.95
            else:
                max_sim = 0.0
                for other_lbl, cent in other_centroids:
                    sim = float(np.dot(vec, cent))
                    # Recency decay based on cluster age
                    pub_str = self.cluster_metadata[other_lbl].get("latest_update", "")
                    decay = 1.0
                    if pub_str:
                        try:
                            # Parse ISO string
                            dt = datetime.datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                            days_old = max(0.0, (now - dt).total_seconds() / 86400.0)
                            decay = math.exp(-self.decay_rate * days_old)
                        except Exception:
                            decay = 1.0
                    effective_sim = sim * decay
                    if effective_sim > max_sim:
                        max_sim = effective_sim

                item_copy["novelty_score"] = round(max(0.0, min(1.0, 1.0 - max_sim)), 3)

            results.append(item_copy)

        return results

    def get_topics_summary(self) -> List[Dict[str, Any]]:
        """Return structured summary of discovered topic clusters."""
        sorted_topics = sorted(
            self.cluster_metadata.values(),
            key=lambda x: x["size"],
            reverse=True,
        )
        return sorted_topics
