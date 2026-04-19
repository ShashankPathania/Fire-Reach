"""
agent/nodes/clean_signals.py – Node 2: Validate and normalize raw signals.

Ensures:
- All confidence values are clamped to [0.0, 1.0]
- Required fields exist with sensible defaults
- Malformed signal types are dropped gracefully
"""

import logging
from typing import Any, Dict

from agent.state import AgentState

logger = logging.getLogger(__name__)

# Required fields per signal type (with defaults)
_SIGNAL_SCHEMA: Dict[str, Dict[str, Any]] = {
    "funding": {
        "status": "unknown",
        "amount": "undisclosed",
        "round": "undisclosed",
        "confidence": 0.5,
    },
    "hiring": {
        "open_roles": None,
        "departments": [],
        "growth_rate": "unknown",
        "confidence": 0.5,
    },
    "expansion": {
        "regions": [],
        "description": "",
        "confidence": 0.5,
    },
    "tech_stack": {
        "identified": [],
        "changes": None,
        "confidence": 0.5,
    },
    "leadership": {
        "description": "",
        "confidence": 0.5,
    },
    "news": {
        "headline": "",
        "snippet": "",
        "confidence": 0.5,
    },
}


async def clean_signals_node(state: AgentState) -> dict:
    raw_signals: Dict[str, Any] = state.get("signals") or {}
    logger.info("[clean_signals] Cleaning %d signal types", len(raw_signals))

    if not raw_signals:
        logger.warning("[clean_signals] No signals to clean — continuing with empty set")
        return {"cleaned_signals": {}}

    cleaned: Dict[str, Any] = {}

    for signal_type, data in raw_signals.items():
        if not isinstance(data, dict):
            logger.debug("[clean_signals] Dropping non-dict signal: %s", signal_type)
            continue

        schema = _SIGNAL_SCHEMA.get(signal_type, {})
        signal_clean = dict(schema)          # Start with defaults
        signal_clean.update(data)            # Override with real data

        # Clamp confidence to [0, 1]
        raw_conf = signal_clean.get("confidence", 0.5)
        try:
            signal_clean["confidence"] = round(max(0.0, min(1.0, float(raw_conf))), 3)
        except (TypeError, ValueError):
            signal_clean["confidence"] = 0.5

        cleaned[signal_type] = signal_clean

    logger.info("[clean_signals] Cleaned signals: %s", list(cleaned.keys()))
    return {"cleaned_signals": cleaned}
