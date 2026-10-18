"""NetworkX Knowledge Graph engine for ORBIT."""

from typing import Dict, Any, List, Optional
import networkx as nx

from src.knowledge.db import (
    get_all_entities_and_relations,
    upsert_entity,
    insert_relation,
    DEFAULT_DB_PATH,
)


class KnowledgeGraphEngine:
    """
    In-memory NetworkX directed graph engine backed by SQLite persistent storage.
    Supports Cytoscape.js export, ego-network neighborhoods, and centrality ranking.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.graph = nx.DiGraph()

    def sync_from_db(self) -> nx.DiGraph:
        """Load all entities and relations from SQLite into NetworkX DiGraph."""
        data = get_all_entities_and_relations(self.db_path)
        self.graph.clear()

        # Add nodes
        for node in data["nodes"]:
            self.graph.add_node(
                node["canonical_name"],
                id=node["id"],
                canonical_name=node["canonical_name"],
                entity_type=node["entity_type"],
                created_at=node["created_at"],
            )

        # Add directed edges
        for edge in data["edges"]:
            self.graph.add_edge(
                edge["source_name"],
                edge["target_name"],
                id=edge["id"],
                relation_type=edge["relation_type"],
                confidence=edge["confidence"],
                source_id=edge["source_id"],
                source_title=edge["source_title"],
                source_url=edge["source_url"],
                source_date=edge["source_date"],
            )

        return self.graph

    def get_summary(self) -> Dict[str, Any]:
        """Return topological metrics of the knowledge graph."""
        self.sync_from_db()
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "is_connected": nx.is_weakly_connected(self.graph) if len(self.graph) > 0 else False,
            "density": nx.density(self.graph),
        }

    def to_cytoscape(self, target_graph: Optional[nx.DiGraph] = None) -> Dict[str, Any]:
        """
        Export graph in Cytoscape.js format:
        { "elements": { "nodes": [{data: {...}}], "edges": [{data: {...}}] } }
        """
        g = target_graph if target_graph is not None else self.sync_from_db()

        nodes = []
        for n, attrs in g.nodes(data=True):
            deg = g.degree(n)
            nodes.append({
                "data": {
                    "id": n,
                    "label": n,
                    "entity_type": attrs.get("entity_type", "Entity"),
                    "degree": deg,
                }
            })

        edges = []
        for u, v, attrs in g.edges(data=True):
            edges.append({
                "data": {
                    "id": f"{u}->{v}:{attrs.get('relation_type', 'mentions')}",
                    "source": u,
                    "target": v,
                    "label": attrs.get("relation_type", "mentions"),
                    "confidence": attrs.get("confidence", 1.0),
                    "source_title": attrs.get("source_title", ""),
                    "source_url": attrs.get("source_url", ""),
                    "source_date": attrs.get("source_date", ""),
                    "source_id": attrs.get("source_id"),
                }
            })

        return {"elements": {"nodes": nodes, "edges": edges}}

    def get_neighborhood(self, entity_name: str, radius: int = 1) -> Dict[str, Any]:
        """Extract ego-subgraph centered around an entity."""
        self.sync_from_db()
        if entity_name not in self.graph:
            return {"elements": {"nodes": [], "edges": []}}

        subgraph_nodes = set([entity_name])
        current_layer = set([entity_name])

        for _ in range(radius):
            next_layer = set()
            for node in current_layer:
                next_layer.update(self.graph.successors(node))
                next_layer.update(self.graph.predecessors(node))
            subgraph_nodes.update(next_layer)
            current_layer = next_layer

        subgraph = self.graph.subgraph(subgraph_nodes)
        return self.to_cytoscape(target_graph=subgraph)

    def get_key_entities(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """Return top entities ranked by degree centrality."""
        self.sync_from_db()
        if not self.graph:
            return []

        centrality = nx.degree_centrality(self.graph)
        sorted_entities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for name, score in sorted_entities:
            node_data = self.graph.nodes[name]
            results.append({
                "name": name,
                "type": node_data.get("entity_type", "Entity"),
                "degree": self.graph.degree(name),
                "centrality": round(score, 4),
            })
        return results
