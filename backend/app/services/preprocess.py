from __future__ import annotations

import re


def preprocess_text(text: str) -> str:
    """
    Preprocess text (as required):
    - Lowercase
    - Remove special characters
    """
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


