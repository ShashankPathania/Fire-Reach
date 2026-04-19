"""
agent/nodes/__init__.py – Export all node factories + conditional functions.
"""

from agent.nodes.fetch_signals import make_fetch_signals_node
from agent.nodes.find_contact import make_find_contact_node
from agent.nodes.clean_signals import clean_signals_node
from agent.nodes.analyze_signals import make_analyze_signals_node
from agent.nodes.score_lead import score_lead_node, should_continue
from agent.nodes.strategy import make_strategy_node
from agent.nodes.generate_email import make_generate_email_node
from agent.nodes.send_email import send_email_node
from agent.nodes.memory import make_memory_node

__all__ = [
    "make_fetch_signals_node",
    "make_find_contact_node",
    "clean_signals_node",
    "make_analyze_signals_node",
    "score_lead_node",
    "should_continue",
    "make_strategy_node",
    "make_generate_email_node",
    "send_email_node",
    "make_memory_node",
]
