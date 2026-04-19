"""
services/memory.py – Async database service wrapping all outreach history operations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from db.models import OutreachRecord

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Handles all database persistence for outreach records.
    Uses async SQLAlchemy sessions.
    """

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    # ──────────────────────────────────────────────────────────────────────────
    # Write
    # ──────────────────────────────────────────────────────────────────────────

    async def save_outreach(self, state: Dict[str, Any]) -> int:
        """
        Persist an agent run to the database.
        Returns the new record ID.
        """
        async with self._session_factory() as session:
            record = OutreachRecord(
                user_id=state.get("user_id"),
                company=state.get("company", ""),
                icp=state.get("icp", ""),
                signals=state.get("signals"),
                cleaned_signals=state.get("cleaned_signals"),
                insights=state.get("insights", ""),
                score=state.get("score", 0.0),
                score_breakdown=state.get("score_breakdown"),
                strategy=state.get("strategy", ""),
                email_subject=state.get("email_subject", ""),
                email_body=state.get("email", ""),
                sent_to=state.get("recipient_email"),
                status=state.get("status", "pending"),
                error_msg=state.get("error", "") or None,
                created_at=datetime.now(timezone.utc),
                sent_at=datetime.now(timezone.utc) if state.get("email_sent") else None,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.info("Saved outreach record id=%d for '%s'", record.id, record.company)
            return record.id

    async def update_status(self, record_id: int, status: str, error: str = None) -> None:
        """Update status on an existing record."""
        async with self._session_factory() as session:
            record = await session.get(OutreachRecord, record_id)
            if record:
                record.status = status
                if error:
                    record.error_msg = error
                await session.commit()

    # ──────────────────────────────────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────────────────────────────────

    async def has_recent_outreach(self, company: str, days: int = 30, user_id: Optional[int] = None) -> bool:
        """Return True if we've already reached out to this company within `days` days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with self._session_factory() as session:
            stmt = select(OutreachRecord).where(
                OutreachRecord.company.ilike(company),
                OutreachRecord.created_at >= cutoff,
                OutreachRecord.status.in_(["complete", "sent", "email_ready"]),
            )
            if user_id:
                stmt = stmt.where(OutreachRecord.user_id == user_id)
            result = await session.execute(stmt)
            record = result.scalars().first()
            return record is not None

    async def get_history(
        self,
        user_id: Optional[int] = None,
        company: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict]:
        """Fetch outreach history, optionally filtered by company name."""
        async with self._session_factory() as session:
            stmt = select(OutreachRecord).order_by(desc(OutreachRecord.created_at))
            if user_id:
                stmt = stmt.where(OutreachRecord.user_id == user_id)
            if company:
                stmt = stmt.where(OutreachRecord.company.ilike(f"%{company}%"))
            stmt = stmt.limit(limit).offset(offset)
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [r.to_dict() for r in records]

    async def get_record(self, record_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
        """Fetch a single record by ID."""
        async with self._session_factory() as session:
            record = await session.get(OutreachRecord, record_id)
            if record and user_id and record.user_id != user_id:
                return None
            return record.to_dict() if record else None

    async def get_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Return summary stats for the dashboard."""
        async with self._session_factory() as session:
            stmt = select(OutreachRecord)
            if user_id:
                stmt = stmt.where(OutreachRecord.user_id == user_id)
            all_result = await session.execute(stmt)
            all_records = all_result.scalars().all()

            total = len(all_records)
            sent = sum(1 for r in all_records if r.status in ("sent", "email_ready", "complete"))
            stopped = sum(1 for r in all_records if r.status == "stopped")
            avg_score = (
                sum(r.score or 0 for r in all_records) / total if total > 0 else 0.0
            )
            companies = list({r.company for r in all_records})

            return {
                "total_runs": total,
                "emails_ready": sent,
                "low_score_stopped": stopped,
                "avg_score": round(avg_score, 3),
                "unique_companies": len(companies),
            }

    async def delete_record(self, record_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a record by ID. Returns True if deleted."""
        async with self._session_factory() as session:
            record = await session.get(OutreachRecord, record_id)
            if record:
                if user_id and record.user_id != user_id:
                    return False
                await session.delete(record)
                await session.commit()
                return True
            return False
