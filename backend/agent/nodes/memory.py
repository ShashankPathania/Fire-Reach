"""
agent/nodes/memory.py – Node 8: Persist run to database + finalize state.

This is the terminal node for all paths (both continue and stop branches).
"""

import logging
from datetime import datetime, timezone

from agent.state import AgentState
from config import settings
from services.memory import MemoryService

logger = logging.getLogger(__name__)


def make_memory_node(memory_service: MemoryService):
    """Factory returning a node function with memory_service injected."""

    async def memory_node(state: AgentState) -> dict:
        company = state.get("company", "Unknown")
        score = state.get("score", 0.0)
        threshold = state.get("score_threshold", settings.SCORE_THRESHOLD)
        record_id = 0

        # Determine final status
        current_status = state.get("status", "pending")
        if current_status == "failed":
            final_status = "failed"
        elif score < threshold:
            final_status = "stopped"  # Low score path
        else:
            final_status = "complete"

        state_with_status = dict(state)
        state_with_status["status"] = final_status

        try:
            record_id = await memory_service.save_outreach(state_with_status)
            logger.info(
                "[memory] Saved run for '%s' as status='%s' (id=%d)",
                company, final_status, record_id
            )
        except Exception as exc:
            logger.error("[memory] Failed to save outreach record: %s", exc)
            # Don't fail the whole run just because DB save failed

        return {
            "status": final_status,
            "record_id": record_id or state.get("record_id", 0),
        }

    return memory_node
