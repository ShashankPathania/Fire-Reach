"""
agent/nodes/generate_email.py – Node 6: Generate personalized outreach email.

Strict constraints:
  - Max 120 words
  - Must reference ≥2 real signals
  - No templates — every email unique
  - Conversational, not sales-y
"""

import logging
import re
from typing import Any, Dict

from agent.state import AgentState
from services.llm import LLMService

logger = logging.getLogger(__name__)


def make_generate_email_node(llm_service: LLMService):
    """Factory returning a node function with llm_service injected."""

    async def generate_email_node(state: AgentState) -> dict:
        company = state.get("company", "Unknown")
        icp = state.get("icp", "")
        strategy = state.get("strategy", "")
        insights = state.get("insights", "")
        cleaned_signals = state.get("cleaned_signals") or {}
        recipient_email = (state.get("recipient_email") or "").strip().lower()
        recipient_name = _resolve_recipient_name(state, recipient_email)
        sender_name = (state.get("sender_name") or "FireReach Team").strip()
        sender_contact_email = (state.get("sender_contact_email") or "").strip()

        logger.info("[generate_email] Generating email for %s", company)

        signals_summary = _build_signals_summary(cleaned_signals)

        prompt = f"""You are a senior B2B sales development rep. Write a short, highly-personalized cold outreach email with clean formatting.

MANDATORY RULES:
1. Maximum 120 words for the body (HARD LIMIT — count carefully)
2. Must reference at least 2 specific signals from the data below
3. Do NOT use generic templates or clichés ("I hope this finds you well", "synergies", etc.)
4. Conversational tone — write like a real person, not a marketer
5. One clear CTA — ask for a specific 15-minute call
6. Opening line must reference a SPECIFIC signal (number, event, or fact)
7. Use plain-text formatting only (NO markdown, NO **, NO bullet symbols like "- ")
8. If recipient name is not verified, greeting must be exactly "Hi there,"

CONTEXT:
Company: {company}
Outreach angle: {strategy}
ICP context: {icp}
Signal data: {signals_summary}
Account brief (truncated): {insights[:400]}
Verified recipient first name: {recipient_name or "UNKNOWN"}

OUTPUT FORMAT — respond ONLY with this exact structure:
Subject: [compelling subject line referencing a real signal]
Body:
Hi [use verified first name if available, otherwise "there"],

[2-3 concise paragraphs that: (a) ground in the signals, (b) connect to likely pains, (c) briefly describe the value, (d) keep it human and specific.]

[Optional one short sentence listing 1-2 concrete value points in plain text.]

[1-sentence CTA asking for a 15-minute chat with a specific next step]

Best regards,
{sender_name}
{sender_contact_email if sender_contact_email else ""}

Generate the email now:"""

        try:
            raw = await llm_service.generate(prompt, max_tokens=300)
            subject, body = _parse_email(raw, company)
            body = _sanitize_email_body(body, recipient_name, sender_name, sender_contact_email)

            # Validate word count; trim if over limit
            body = _enforce_word_limit(body, 120)

            logger.info("[generate_email] Subject: '%s' | Words: %d", subject, _word_count(body))
            return {
                "email_subject": subject,
                "email": body,
            }

        except Exception as exc:
            logger.error("[generate_email] LLM failed: %s", exc)
            # Fallback template using real signal data
            subject, body = _fallback_email(company, signals_summary, strategy)
            return {
                "email_subject": subject,
                "email": body,
            }

    return generate_email_node


def _build_signals_summary(signals: Dict[str, Any]) -> str:
    """Create a compact, factual signal summary for the prompt."""
    parts = []

    if "funding" in signals:
        f = signals["funding"]
        amt = f.get("amount", "undisclosed")
        rnd = f.get("round", "")
        parts.append(f"Funding: Raised {amt} ({rnd})" if rnd != "undisclosed" else f"Funding: Raised {amt}")

    if "hiring" in signals:
        h = signals["hiring"]
        roles = h.get("open_roles")
        depts = ", ".join(h.get("departments", []))
        parts.append(
            f"Hiring: {roles}+ open roles" + (f" in {depts}" if depts else "")
            if roles else f"Hiring: Active recruitment in {depts or 'multiple departments'}"
        )

    if "expansion" in signals:
        e = signals["expansion"]
        regions = ", ".join(e.get("regions", []))
        parts.append(f"Expansion: Entering {regions or 'new markets'}")

    if "tech_stack" in signals:
        t = signals["tech_stack"]
        tech = ", ".join(t.get("identified", [])[:4])
        parts.append(f"Tech stack: {tech}")

    if "leadership" in signals:
        l = signals["leadership"]
        parts.append(f"Leadership: {l.get('headline', 'Recent leadership change')}")

    if "news" in signals:
        n = signals["news"]
        parts.append(f"News: {n.get('headline', '')}")

    return " | ".join(parts) if parts else "Limited public signals available"


