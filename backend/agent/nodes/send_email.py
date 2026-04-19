"""
agent/nodes/send_email.py – Node 7: Execute email sending (optional).

By default this node marks the email as ready but does NOT send.
Actual sending is triggered by the /run-agent endpoint when send_email=true.
This keeps the agent graph stateless with respect to external I/O.
"""

import logging

from agent.state import AgentState

logger = logging.getLogger(__name__)


async def send_email_node(state: AgentState) -> dict:
    """
    Mark email as ready for sending.

    Actual delivery is handled by the FastAPI endpoint after the graph
    completes, so this node simply validates the email was generated and
    sets the status accordingly.
    """
    email_body = state.get("email", "").strip()
    email_subject = state.get("email_subject", "").strip()

    if not email_body or not email_subject:
        logger.warning("[send_email] Email content missing — generation may have failed")
        return {
            "status": "failed",
            "error": "Email generation produced empty content.",
        }

    word_count = len(email_body.split())
    logger.info(
        "[send_email] Email ready: '%s' (%d words)", email_subject[:60], word_count
    )

    return {
        "status": "email_ready",
        "email_sent": False,  # Will be set to True by the API after actual sending
    }
