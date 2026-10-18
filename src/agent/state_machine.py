"""ORBIT Autonomous 6-Step State Machine."""

import datetime
import logging
from enum import Enum
from typing import Dict, Any, Optional

from src.discovery.collector import run_collection_cycle
from src.semantic.pipeline import run_semantic_pipeline
from src.knowledge.pipeline import run_knowledge_pipeline
from src.knowledge.db import DEFAULT_DB_PATH
from src.agent.prioritization import PriorityQueueEngine, KnowledgeGap
from src.agent.investigation import AutonomousInvestigator

logger = logging.getLogger("orbit.agent")


class AgentState(str, Enum):
    DISCOVER = "DISCOVER"
    UNDERSTAND = "UNDERSTAND"
    CONNECT = "CONNECT"
    RANK = "RANK"
    INVESTIGATE = "INVESTIGATE"
    UPDATE = "UPDATE"
    IDLE = "IDLE"


class OrbitAutonomousAgent:
    """
    6-step state machine:
    DISCOVER -> UNDERSTAND -> CONNECT -> RANK -> INVESTIGATE -> UPDATE -> IDLE
    """

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        query_budget: int = 15,
        circuit_breaker_limit: int = 3,
    ):
        self.db_path = db_path
        self.current_state = AgentState.IDLE
        self.priority_queue = PriorityQueueEngine(db_path=db_path)
        self.investigator = AutonomousInvestigator(
            db_path=db_path,
            max_budget=query_budget,
            circuit_breaker_limit=circuit_breaker_limit,
        )
        self.history: list = []
        self.last_run_at: Optional[str] = None
        self.cycle_count = 0

    def step_cycle(self) -> Dict[str, Any]:
        """Execute one complete 6-stage autonomous cycle."""
        self.cycle_count += 1
        cycle_start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cycle_log = {"cycle": self.cycle_count, "started_at": cycle_start}

        try:
            # 1. DISCOVER: Baseline ingestion pass
            self.current_state = AgentState.DISCOVER
            logger.info(f"Cycle {self.cycle_count} -> [01 DISCOVER]")
            discover_stats = run_collection_cycle(max_items_per_feed=5, db_path=self.db_path)
            cycle_log["discover"] = discover_stats

            # 2. UNDERSTAND: Text normalization & deduplication
            self.current_state = AgentState.UNDERSTAND
            logger.info(f"Cycle {self.cycle_count} -> [02 UNDERSTAND]")
            cycle_log["understand"] = {"cleaned": discover_stats.get("new_items_ingested", 0)}

            # 3. CONNECT: Knowledge Graph extraction
            self.current_state = AgentState.CONNECT
            logger.info(f"Cycle {self.cycle_count} -> [03 CONNECT]")
            graph_stats = run_knowledge_pipeline(limit=500, db_path=self.db_path)
            cycle_log["connect"] = graph_stats

            # 4. RANK: Topic clustering & novelty scoring
            self.current_state = AgentState.RANK
            logger.info(f"Cycle {self.cycle_count} -> [04 RANK]")
            semantic_stats = run_semantic_pipeline(limit=500, db_path=self.db_path)
            cycle_log["rank"] = semantic_stats

            # 5. INVESTIGATE: Resolve prioritized knowledge gaps
            self.current_state = AgentState.INVESTIGATE
            logger.info(f"Cycle {self.cycle_count} -> [05 INVESTIGATE]")
            self.priority_queue.refresh_gaps()
            top_gap = self.priority_queue.pop_highest_gap()
            if top_gap:
                logger.info(f"Investigating knowledge gap: '{top_gap.topic_title}' (priority={top_gap.score})")
                investigate_res = self.investigator.investigate_gap(top_gap, max_queries=2)
                cycle_log["investigate"] = investigate_res
            else:
                cycle_log["investigate"] = {"status": "no_active_gaps", "new_sources_found": 0}

            # 6. UPDATE: Revise graph and clusters with new investigation findings
            self.current_state = AgentState.UPDATE
            logger.info(f"Cycle {self.cycle_count} -> [06 UPDATE]")
            if cycle_log["investigate"].get("new_sources_found", 0) > 0:
                run_knowledge_pipeline(limit=500, db_path=self.db_path)
                run_semantic_pipeline(limit=500, db_path=self.db_path)
            cycle_log["update"] = {"status": "synchronized"}

            self.current_state = AgentState.IDLE
            self.last_run_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cycle_log["completed_at"] = self.last_run_at
            self.history.append(cycle_log)
            return cycle_log

        except Exception as e:
            self.current_state = AgentState.IDLE
            logger.error(f"Error during autonomous state machine cycle: {e}")
            cycle_log["error"] = str(e)
            return cycle_log

    def get_status(self) -> Dict[str, Any]:
        """Return agent status, current state, active gaps, and budget."""
        top_gaps = self.priority_queue.peek_top_gaps(top_k=3)
        return {
            "current_state": self.current_state.value,
            "cycles_completed": self.cycle_count,
            "last_run_at": self.last_run_at,
            "budget_spent": self.investigator.queries_executed,
            "budget_limit": self.investigator.max_budget,
            "circuit_breaker_tripped": (
                self.investigator.consecutive_empty_cycles >= self.investigator.circuit_breaker_limit
            ),
            "top_knowledge_gaps": top_gaps,
        }
