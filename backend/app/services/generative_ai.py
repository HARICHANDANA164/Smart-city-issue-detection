from __future__ import annotations

"""
Generative AI module (prompt-based, no training).

For this demo we use simple templated logic to produce:
- an acknowledgment message (citizen-facing)
- suggested resolution steps (authority-facing)

Later, you can swap this implementation for an LLM call (Bedrock/OpenAI/etc.)
without changing the API contract.
"""

from typing import Literal

from ..schemas import Category, Urgency


def generate_acknowledgment(category: Category, urgency: Urgency) -> str:
    urgency_line = {
        # ASCII-only (avoids curly apostrophes/encoding issues in some terminals)
        "High": "We've flagged this as HIGH priority and will act immediately.",
        "Medium": "We've marked this as MEDIUM priority and will schedule a prompt response.",
        "Low": "We've marked this as LOW priority and will address it in the normal queue.",
    }[urgency]

    return (
        f"Thanks for reporting this {category} issue. "
        f"{urgency_line} "
        "You will receive updates as it progresses."
    )


def generate_suggestions(category: Category, urgency: Urgency) -> list[str]:
    # Generic steps that apply to most categories.
    base = [
        "Log the complaint and assign it to the responsible department.",
        "Verify the location/details and capture evidence (photo/video) if available.",
    ]

    if urgency == "High":
        base.insert(0, "Dispatch an on-call team to assess and make the area safe.")

    category_specific: dict[Category, list[str]] = {
        "Road & Infrastructure": [
            "Inspect the reported site and place temporary warning signage/barriers.",
            "Schedule repair (pothole fill / resurfacing) and notify traffic control if needed.",
        ],
        "Water & Drainage": [
            "Send a crew to isolate the leak/clog and prevent flooding.",
            "Clear blockage and test water flow/drainage after repair.",
        ],
        "Sanitation": [
            "Arrange immediate cleaning/garbage pickup for the affected area.",
            "Ensure recurring collection schedule is reinstated and monitored.",
        ],
        "Electricity": [
            "Check feeder/transformer status and dispatch an electrical maintenance crew.",
            "Repair fault and confirm power restoration; monitor for repeated outages.",
        ],
        "Public Safety": [
            "Notify the nearest patrol/unit and increase monitoring of the area.",
            "Address hazards (e.g., missing cover/light/signal) with the relevant department.",
        ],
    }

    closing = [
        "Update the complaint status once work is completed.",
    ]

    return base + category_specific[category] + closing

