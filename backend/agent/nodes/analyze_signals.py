"""
agent/nodes/analyze_signals.py – Node 3: LLM analysis of signals vs ICP.

Generates a 2-paragraph account brief:
  P1: What is happening at the company? (factual, signal-grounded)
  P2: What pain points exist? How does it align to the ICP?
"""

import json
import logging

from agent.state import AgentState
from services.llm import LLMService

logger = logging.getLogger(__name__)


def make_analyze_signals_node(llm_service: LLMService):
    """Factory returning a node function with llm_service injected."""

    async def analyze_signals_node(state: AgentState) -> dict:
        company = state.get("company", "Unknown")
        icp = state.get("icp", "")
        cleaned_signals = state.get("cleaned_signals") or {}

        logger.info("[analyze_signals] Analyzing %d signals for %s", len(cleaned_signals), company)

        if not cleaned_signals:
            logger.warning("[analyze_signals] No signals — generating minimal insight")
            return {
                "insights": (
                    f"{company} has limited public signal data available at this time. "
                    "Consider refreshing or checking the company name.\n\n"
                    "Without strong signal data, alignment to the ICP cannot be confidently assessed."
                )
            }

        signals_json = json.dumps(cleaned_signals, indent=2, default=str)

        prompt = f"""You are a B2B GTM strategist. Analyze the following real signals and write a concise account brief.

Company: {company}

Signals (real data only):
{signals_json}

Our ICP (Ideal Customer Profile):
{icp}

Task: Write exactly 2 paragraphs:

Paragraph 1: What is happening at {company}? Describe the situation using the signals above. Be specific — mention amounts, departments, regions, technologies, or any concrete details found in the signals. Do NOT add assumptions.

Paragraph 2: Based on these signals, what pain points or opportunities exist that align with our ICP? Connect specific signals to business challenges our solution could address.

CONSTRAINTS:
- ONLY reference what is in the signals provided above
- NO hallucination or guessing
- Be crisp and analytical, not sales-y
- Each paragraph should be 3-5 sentences

Output format — write only the two paragraphs, no headers or labels:
"""

        try:
            raw = await llm_service.generate(prompt, max_tokens=512)
            insights = raw.strip()
            logger.info("[analyze_signals] Generated %d char insight", len(insights))
            return {"insights": insights}
        except Exception as exc:
            logger.error("[analyze_signals] LLM failed: %s", exc)
            return {
                "insights": (
                    f"Signal analysis could not be completed (LLM error: {exc}). "
                    "Proceeding with raw signal data."
                )
            }

    return analyze_signals_node
