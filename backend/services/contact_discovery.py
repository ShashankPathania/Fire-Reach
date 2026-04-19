"""
services/contact_discovery.py – Contact discovery via Hunter with fallback.
"""

import logging
from typing import Any, Dict, List

import httpx

from services.serper import SerperService

logger = logging.getLogger(__name__)


class ContactDiscoveryService:
    def __init__(
        self,
        hunter_api_key: str = "",
        serper_service: SerperService | None = None,
    ):
        self.hunter_api_key = (hunter_api_key or "").strip()
        self.serper_service = serper_service

    async def find_contacts(
        self,
        company: str,
        target_titles: List[str] | None = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        target_titles = target_titles or ["VP Engineering", "CTO", "Engineering Manager"]
        expanded_titles = self._expand_target_titles(target_titles)
        domain = await self._resolve_domain(company)
        contacts = []

        hunter_fetch_limit = max(5, min(10, limit * 2))
        hunter_contacts = await self._fetch_hunter_contacts(
            domain,
            expanded_titles,
            limit=hunter_fetch_limit,
        )
        if hunter_contacts:
            contacts.extend(hunter_contacts)

        if not contacts and self.serper_service:
            # Fallback keeps local workflow usable without paid keys.
            fallback = await self.serper_service.fetch_contact_candidates(company)
            contacts = [
                {
                    "name": "",
                    "title": "Unknown",
                    "email": row["email"],
                    "department": "Engineering",
                    "seniority": "unknown",
                    "confidence": 0.6,
                    "source": row.get("source", "serper"),
                }
                for row in fallback
            ]

        deduped = self._dedupe_contacts(contacts)
        ranked = self._rank_contacts(deduped, expanded_titles)
        return ranked[:limit]

    async def _fetch_hunter_contacts(
        self,
        domain: str,
        target_titles: List[str],
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        if not self.hunter_api_key:
            return []

        url = "https://api.hunter.io/v2/domain-search"
        params = {"domain": domain, "limit": limit, "api_key": self.hunter_api_key}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, params=params)
            response.raise_for_status()
        except Exception as exc:
            logger.warning(
                "Hunter lookup failed for %s (limit=%d): %s",
                domain,
                limit,
                exc.__class__.__name__,
            )
            return []

        data = response.json().get("data", {})
        rows = data.get("emails", []) or []
        contacts: List[Dict[str, Any]] = []

        for row in rows:
            title = (row.get("position") or "").strip()
            email = (row.get("value") or "").lower()
            is_generic = self._is_generic_inbox(email)
            first = (row.get("first_name") or "").strip()
            last = (row.get("last_name") or "").strip()
            full_name = f"{first} {last}".strip()
            confidence = float((row.get("confidence") or 0) / 100) if row.get("confidence") else 0.75
            contacts.append(
                {
                    "name": full_name,
                    "title": title or "Unknown",
                    "email": email,
                    "department": self._infer_department(title),
                    "seniority": self._infer_seniority(title),
                    "confidence": max(0.0, min(confidence, 1.0)),
                    "is_generic": is_generic,
                    "source": "hunter",
                }
            )
        contacts = [c for c in contacts if c.get("email")]
        person_contacts = [c for c in contacts if not c.get("is_generic")]
        return person_contacts or contacts

    async def _resolve_domain(self, company: str) -> str:
        normalized = company.lower().strip()
        if self._looks_like_domain(normalized):
            return normalized.removeprefix("www.")

        if self.serper_service:
            resolved = await self.serper_service.resolve_company_domain(company)
            if resolved:
                logger.info(
                    "Resolved domain for '%s' -> %s (confidence=%.2f)",
                    company,
                    resolved["domain"],
                    resolved["confidence"],
                )
                return resolved["domain"]

        slug = "".join(ch for ch in normalized if ch.isalnum())
        for suffix in (".ai", ".io", ".com"):
            if slug:
                return f"{slug}{suffix}"
        return f"{normalized}.com"

    def _looks_like_domain(self, value: str) -> bool:
        return "." in value and " " not in value and "/" not in value

    def _matches_title(self, title: str, target_titles: List[str]) -> bool:
        low = title.lower()
        return any(target.lower() in low for target in target_titles)

    def _expand_target_titles(self, target_titles: List[str]) -> List[str]:
        expanded = set(target_titles)
        expanded.update(
            {
                "Head of Engineering",
                "Founder",
                "Co-Founder",
                "CEO",
                "Chief Executive Officer",
                "Head of AI",
                "Technical Lead",
                "Lead Engineer",
            }
        )
        return list(expanded)

    def _is_founder_or_exec(self, title: str) -> bool:
        low = (title or "").lower()
        return any(token in low for token in ["founder", "co-founder", "ceo", "chief", "head of"])

    def _infer_department(self, title: str) -> str:
        low = (title or "").lower()
        if "eng" in low or "cto" in low or "developer" in low:
            return "Engineering"
        if "product" in low:
            return "Product"
        if "sales" in low:
            return "Sales"
        return "Other"

    def _infer_seniority(self, title: str) -> str:
        low = (title or "").lower()
        if any(x in low for x in ["cto", "vp", "chief", "head"]):
            return "executive"
        if any(x in low for x in ["manager", "lead", "senior"]):
            return "manager"
        return "individual_contributor"

    def _rank_contacts(self, contacts: List[Dict[str, Any]], target_titles: List[str]) -> List[Dict[str, Any]]:
        def _score(contact: Dict[str, Any]) -> float:
            score = float(contact.get("confidence", 0.0))
            title = (contact.get("title") or "").lower()
            if any(t.lower() in title for t in target_titles):
                score += 0.2
            if contact.get("seniority") == "executive":
                score += 0.2
            if contact.get("name"):
                score += 0.15
            if contact.get("is_generic"):
                score -= 0.35
            return score

        return sorted(contacts, key=_score, reverse=True)

    def _is_generic_inbox(self, email: str) -> bool:
        prefix = (email or "").split("@")[0].lower()
        generic_prefixes = {
            "sales",
            "hello",
            "contact",
            "support",
            "info",
            "team",
            "partners",
            "partnerships",
            "admin",
        }
        return prefix in generic_prefixes

    def _dedupe_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = {}
        for contact in contacts:
            email = (contact.get("email") or "").lower().strip()
            if not email:
                continue
            existing = seen.get(email)
            if not existing or contact.get("confidence", 0) > existing.get("confidence", 0):
                seen[email] = contact
        return list(seen.values())
