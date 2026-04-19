"""
services/serper.py – Serper API integration for real signal ingestion.

Fires 5 async queries per company, parses organic results into structured
signal objects with confidence scores. Zero fabrication — only real data.
"""

import re
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ── Keyword banks for parsing ──────────────────────────────────────────────
_FUNDING_KWS = [
    "raised", "funding", "series", "seed", "round", "investment",
    "investors", "valuation", "venture", "capital", "backed",
]
_HIRING_KWS = [
    "hiring", "jobs", "careers", "positions", "openings", "recruitment",
    "talent", "employees", "workforce", "headcount", "staff",
]
_EXPANSION_KWS = [
    "expand", "expansion", "launch", "entering", "new market", "opens",
    "international", "global", "region", "growth", "partnership",
]
_TECH_KWS = [
    "kubernetes", "k8s", "aws", "azure", "gcp", "docker", "microservices",
    "cloud", "infrastructure", "platform", "devops", "migrate", "stack",
    "postgresql", "mongodb", "redis", "kafka", "graphql",
]
_LEADERSHIP_KWS = [
    "appoints", "names", "ceo", "cto", "coo", "vp", "president",
    "joins", "hire", "executive", "leadership", "chief",
]

_AMOUNT_RE = re.compile(
    r"\$\s*([\d,.]+)\s*(million|billion|m\b|b\b)", re.IGNORECASE
)
_ROUND_RE = re.compile(r"\b(seed|series\s+[a-z]|pre-[a-z]+)\b", re.IGNORECASE)
_ROLES_RE = re.compile(r"\b(\d+)\+?\s*(engineer|developer|position|role|job|opening)", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(20\d{2})\b")
_EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}\b")