def _parse_email(raw: str, company: str) -> tuple[str, str]:
    """Extract subject and body from LLM output."""
    lines = raw.strip().splitlines()
    subject = ""
    body_lines = []
    in_body = False

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("subject:"):
            subject = stripped[len("subject:"):].strip()
        elif stripped.lower() == "body:" or stripped.lower().startswith("body:"):
            in_body = True
            after = stripped[5:].strip()
            if after:
                body_lines.append(after)
        elif in_body:
            body_lines.append(line)
        elif subject and not in_body and stripped:
            # Body started without "Body:" label
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # Fallback if parsing fails
    if not subject:
        subject = f"{company}'s growth momentum"
    if not body:
        body = raw.strip()

    return subject, body


def _enforce_word_limit(body: str, limit: int) -> str:
    """Trim body to `limit` words if over."""
    words = body.split()
    if len(words) <= limit:
        return body
    trimmed = " ".join(words[:limit])
    # Ensure we end on a complete sentence
    last_period = trimmed.rfind(".")
    if last_period > len(trimmed) * 0.7:
        trimmed = trimmed[:last_period + 1]
    return trimmed


def _sanitize_email_body(
    body: str,
    recipient_name: str | None = None,
    sender_name: str = "FireReach Team",
    sender_contact_email: str = "",
) -> str:
    """Remove markdown artifacts and enforce safe greeting/signoff."""
    text = (body or "").strip()

    # Strip markdown formatting tokens that may leak into plain-text email.
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"^[ \t]*-\s+", "", text, flags=re.MULTILINE)

    lines = text.splitlines()
    sanitized = []
    greeting_fixed = False
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("hi "):
            if recipient_name:
                sanitized.append(f"Hi {recipient_name},")
            else:
                sanitized.append("Hi there,")
            greeting_fixed = True
            continue
        if "your name" in lower or "[your name" in lower:
            continue
        sanitized.append(line)

    result = "\n".join(sanitized).strip()
    if not greeting_fixed:
        result = f"{'Hi ' + recipient_name + ',' if recipient_name else 'Hi there,'}\n\n{result}".strip()

    # Ensure a stable sign-off without placeholders.
    if "best regards," not in result.lower():
        result = f"{result}\n\nBest regards,\n{sender_name}"
    elif sender_name.lower() not in result.lower():
        result = f"{result}\n{sender_name}"

    if sender_contact_email and sender_contact_email.lower() not in result.lower():
        result = f"{result}\n{sender_contact_email}"

    return result


def _resolve_recipient_name(state: AgentState, recipient_email: str) -> str:
    """Return first name only if confidently present in contact candidates."""
    if not recipient_email:
        return ""
    candidates = state.get("contact_candidates") or []
    for c in candidates:
        email = (c.get("email") or "").strip().lower()
        name = (c.get("name") or "").strip()
        if email == recipient_email and name:
            first = name.split()[0].strip(" ,.")
            return first
    return ""


def _word_count(text: str) -> int:
    return len(text.split())


def _fallback_email(company: str, signals_summary: str, strategy: str) -> tuple[str, str]:
    """Generate a minimal signal-grounded email if LLM is unavailable."""
    subject = f"Quick note on {company}'s growth trajectory"
    body = (
        f"Hi there,\n\n"
        f"I noticed {company} has been making moves recently — {signals_summary[:120]}.\n\n"
        f"This often signals {strategy.split('—')[0].strip().lower()} challenges that we help companies navigate.\n\n"
        f"Would you be open to a quick 15-minute call to explore if there's a fit?\n\n"
        f"Best,"
    )
    return subject, _enforce_word_limit(body, 120)
