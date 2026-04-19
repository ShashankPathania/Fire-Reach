"""
agent/nodes/score_lead.py – Node 4: Deterministic opportunity scoring.

No LLM. Pure math. Score determines whether outreach proceeds.
"""

import logging

from agent.state import AgentState
from config import settings
from services.scoring import calculate_breakdown, explain_score, score_lead

logger = logging.getLogger(__name__)


async def score_lead_node(state: AgentState) -> dict:
    cleaned_signals = state.get("cleaned_signals") or {}
    company = state.get("company", "Unknown")

    score = score_lead(cleaned_signals)
    breakdown = calculate_breakdown(cleaned_signals)
    explanation = explain_score(score, breakdown)

    logger.info("[score_lead] %s → score=%.3f", company, score)
    logger.debug("[score_lead] Breakdown: %s", breakdown)

    return {
        "score": score,
        "score_breakdown": breakdown,
    }


def should_continue(state: AgentState) -> str:
    """
    Conditional edge: Decide whether to proceed with outreach.
    Returns 'continue' or 'stop'.
    """
    score = state.get("score", 0.0)
    threshold = state.get("score_threshold", settings.SCORE_THRESHOLD)

    if score >= threshold:
        logger.info("[should_continue] Score %.3f >= %.2f → CONTINUE", score, threshold)
        return "continue"
    else:
        logger.info("[should_continue] Score %.3f < %.2f → STOP", score, threshold)
        return "stop"