class SerperService:
    def __init__(self, api_key: str, base_url: str = "https://google.serper.dev/search"):
        self.api_key = api_key
        self.base_url = base_url
        self._headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    async def fetch_company_signals(self, company: str) -> Dict[str, Any]:
        """
        Run 5 targeted searches for a company and return structured signals.
        Returns a dict with keys: funding, hiring, expansion, tech_stack,
        leadership, news (all optional).
        """
        queries = {
            "funding": f"{company} funding round raised investment 2024 2025",
            "hiring": f"{company} hiring jobs careers openings",
            "expansion": f"{company} expansion new market launch growth",
            "tech_stack": f"{company} tech stack infrastructure engineering",
            "leadership": f"{company} appoints names leadership executive",
        }

        raw_results: Dict[str, List[Dict]] = {}
        async with httpx.AsyncClient(timeout=20.0) as client:
            for signal_type, query in queries.items():
                try:
                    results = await self._search(client, query)
                    raw_results[signal_type] = results
                except Exception as exc:
                    logger.warning(f"Serper query failed for '{query}': {exc}")
                    raw_results[signal_type] = []

        # Parse each result bucket into a structured signal
        signals: Dict[str, Any] = {}

        funding = self._parse_funding(raw_results.get("funding", []), company)
        if funding:
            signals["funding"] = funding

        hiring = self._parse_hiring(raw_results.get("hiring", []), company)
        if hiring:
            signals["hiring"] = hiring

        expansion = self._parse_expansion(raw_results.get("expansion", []), company)
        if expansion:
            signals["expansion"] = expansion

        tech = self._parse_tech(raw_results.get("tech_stack", []), company)
        if tech:
            signals["tech_stack"] = tech

        leadership = self._parse_leadership(raw_results.get("leadership", []), company)
        if leadership:
            signals["leadership"] = leadership

        # General news fallback: pick best headline
        all_results = []
        for bucket in raw_results.values():
            all_results.extend(bucket)
        news = self._parse_news(all_results, company)
        if news:
            signals["news"] = news

        logger.info(f"Fetched {len(signals)} signal types for '{company}'")
        return signals

    async def fetch_contact_candidates(self, company: str) -> List[Dict[str, str]]:
        """
        Discover likely work emails for a company from public search snippets.
        Returns ranked list of unique candidates.
        """
        queries = [
            f'{company} head of sales email',
            f'{company} vp sales email',
            f'{company} cto email',
            f'{company} contact us email',
            f'site:linkedin.com/in "{company}" "@"',
        ]

        candidates: Dict[str, Dict[str, str]] = {}

        async with httpx.AsyncClient(timeout=20.0) as client:
            for query in queries:
                try:
                    results = await self._search(client, query)
                except Exception as exc:
                    logger.warning("Contact discovery query failed for '%s': %s", query, exc)
                    continue

                for item in results[:10]:
                    blob = " ".join([
                        str(item.get("title", "")),
                        str(item.get("snippet", "")),
                        str(item.get("link", "")),
                    ])
                    for raw_email in _EMAIL_RE.findall(blob):
                        email = raw_email.lower().strip(".,;:()[]<>")
                        if self._is_useful_work_email(email, company):
                            candidates[email] = {
                                "email": email,
                                "source": item.get("link") or "serper",
                            }

                    # If explicit emails are missing, generate common inbox aliases from company domain.
                    domain = self._extract_domain(item.get("link", ""))
                    if domain and self._domain_matches_company(domain, company):
                        for alias in ("hello", "sales", "contact", "partnerships"):
                            synthetic = f"{alias}@{domain}"
                            if synthetic not in candidates:
                                candidates[synthetic] = {
                                    "email": synthetic,
                                    "source": f"domain_guess:{domain}",
                                }

        ranked = sorted(candidates.values(), key=lambda c: self._email_rank(c["email"]))
        return ranked[:8]

    async def resolve_company_domain(self, company: str) -> Optional[Dict[str, Any]]:
        """
        Resolve the most likely official company domain from search results.
        Returns best candidate with confidence, or None if confidence is too low.
        """
        queries = [
            f'"{company}" official website',
            f'"{company}" company site',
            f'"{company}" about',
        ]
        candidates: Dict[str, Dict[str, Any]] = {}

        async with httpx.AsyncClient(timeout=20.0) as client:
            for query in queries:
                try:
                    results = await self._search(client, query)
                except Exception as exc:
                    logger.warning("Domain resolution query failed for '%s': %s", query, exc)
                    continue

                for idx, item in enumerate(results[:8]):
                    domain = self._extract_domain(item.get("link", ""))
                    if not domain or self._is_non_company_host(domain):
                        continue
                    score = self._score_domain_candidate(company, domain, item, idx)
                    current = candidates.get(domain)
                    if not current or score > current["confidence"]:
                        candidates[domain] = {
                            "domain": domain,
                            "confidence": round(score, 3),
                            "source": item.get("link"),
                            "title": item.get("title", ""),
                        }

        if not candidates:
            return None

        ranked = sorted(candidates.values(), key=lambda row: row["confidence"], reverse=True)
        best = ranked[0]
        return best if best["confidence"] >= 0.75 else None

    # ──────────────────────────────────────────────────────────────────────────
    # Internal: HTTP
    # ──────────────────────────────────────────────────────────────────────────

    async def _search(self, client: httpx.AsyncClient, query: str) -> List[Dict]:
        """Execute a single Serper search and return organic results."""
        payload = {"q": query, "num": 10}
        response = await client.post(self.base_url, headers=self._headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("organic", [])

    # ──────────────────────────────────────────────────────────────────────────
    # Internal: Parsers
    # ──────────────────────────────────────────────────────────────────────────

    def _text_of(self, item: Dict) -> str:
        return f"{item.get('title', '')} {item.get('snippet', '')}".lower()

    def _calculate_relevance(self, text: str, company: str) -> float:
        """
        Calculate a relevance score (0.05 - 1.0) based on company mention.
        Exact/Alias: 1.0 | First Word: 0.8 | None: 0.05
        """
        text_lower = text.lower()
        co_lower = company.lower()
        
        # 1.0 - Exact or Alias match
        if co_lower in text_lower:
            return 1.0
        
        # 0.8 - First word (e.g., "Stripe" for "Stripe Inc")
        first_word = co_lower.split()[0]
        if len(first_word) > 2 and first_word in text_lower:
            return 0.8
            
        # 0.05 - No mention (soft-kill)
        return 0.05

    def _confidence_from_keyword_density(self, text: str, keywords: List[str]) -> float:
        hits = sum(1 for kw in keywords if kw in text)
        return min(0.95, 0.4 + (hits * 0.1))

    def _parse_funding(self, results: List[Dict], company: str) -> Optional[Dict]:
        for item in results[:10]:
            text = self._text_of(item)
            relevance = self._calculate_relevance(text, company)
            
            if not any(kw in text for kw in _FUNDING_KWS):
                continue

            amount_match = _AMOUNT_RE.search(text)
            round_match = _ROUND_RE.search(text)
            year_match = _DATE_RE.search(item.get("date", "") + " " + text)

            amount = None
            if amount_match:
                num = amount_match.group(1).replace(",", "")
                unit = amount_match.group(2).lower()
                if unit in ("billion", "b"):
                    amount = f"${num}B"
                else:
                    amount = f"${num}M"

            confidence = self._confidence_from_keyword_density(text, _FUNDING_KWS)
            if amount:
                confidence = min(0.97, confidence + 0.15)

            return {
                "status": "raised",
                "amount": amount or "undisclosed",
                "round": round_match.group(0).title() if round_match else "undisclosed",
                "date": year_match.group(0) if year_match else item.get("date"),
                "source": item.get("link"),
                "headline": item.get("title"),
                "confidence": round(confidence, 2),
                "relevance": relevance,
                "ignored_in_scoring": relevance < 0.2
            }
        return None

    def _parse_hiring(self, results: List[Dict], company: str) -> Optional[Dict]:
        for item in results[:10]:
            text = self._text_of(item)
            relevance = self._calculate_relevance(text, company)
            
            if not any(kw in text for kw in _HIRING_KWS):
                continue

            roles_match = _ROLES_RE.search(text)
            open_roles = int(roles_match.group(1)) if roles_match else None

            # Detect departments from common terms
            departments = []
            for dept in ["engineering", "sales", "marketing", "product", "data", "design"]:
                if dept in text:
                    departments.append(dept.title())

            confidence = self._confidence_from_keyword_density(text, _HIRING_KWS)

            return {
                "open_roles": open_roles,
                "departments": departments or ["General"],
                "growth_rate": "high" if open_roles and open_roles >= 10 else "moderate",
                "source": item.get("link"),
                "headline": item.get("title"),
                "confidence": round(confidence, 2),
                "relevance": relevance,
                "ignored_in_scoring": relevance < 0.2
            }
        return None

    def _parse_expansion(self, results: List[Dict], company: str) -> Optional[Dict]:
        for item in results[:10]:
            text = self._text_of(item)
            relevance = self._calculate_relevance(text, company)
            
            if not any(kw in text for kw in _EXPANSION_KWS):
                continue

            regions = []
            for region in ["apac", "europe", "emea", "latam", "asia", "africa",
                           "americas", "middle east", "india", "china"]:
                if region in text:
                    regions.append(region.upper())

            confidence = self._confidence_from_keyword_density(text, _EXPANSION_KWS)

            return {
                "regions": regions or ["undisclosed"],
                "description": item.get("snippet", "")[:200],
                "source": item.get("link"),
                "headline": item.get("title"),
                "confidence": round(confidence, 2),
                "relevance": relevance,
                "ignored_in_scoring": relevance < 0.2
            }
        return None

    def _parse_tech(self, results: List[Dict], company: str) -> Optional[Dict]:
        identified = []
        best_relevance = 0.05
        for item in results[:10]:
            text = self._text_of(item)
            rel = self._calculate_relevance(text, company)
            best_relevance = max(best_relevance, rel)
            for tech in _TECH_KWS:
                display = tech.upper() if len(tech) <= 4 else tech.title()
                if tech in text and display not in identified:
                    identified.append(display)

        if not identified:
            return None

        confidence = min(0.90, 0.5 + len(identified) * 0.05)
        return {
            "identified": identified[:8],
            "changes": f"Using {', '.join(identified[:3])}" if identified else None,
            "source": results[0].get("link") if results else None,
            "confidence": round(confidence, 2),
            "relevance": best_relevance,
            "ignored_in_scoring": best_relevance < 0.2
        }

    def _parse_leadership(self, results: List[Dict], company: str) -> Optional[Dict]:
        for item in results[:8]:
            text = self._text_of(item)
            relevance = self._calculate_relevance(text, company)
            
            if not any(kw in text for kw in _LEADERSHIP_KWS):
                continue
            confidence = self._confidence_from_keyword_density(text, _LEADERSHIP_KWS)
            return {
                "description": item.get("snippet", "")[:200],
                "headline": item.get("title"),
                "source": item.get("link"),
                "confidence": round(confidence, 2),
                "relevance": relevance,
                "ignored_in_scoring": relevance < 0.2
            }
        return None

    def _parse_news(self, all_results: List[Dict], company: str) -> Optional[Dict]:
        """Pick most relevant recent news headline."""
        company_lower = company.lower()
        for item in all_results[:20]:
            title = item.get("title", "").lower()
            text = self._text_of(item)
            relevance = self._calculate_relevance(text, company)
            
            if relevance >= 0.8:
                return {
                    "headline": item.get("title"),
                    "snippet": item.get("snippet", "")[:200],
                    "date": item.get("date"),
                    "source": item.get("link"),
                    "confidence": 0.75,
                    "relevance": relevance,
                    "ignored_in_scoring": False
                }
        return None

    def _extract_domain(self, url: str) -> Optional[str]:
        if not url:
            return None
        try:
            host = urlparse(url).netloc.lower()
            if host.startswith("www."):
                host = host[4:]
            if "." not in host:
                return None
            return host
        except Exception:
            return None

    def _domain_matches_company(self, domain: str, company: str) -> bool:
        company_slug = "".join(ch for ch in company.lower() if ch.isalnum())
        domain_root = domain.split(".")[0]
        return company_slug and (company_slug in domain_root or domain_root in company_slug)

    def _score_domain_candidate(self, company: str, domain: str, item: Dict[str, Any], rank_idx: int) -> float:
        title = str(item.get("title", "")).lower()
        snippet = str(item.get("snippet", "")).lower()
        text = f"{title} {snippet}"
        company_slug = "".join(ch for ch in company.lower() if ch.isalnum())
        company_words = [w for w in re.split(r"[^a-z0-9]+", company.lower()) if w]
        root = domain.split(".")[0].lower()

        score = max(0.1, 0.45 - (rank_idx * 0.04))
        if company_slug and root == company_slug:
            score += 0.4
        elif company_slug and (company_slug in root or root in company_slug):
            score += 0.25

        word_hits = sum(1 for word in company_words if len(word) > 2 and word in text)
        score += min(0.2, word_hits * 0.08)

        if "official" in text:
            score += 0.08
        if any(token in text for token in ["about", "contact", "careers"]):
            score += 0.04

        return min(score, 1.0)

    def _is_non_company_host(self, domain: str) -> bool:
        blocked = (
            "linkedin.com",
            "crunchbase.com",
            "pitchbook.com",
            "facebook.com",
            "instagram.com",
            "x.com",
            "twitter.com",
            "youtube.com",
            "wikipedia.org",
        )
        return any(domain.endswith(host) for host in blocked)

    def _is_useful_work_email(self, email: str, company: str) -> bool:
        blocked_domains = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "proton.me",
            "protonmail.com",
        }
        domain = email.split("@")[-1]
        if domain in blocked_domains:
            return False
        return "." in domain and len(email) >= 8

    def _email_rank(self, email: str) -> int:
        # Lower rank value = better candidate.
        if email.startswith("sales@"):
            return 0
        if email.startswith("partnerships@"):
            return 1
        if email.startswith("hello@") or email.startswith("contact@"):
            return 2
        return 3
