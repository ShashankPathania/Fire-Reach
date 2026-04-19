"""
services/scoring.py – Deterministic lead scoring engine.

No LLM involved. Pure math based on signal confidence + recency.
Score range: 0.0 → 1.0.
Threshold for proceeding with outreach: >= 0.5
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

# ── Weights ─────────────────────────────────────────────────────────────────
WEIGHTS = {
    "hiring": 0.40,    # Strongest: active growth, budget open
    "funding": 0.30,   # Resources acquired = new vendor evaluation
    "expansion": 0.20, # New market = new stack/infra needs
    "tech_stack": 0.10, # Modernization = solution adoption window
}

RECENCY_DECAY_DAYS = 90  # Signal loses max value over 90 days


def score_lead(signals: Dict[str, Any]) -> float:
    """
    Master-Class Scoring Engine (V6 - LOCKED).
    Definitive, proportional logic for high-integrity lead evaluation.
    """
    # ── 1. Strict Filter ──────────────────────────────────────────────────
    # relevance < 0.2 is ignored entirely
    effective_signals_map = {
        name: s for name, s in signals.items()
        if isinstance(s, dict) and s.get("relevance", 0) >= 0.2
    }
    
    if not effective_signals_map:
        logger.info("Scoring: 0 valid signals (relevance >= 0.2). Returning 0.0")
        return 0.0

    # ── 2. Calculate Component Scores (Raw) ───────────────────────────────
    hiring_raw = _score_signal(effective_signals_map.get("hiring"))
    funding_raw = _score_signal(effective_signals_map.get("funding"))
    expansion_raw = _score_signal(effective_signals_map.get("expansion"))
    tech_raw = _score_signal(effective_signals_map.get("tech_stack"))
    
    raw_scores = [hiring_raw, funding_raw, expansion_raw, tech_raw]
    max_signal = max(raw_scores)

    # ── 3. Base Score Calculation ─────────────────────────────────────────
    # base = (0.7 * weighted_sum) + (0.3 * max_signal)
    weighted_sum = (
        hiring_raw * WEIGHTS["hiring"]
        + funding_raw * WEIGHTS["funding"]
        + expansion_raw * WEIGHTS["expansion"]
        + tech_raw * WEIGHTS["tech_stack"]
    )
    base_score = (0.7 * weighted_sum) + (0.3 * max_signal)

    # ── 4. Intensity Boost ────────────────────────────────────────────────
    # rewards strong signals without overriding missing data
    score = base_score + (0.2 * max_signal)

    # ── 5. Bonus Layer (Capped at 0.15) ───────────────────────────────────
    bonus_sum = 0.0
    # Multi-Signal: Funding (0.7) + Hiring (0.5)
    if funding_raw > 0.7 and hiring_raw > 0.5:
        bonus_sum += 0.15
        logger.debug("Scoring: Multi-signal bonus applied (+0.15)")
    
    # High-Intensity: Any > 0.85
    if any(s > 0.85 for s in raw_scores):
        bonus_sum += 0.1
        logger.debug("Scoring: High-intensity bonus applied (+0.1)")

    score += min(0.15, bonus_sum)

    # ── 6. Scaling & Penalties ─────────────────────────────────────────────
    # q = signals with relevance > 0.5
    quality_signals = [s for s in effective_signals_map.values() if s.get("relevance", 0) > 0.5]
    q = len(quality_signals)
    
    # Count Multiplier: keep score responsive for 2-3 strong signals.
    count_mult = min(1.05, 0.85 + (0.05 * q))
    score *= count_mult
    
    # Solo Penalty: 0.85x if q < 2
    if q < 2:
        score *= 0.85
        logger.debug("Scoring: Solo penalty applied (0.85x)")

    # ── 7. Final Clamp ────────────────────────────────────────────────────
    final_score = round(min(max(score, 0.0), 1.0), 4)
    
    logger.info(
        "Scoring V6: %0.2f | q=%d | base=%0.2f | boost=%0.2f | mult=%0.2f",
        final_score, q, base_score, (0.2 * max_signal), count_mult
    )
    
    return final_score


def calculate_breakdown(signals: Dict[str, Any]) -> Dict[str, float]:
    """
    Return per-component scores (pre-weighting) for UI display.
    """
    return {
        "hiring": round(_score_signal(signals.get("hiring")), 4),
        "funding": round(_score_signal(signals.get("funding")), 4),
        "expansion": round(_score_signal(signals.get("expansion")), 4),
        "tech_stack": round(_score_signal(signals.get("tech_stack")), 4),
        "weights": WEIGHTS,
    }


def _score_signal(signal: Optional[Dict]) -> float:
    """
    Score a single signal 0.0–1.0.
    Formula: confidence * recency * relevance
    """
    if not signal or signal.get("ignored_in_scoring", False) or signal.get("relevance", 0) < 0.2:
        return 0.0

    confidence: float = float(signal.get("confidence", 0.5))
    relevance: float = float(signal.get("relevance", 1.0))
    
    # ── Recency decay ────────────────────────────────────────────────────────
    date_str = signal.get("date")
    recency = _recency_factor(date_str)

    raw = confidence * recency * relevance
    return round(raw, 4)

    confidence: float = float(signal.get("confidence", 0.5))
    relevance: float = float(signal.get("relevance", 1.0))
    
    # ── Recency decay ────────────────────────────────────────────────────────
    date_str = signal.get("date")
    recency = _recency_factor(date_str)

    raw = confidence * recency * relevance
    return round(raw, 4)


def _recency_factor(date_str: Optional[str]) -> float:
    """
    Convert a date string into a recency multiplier.
    Default for missing date: 0.75
    """
    if not date_str:
        return 0.85

    try:
        parsed = dateutil_parser.parse(str(date_str), default=datetime(2024, 1, 1))
        # Use timezone-aware comparison if possible, otherwise naive
        now = datetime.now(timezone.utc) if parsed.tzinfo else datetime.now()
        days_old = (now - parsed).days
        days_old = max(0, days_old)
        factor = 1.0 - (days_old / RECENCY_DECAY_DAYS)
        return max(0.5, min(1.0, factor))
    except Exception:
        return 0.85


def explain_score(score: float, breakdown: Dict[str, float]) -> str:
    """
    Generate a human-readable explanation of the score.
    Used in the UI score explainability panel.
    """
    level = "🔥 High" if score >= 0.75 else ("⚡ Medium" if score >= 0.45 else "❄️ Low")
    parts = []
    for key, raw in breakdown.items():
        if key == "weights":
            continue
        weight = WEIGHTS.get(key, 0)
        contribution = raw * weight
        parts.append(f"  • {key.replace('_', ' ').title()}: {raw:.0%} signal × {weight:.0%} weight")

    return (
        f"{level} opportunity (score: {score:.2f})\n"
        + "\n".join(parts)
        + f"\n\nTotal Opportunity Score: {score:.2f}"
    )
