"""
db/models.py – SQLAlchemy ORM model for outreach history.
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from db.database import Base


class User(Base):
    """Stores app users for authentication and personalization."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    google_email = Column(String(255), nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "google_email": self.google_email,
            "google_connected": bool(self.google_refresh_token),
            "google_connected_at": self.google_connected_at.isoformat() if self.google_connected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OutreachRecord(Base):
    """Stores every agent run: signals, insights, email, and send status."""

    __tablename__ = "outreach_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)

    # ── Input ──────────────────────────────────────────────────
    company = Column(String(255), nullable=False, index=True)
    icp = Column(Text, nullable=True)

    # ── Signals ────────────────────────────────────────────────
    signals = Column(JSON, nullable=True)          # Raw Serper signals
    cleaned_signals = Column(JSON, nullable=True)  # Structured signals

    # ── Analysis ───────────────────────────────────────────────
    insights = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    score_breakdown = Column(JSON, nullable=True)
    strategy = Column(Text, nullable=True)

    # ── Email ──────────────────────────────────────────────────
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    sent_to = Column(String(255), nullable=True)   # Recipient email address

    # ── Execution ──────────────────────────────────────────────
    status = Column(String(50), nullable=False, default="pending")
    # Values: pending | email_ready | sent | failed | stopped
    error_msg = Column(Text, nullable=True)

    # ── Timestamps ─────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    # ── Optional tracking ──────────────────────────────────────
    open_tracked = Column(Boolean, nullable=True)
    reply_received = Column(Boolean, nullable=True)

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        return {
            "id": self.id,
            "company": self.company,
            "user_id": self.user_id,
            "icp": self.icp,
            "signals": self.signals,
            "cleaned_signals": self.cleaned_signals,
            "insights": self.insights,
            "score": self.score,
            "score_breakdown": self.score_breakdown,
            "strategy": self.strategy,
            "email_subject": self.email_subject,
            "email_body": self.email_body,
            "sent_to": self.sent_to,
            "status": self.status,
            "error_msg": self.error_msg,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "open_tracked": self.open_tracked,
            "reply_received": self.reply_received,
        }
