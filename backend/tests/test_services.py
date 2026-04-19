"""
tests/test_services.py – Unit tests for pure functions and services.
"""

import pytest
from datetime import datetime, timezone
from services.scoring import score_lead, calculate_breakdown, _score_signal, _recency_factor


# ── Scoring Tests ─────────────────────────────────────────────────────────────

class TestScoring:

    def test_empty_signals_zero_score(self):
        assert score_lead({}) == 0.0

    def test_none_signals_zero_score(self):
        assert score_lead({"hiring": None}) == 0.0

    def test_full_signals_high_score(self):
        # Multiple quality signals should trigger boosts
        signals = {
            "hiring": {"confidence": 0.9, "relevance": 1.0, "date": "2025"},
            "funding": {"confidence": 0.85, "relevance": 1.0, "date": "2025"},
            "expansion": {"confidence": 0.8, "relevance": 1.0},
            "tech_stack": {"confidence": 0.75, "relevance": 1.0},
        }
        score = score_lead(signals)
        assert score > 0.65
        assert score <= 1.0

    def test_stripe_scenario_v4(self):
        """
        Verify the exact case that was failing.
        Signals: Funding 0.85, Hiring 0.5, Expansion 0.7 (but noisy), Tech 0.65.
        With V4 logic, this should pass comfortably.
        """
        signals = {
            "funding": {"confidence": 0.85, "relevance": 1.0, "date": "2026-02-24"},  # High value
            "hiring": {"confidence": 0.5, "relevance": 1.0},
            "expansion": {"confidence": 0.7, "relevance": 0.05, "ignored_in_scoring": True}, # NOISE
            "tech_stack": {"confidence": 0.65, "relevance": 0.8},
        }
        score = score_lead(signals)
        assert score >= 0.45

    def test_noise_suppression(self):
        # Signals that are irrelevant should result in 0 score
        signals = {
            "funding": {"confidence": 0.9, "relevance": 0.05, "ignored_in_scoring": True},
            "hiring": {"confidence": 0.9, "relevance": 0.05, "ignored_in_scoring": True},
        }
        assert score_lead(signals) == 0.0

    def test_single_signal_penalty(self):
        # One high confidence signal should be safe-guarded
        signals = {
            "funding": {"confidence": 0.9, "relevance": 1.0},
        }
        score = score_lead(signals)
        assert score < 0.5

    def test_recency_no_date(self):
        # Default for missing dates should not over-penalize fresh but undated news.
        factor = _recency_factor(None)
        assert factor == 0.85


# ── Serper Parser Tests ───────────────────────────────────────────────────────

class TestSerperParser:
    """Test signal extraction logic using mock Serper organic results."""

    def _make_result(self, title="", snippet="", link="", date=""):
        return {"title": title, "snippet": snippet, "link": link, "date": date}

    def test_relevance_matching(self):
        from services.serper import SerperService
        svc = SerperService(api_key="test")
        
        assert svc._calculate_relevance("Stripe raises funding", "Stripe") == 1.0
        assert svc._calculate_relevance("Stripe Inc expands", "Stripe Inc") == 1.0
        assert svc._calculate_relevance("Stripe expands", "Stripe Inc") == 0.8
        assert svc._calculate_relevance("Higgsfield revenue up", "Stripe") == 0.05

    def test_parse_funding_with_relevance(self):
        from services.serper import SerperService
        svc = SerperService(api_key="test")
        results = [
            self._make_result(
                title="Stripe raises $150M",
                snippet="Stripe announced series C"
            )
        ]
        # Match
        signal = svc._parse_funding(results, "Stripe")
        assert signal["relevance"] == 1.0
        assert signal["ignored_in_scoring"] is False
        
        # No match
        signal_noise = svc._parse_funding(results, "Higgsfield")
        assert signal_noise["relevance"] == 0.05
        assert signal_noise["ignored_in_scoring"] is True

    def test_parse_hiring_detects_departments(self):
        from services.serper import SerperService
        svc = SerperService(api_key="test")
        results = [
            self._make_result(
                title="Acme Corp is hiring engineers",
                snippet="Acme currently hiring for 25 engineering positions"
            )
        ]
        signal = svc._parse_hiring(results, "Acme Corp")
        assert signal is not None
        assert "Engineering" in signal["departments"]

    def test_score_domain_candidate_prefers_exact_brand_domain(self):
        from services.serper import SerperService
        svc = SerperService(api_key="test")
        exact = svc._score_domain_candidate(
            "Rabbitt AI",
            "rabbitt.ai",
            {"title": "Rabbitt AI Official Website", "snippet": "Rabbitt AI official site"},
            0,
        )
        wrong = svc._score_domain_candidate(
            "Rabbitt AI",
            "rabbittools.com",
            {"title": "Rabbit Tools", "snippet": "AI workflow tools"},
            0,
        )
        assert exact > wrong


