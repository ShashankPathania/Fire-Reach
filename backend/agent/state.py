"""
agent/state.py – TypedDict state that flows through all LangGraph nodes.

Using TypedDict (not dataclass) because LangGraph's StateGraph requires
dict-like state for its internal merging and checkpoint mechanics.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────
    company: str                          # Company name to analyze
    icp: str                              # Ideal Customer Profile description

    # ── Signal Ingestion ───────────────────────────────────────────
    signals: Dict[str, Any]              # Raw structured signals from Serper
    cleaned_signals: Dict[str, Any]      # Validated + normalized signals

    # ── LLM Analysis ──────────────────────────────────────────────
    insights: str                         # 2-paragraph account brief from LLM

    # ── Scoring ────────────────────────────────────────────────────
    score: float                          # Composite opportunity score 0.0–1.0
    score_breakdown: Dict[str, float]    # Per-signal breakdown

    # ── Strategy ──────────────────────────────────────────────────
    strategy: str                         # Single outreach angle chosen by LLM

    # ── Email ──────────────────────────────────────────────────────
    email: str                            # Generated email body
    email_subject: str                    # Generated subject line
    contact_candidates: List[Dict[str, Any]]  # Discovered contacts from search
    target_titles: List[str]              # Preferred decision-maker titles
    contacts_found: int                   # Number of discovered contacts
    sender_name: str                      # Authenticated sender display name
    sender_contact_email: str             # Authenticated app user email for contact
    user_id: int                          # Authenticated user id
    sender_google_email: str              # Connected Google sender email
    sender_google_refresh_token: str      # Connected Google refresh token

    # ── Execution Flags ────────────────────────────────────────────
    send_email_flag: bool                 # Whether to actually send (set by API)
    recipient_email: Optional[str]        # Target email address
    score_threshold: float                # Runtime score threshold from config

    # ── Status ─────────────────────────────────────────────────────
    status: str                           # pending | processing | email_ready | complete | failed | stopped
    error: str                            # Error message if status == failed

    # ── Metadata ───────────────────────────────────────────────────
    record_id: int                        # DB ID of this outreach record
    created_at: str                       # ISO timestamp of run start
    email_sent: bool                      # Whether email was actually sent
    email_send_result: Dict[str, Any]    # Raw result from email service
