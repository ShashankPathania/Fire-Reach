"""
agent/nodes/find_contact.py – Discover likely prospect email contacts.

Uses ContactDiscoveryService (Hunter/Apollo) with fallback support.
"""

import logging

from agent.state import AgentState
from services.contact_discovery import ContactDiscoveryService

logger = logging.getLogger(__name__)


def make_find_contact_node(contact_discovery_service: ContactDiscoveryService):
    async def find_contact_node(state: AgentState) -> dict:
        company = (state.get("company") or "").strip()
        provided_recipient = (state.get("recipient_email") or "").strip()
        target_titles = state.get("target_titles") or [
            "VP Engineering",
            "CTO",
            "Engineering Manager",
        ]

        if not company:
            return {}

        # Respect user-provided recipient over auto-discovery.
        if provided_recipient:
            return {
                "contact_candidates": [{"email": provided_recipient, "source": "user_input"}],
                "recipient_email": provided_recipient,
            }

        contacts = await contact_discovery_service.find_contacts(
            company=company,
            target_titles=target_titles,
            limit=5,
        )
        chosen = contacts[0]["email"] if contacts else None
        logger.info(
            "[find_contact] %s → %d contacts (%s)",
            company,
            len(contacts),
            chosen or "none",
        )
        return {
            "contact_candidates": contacts,
            "contacts_found": len(contacts),
            "recipient_email": chosen,
        }

    return find_contact_node