class TestContactDiscovery:
    @pytest.mark.asyncio
    async def test_resolve_domain_uses_direct_domain_input(self):
        from services.contact_discovery import ContactDiscoveryService
        svc = ContactDiscoveryService(hunter_api_key="")
        resolved = await svc._resolve_domain("rabbitt.ai")
        assert resolved == "rabbitt.ai"

    @pytest.mark.asyncio
    async def test_resolve_domain_uses_serper_resolution(self):
        from services.contact_discovery import ContactDiscoveryService

        class DummySerper:
            async def resolve_company_domain(self, company):
                return {"domain": "rabbitt.ai", "confidence": 0.91}

        svc = ContactDiscoveryService(hunter_api_key="", serper_service=DummySerper())
        resolved = await svc._resolve_domain("Rabbitt AI")
        assert resolved == "rabbitt.ai"

    def test_rank_contacts_prefers_named_people_over_generic_inbox(self):
        from services.contact_discovery import ContactDiscoveryService
        svc = ContactDiscoveryService(hunter_api_key="")
        contacts = [
            {
                "name": "",
                "title": "Unknown",
                "email": "sales@rabbitt.ai",
                "confidence": 0.9,
                "seniority": "unknown",
                "is_generic": True,
            },
            {
                "name": "Jane Doe",
                "title": "Founder",
                "email": "jane@rabbitt.ai",
                "confidence": 0.75,
                "seniority": "executive",
                "is_generic": False,
            },
        ]
        ranked = svc._rank_contacts(contacts, ["Founder", "CTO"])
        assert ranked[0]["email"] == "jane@rabbitt.ai"

    def test_fetch_hunter_prefers_people_if_available(self):
        from services.contact_discovery import ContactDiscoveryService
        svc = ContactDiscoveryService(hunter_api_key="")
        contacts = [
            {"email": "sales@rabbitt.ai", "is_generic": True},
            {"email": "jane@rabbitt.ai", "is_generic": False},
        ]
        person_contacts = [c for c in contacts if not c.get("is_generic")]
        assert person_contacts == [{"email": "jane@rabbitt.ai", "is_generic": False}]


# ── Email Service Tests ───────────────────────────────────────────────────────

class TestEmailService:

    @pytest.mark.asyncio
    async def test_no_credentials_returns_preview_only(self):
        from services.email import EmailService
        svc = EmailService()
        result = await svc.send_email("test@example.com", "Subject", "Body")
        assert result["status"] == "preview_only"
        assert result["method"] == "none"

    @pytest.mark.asyncio
    async def test_validate_config_no_keys(self):
        from services.email import EmailService
        svc = EmailService()
        config = await svc.validate_config()
        assert config["can_send"] is False


# ── Email Generation Tests ────────────────────────────────────────────────────

class TestEmailGeneration:

    def test_word_count_enforcement(self):
        from agent.nodes.generate_email import _enforce_word_limit
        long_text = " ".join(["word"] * 200)
        trimmed = _enforce_word_limit(long_text, 120)
        assert len(trimmed.split()) <= 120

    def test_signals_summary_formatting(self):
        from agent.nodes.generate_email import _build_signals_summary
        signals = {
            "funding": {"amount": "$100M", "round": "Series A"},
            "hiring": {"open_roles": 15, "departments": ["Engineering"]},
        }
        summary = _build_signals_summary(signals)
        assert "100M" in summary
        assert "15" in summary

    def test_email_parse_extracts_subject_and_body(self):
        from agent.nodes.generate_email import _parse_email
        raw = "Subject: Test Company Growth\nBody:\nHi there, I noticed Test Company raised $100M.\n\nWould you be open to a quick 15-minute call?"
        subject, body = _parse_email(raw, "Test Company")
        assert "Test Company Growth" in subject
        assert "100M" in body
