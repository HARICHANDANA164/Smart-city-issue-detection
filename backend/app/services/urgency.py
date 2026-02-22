from __future__ import annotations

import re


HIGH_KEYWORDS = [
    "leak",
    "danger",
    "outage",
    "sparks",
    "accident",
    "unsafe",
    "overflow",
    "fire",
]

MEDIUM_KEYWORDS = [
    "delay",
    "not working",
    "broken",
    "clogged",
    "blocked",
    "power cut",
    "cuts",
]


def predict_urgency(text: str) -> str:
    """
    Rule-based urgency prediction (as required):
    - High: leak, danger, outage, ...
    - Medium: delay, not working, ...
    - Low: others
    """
    t = (text or "").lower()

    def has_any(keywords: list[str]) -> bool:
        for kw in keywords:
            # treat keyword as phrase; match on word boundaries where possible
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, t):
                return True
        return False

    if has_any(HIGH_KEYWORDS):
        return "High"
    if has_any(MEDIUM_KEYWORDS):
        return "Medium"
    return "Low"


