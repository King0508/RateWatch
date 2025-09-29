import re
from typing import Tuple

BASE_POS = {
    "rally",
    "beat",
    "cooling",
    "easing",
    "improves",
    "tightening_spreads",
    "disinflation",
    "soft_landing",
    "resilient",
    "upswing",
    "bid",
    "tightens_spreads",
}
BASE_NEG = {
    "selloff",
    "slump",
    "miss",
    "spike",
    "surge",
    "downgrade",
    "default",
    "sticky_inflation",
    "recession",
    "widen",
    "widening",
    "credit_crunch",
    "risk_aversion",
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-]+")


def _normalize(text: str) -> list:
    return [w.lower() for w in WORD_RE.findall(text or "")]


def sentiment_score(text: str, pos_extra=None, neg_extra=None) -> Tuple[int, str]:
    """
    Simple scoring: +1 per positive word, -1 per negative word.
    Returns (score, label) where label ∈ {"risk-on","risk-off","neutral"}.
    """
    tokens = _normalize(text)
    pos = set(BASE_POS)
    neg = set(BASE_NEG)
    if pos_extra:
        pos |= {w.lower() for w in pos_extra}
    if neg_extra:
        neg |= {w.lower() for w in neg_extra}

    score = 0
    for t in tokens:
        if t in pos:
            score += 1
        elif t in neg:
            score -= 1

    if score >= 1:
        label = "risk-on"
    elif score <= -1:
        label = "risk-off"
    else:
        label = "neutral"
    return score, label
