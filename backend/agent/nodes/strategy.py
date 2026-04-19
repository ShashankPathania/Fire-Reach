"""
agent/nodes/strategy.py – Node 5: LLM identifies the single strongest outreach angle.
"""

import json
import logging
import re

from agent.state import AgentState
from services.llm import LLMService

logger = logging.getLogger(__name__)

STRATEGY_OPTIONS = [
    "Scaling engineering infrastructure",
    "Accelerating hiring growth",
    "Expanding into new markets",
    "Adopting new tech stack",
    "Cost optimization",
]


def make_strategy_node(llm_service: LLMService):
    """Factory returning a node function with llm_service injected."""

    async def strategy_node(state: AgentState) -> dict:
        company = state.get("company", "Unknown")
        insights = state.get("insights", "")
        icp = state.get("icp", "")
        cleaned_signals = state.get("cleaned_signals") or {}

        logger.info("[strategy] Identifying outreach angle for %s", company)

        options_str = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(STRATEGY_OPTIONS))
        signals_summary = _summarize_signals(cleaned_signals)

        prompt = f"""You are a B2B outreach strategist. Based on the company signals and account brief below, identify the SINGLE strongest outreach angle.

Company: {company}
ICP: {icp}
Signals summary: {signals_summary}
Account brief:
{insights}

Available strategies:
{options_str}

Instructions:
- Choose the ONE most relevant strategy from the list above
- Write ONE sentence explaining WHY it's the best angle based on the signals
- Be specific — reference a signal if possible

Output format (respond ONLY with this JSON, nothing else):
{{"angle": "<exact strategy name from list>", "reason": "<one sentence why>"}}
"""

        strategy_str = ""
        reason_str = ""

        try:
            raw = await llm_service.generate(prompt, max_tokens=150)
            raw = raw.strip()

            # Try JSON parse first
            json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                strategy_str = parsed.get("angle", "")
                reason_str = parsed.get("reason", "")

            # Fallback: extract from plain text
            if not strategy_str:
                for option in STRATEGY_OPTIONS:
                    if option.lower() in raw.lower():
                        strategy_str = option
                        break

            if not strategy_str:
                strategy_str = STRATEGY_OPTIONS[0]  # Default

            strategy = f"{strategy_str} — {reason_str}" if reason_str else strategy_str
            logger.info("[strategy] Chosen angle: %s", strategy_str)
            return {"strategy": strategy}

        except Exception as exc:
            logger.error("[strategy] LLM failed: %s", exc)
            # Fallback: pick based on strongest signal
            fallback = _fallback_strategy(cleaned_signals)
            return {"strategy": fallback}

    return strategy_node


def _summarize_signals(signals: dict) -> str:
    parts = []
    if "funding" in signals:
        amt = signals["funding"].get("amount", "undisclosed")
        parts.append(f"Funding: {amt}")
    if "hiring" in signals:
        roles = signals["hiring"].get("open_roles")
        depts = ", ".join(signals["hiring"].get("departments", []))
        parts.append(f"Hiring: {roles or 'active'} roles in {depts or 'various departments'}")
    if "expansion" in signals:
        regions = ", ".join(signals["expansion"].get("regions", []))
        parts.append(f"Expanding into: {regions or 'new markets'}")
    if "tech_stack" in signals:
        tech = ", ".join(signals["tech_stack"].get("identified", [])[:3])
        parts.append(f"Tech: {tech}")
    return "; ".join(parts) if parts else "Limited signals available"


def _fallback_strategy(signals: dict) -> str:
    if "hiring" in signals:
        return "Accelerating hiring growth — company shows active recruiting signals"
    if "funding" in signals:
        return "Scaling engineering infrastructure — recent funding enables investment"
    if "expansion" in signals:
        return "Expanding into new markets — geographic growth signals detected"
    if "tech_stack" in signals:
        return "Adopting new tech stack — technology modernization in progress"
    return "Cost optimization — efficient scaling for the company's current stage"
