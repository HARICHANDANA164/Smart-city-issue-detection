from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.services.generative_ai import generate_acknowledgment, generate_suggestions
from app.services.model import load_models


@lru_cache(maxsize=1)
def _models() -> Any:
    settings = get_settings()
    return load_models(
        train_data_path=settings.train_data_path,
        category_model_path=settings.category_model_path,
        urgency_model_path=settings.urgency_model_path,
    )


def classify_complaint(complaint: str) -> dict[str, str]:
    category_model, urgency_model = _models()
    category = category_model.predict([complaint])[0]
    urgency = urgency_model.predict([complaint])[0]
    acknowledgment = generate_acknowledgment(category=category, urgency=urgency)
    suggestions = generate_suggestions(category=category, urgency=urgency)
    suggestion = " ".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))
    return {
        "category": category,
        "urgency": urgency,
        "acknowledgment": acknowledgment,
        "suggestion": suggestion,
    }
