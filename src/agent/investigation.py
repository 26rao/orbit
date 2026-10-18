"""Autonomous investigation engine: generates queries and searches for independent evidence."""

import urllib.parse
import re
import datetime
import logging
from typing import List, Dict, Any, Optional

from src.discovery.http_client import RobustHttpClient
from src.discovery.feed_parser import parse_feed_xml
from src.extraction.extractor import clean_html, compute_content_hash
from src.semantic.novelty import is_novel
from src.knowledge.db import insert_source, get_recent_titles, DEFAULT_DB_PATH
from src.agent.prioritization import KnowledgeGap

logger = logging.getLogger("orbit.investigator")


def generate_investigation_queries(topic_title: str) -> List[str]:
    """
    Generate 1 to 3 targeted follow-up search queries to verify claims and fill knowledge gaps.
    """
    # Extract core subject nouns/keywords
    cleaned = re.sub(r"[^\w\s\-]", "", topic_title).strip()
    words = [w for w in cleaned.split() if w.lower() not in [
        "the", "and", "for", "with", "from", "into", "over", "what", "how", "new", "demonstrates", "unveils"
    ]]
    core_subject = " ".join(words[:4]) if words else topic_title

    queries = [
        f"{core_subject} benchmark replication",
        f"{core_subject} independent evaluation",
        f"{core_subject} limitations comparison",
    ]
    return queries


class AutonomousInvestigator:
    """
    Executes autonomous targeted research investigations on prioritized knowledge gaps.
    Includes circuit breakers and query budget controls.
    """

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        max_budget: int = 20,
        circuit_breaker_limit: int = 3,
    ):
        self.db_path = db_path
        self.max_budget = max_budget
        self.queries_executed = 0
        self.circuit_breaker_limit = circuit_breaker_limit
        self.consecutive_empty_cycles = 0

    def investigate_gap(self, gap: KnowledgeGap, max_queries: int = 2) -> Dict[str, Any]:
        """
        Investigate a single knowledge gap by searching public research repositories.
        """
        if self.queries_executed >= self.max_budget:
            logger.warning("Investigation halted: Query budget exhausted.")
            return {"status": "budget_exhausted", "new_sources_found": 0}

        if self.consecutive_empty_cycles >= self.circuit_breaker_limit:
            logger.warning("Circuit breaker tripped: Multiple consecutive empty investigation cycles.")
            return {"status": "circuit_breaker_tripped", "new_sources_found": 0}

        queries = generate_investigation_queries(gap.topic_title)[:max_queries]
        new_sources_found = 0
        existing_titles = get_recent_titles(limit=500, db_path=self.db_path)

        with RobustHttpClient() as client:
            for q in queries:
                if self.queries_executed >= self.max_budget:
                    break

                self.queries_executed += 1
                encoded_q = urllib.parse.quote(q)
                url = f"https://export.arxiv.org/api/query?search_query=all:{encoded_q}&sortBy=relevance&sortOrder=descending&max_results=3"

                logger.info(f"Autonomous search [{self.queries_executed}/{self.max_budget}]: {q}")
                resp = client.get(url)
                if not resp:
                    continue

                items = parse_feed_xml(resp.text, default_source_name="Autonomous Investigation")
                for it in items:
                    title = it["title"]
                    # Novelty check
                    novel, sim, match = is_novel(title, existing_titles, similarity_threshold=0.88)
                    if not novel:
                        continue

                    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    summary = it.get("summary", "")
                    content_hash = compute_content_hash(f"{title} {summary}")

                    row_id = insert_source(
                        url=it["url"],
                        title=title,
                        published=it.get("published", now_iso),
                        raw_text=summary,
                        summary=summary[:350],
                        fetched_at=now_iso,
                        source_name="Autonomous Search",
                        content_hash=content_hash,
                        status="investigated",
                        db_path=self.db_path,
                    )
                    if row_id:
                        new_sources_found += 1
                        existing_titles.append(title)
                        logger.info(f"  [+] Found new evidence: {title[:60]}")

        if new_sources_found == 0:
            self.consecutive_empty_cycles += 1
        else:
            self.consecutive_empty_cycles = 0

        return {
            "status": "completed",
            "gap_investigated": gap.topic_title,
            "queries_executed": len(queries),
            "new_sources_found": new_sources_found,
            "total_budget_spent": self.queries_executed,
            "consecutive_empty_cycles": self.consecutive_empty_cycles,
        }
