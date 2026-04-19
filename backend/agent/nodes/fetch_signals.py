"""
agent/nodes/fetch_signals.py – Node 1: Fetch real signals from Serper API.
"""

import logging
from datetime import datetime, timezone

from agent.state import AgentState
from services.serper import SerperService

logger = logging.getLogger(__name__)


def make_fetch_signals_node(serper_service: SerperService):
    """Factory returning a node function with the service injected."""

    async def fetch_signals_node(state: AgentState) -> dict:
        company = state.get("company", "").strip()
        logger.info("[fetch_signals] Fetching signals for: %s", company)

        if not company:
            return {
                "status": "failed",
                "error": "Company name is required.",
            }

        try:
            signals = await serper_service.fetch_company_signals(company)
            logger.info("[fetch_signals] Got %d signal types for %s", len(signals), company)
            return {
                "signals": signals,
                "status": "processing",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            logger.error("[fetch_signals] Failed for '%s': %s", company, exc)
            return {
                "signals": {},
                "status": "failed",
                "error": f"Signal fetch failed: {str(exc)}",
            }

    return fetch_signals_node
