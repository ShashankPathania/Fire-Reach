"""
agent/graph.py – LangGraph StateGraph definition for FireReach AI.

Graph Flow:
  START
    → fetch_signals      (Serper API)
    → find_contact       (recipient discovery)
    → clean_signals      (normalize)
    → analyze_signals    (LLM)
    → score_lead         (deterministic math)
    → [conditional]
       ├─ score < 0.5  → memory → END  (stopped)
       └─ score >= 0.5 → strategy → generate_email → send_email → memory → END
"""

import logging

from langgraph.graph import END, StateGraph

from agent.state import AgentState
from agent.nodes import (
    clean_signals_node,
    make_analyze_signals_node,
    make_fetch_signals_node,
    make_find_contact_node,
    make_generate_email_node,
    make_memory_node,
    make_strategy_node,
    score_lead_node,
    send_email_node,
    should_continue,
)
from services.serper import SerperService
from services.llm import LLMService
from services.memory import MemoryService
from services.contact_discovery import ContactDiscoveryService

logger = logging.getLogger(__name__)


def build_agent_graph(
    serper_service: SerperService,
    llm_service: LLMService,
    memory_service: MemoryService,
    contact_discovery_service: ContactDiscoveryService,
):
    """
    Compile and return the LangGraph agent.

    Services are injected via factory closures — no global state.
    """

    # ── Create bound node functions ─────────────────────────────────────────
    fetch_signals = make_fetch_signals_node(serper_service)
    find_contact = make_find_contact_node(contact_discovery_service)
    analyze_signals = make_analyze_signals_node(llm_service)
    strategy = make_strategy_node(llm_service)
    generate_email = make_generate_email_node(llm_service)
    memory = make_memory_node(memory_service)

    # ── Build graph ──────────────────────────────────────────────────────────
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("fetch_signals", fetch_signals)
    workflow.add_node("find_contact", find_contact)
    workflow.add_node("clean_signals", clean_signals_node)
    workflow.add_node("analyze_signals", analyze_signals)
    workflow.add_node("score_lead", score_lead_node)
    workflow.add_node("strategy", strategy)
    workflow.add_node("generate_email", generate_email)
    workflow.add_node("send_email", send_email_node)
    workflow.add_node("memory", memory)

    # Linear edges
    workflow.add_edge("fetch_signals", "clean_signals")
    workflow.add_edge("clean_signals", "analyze_signals")
    workflow.add_edge("analyze_signals", "score_lead")

    # Conditional branch on score
    workflow.add_conditional_edges(
        "score_lead",
        should_continue,
        {
            "continue": "find_contact",
            "stop": "memory",   # Low score → skip email, just log
        },
    )

    # High-score path
    workflow.add_edge("find_contact", "strategy")
    workflow.add_edge("strategy", "generate_email")
    workflow.add_edge("generate_email", "send_email")
    workflow.add_edge("send_email", "memory")

    # Terminal edge (both paths end here)
    workflow.add_edge("memory", END)

    # Entry point
    workflow.set_entry_point("fetch_signals")

    compiled = workflow.compile()
    logger.info("LangGraph agent compiled successfully (9 nodes)")
    return compiled
