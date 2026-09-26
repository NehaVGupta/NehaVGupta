"""Confidence tiers and the standard wording used across the product."""
HIGH, MODERATE = 0.80, 0.60
INSUFFICIENT = "Insufficient visual evidence for a reliable conclusion."
PRELIMINARY = "Preliminary AI analysis — expert verification required."


def tier(c):
    if c is None:
        return "insufficient"
    return "high" if c >= HIGH else "moderate" if c >= MODERATE else "insufficient"


def pct(c):
    return f"{round((c or 0) * 100)}%"
