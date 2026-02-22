from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Category = Literal[
    "Road & Infrastructure",
    "Water & Drainage",
    "Sanitation",
    "Electricity",
    "Public Safety",
]

Urgency = Literal["High", "Medium", "Low"]


class PredictRequest(BaseModel):
    complaint: str = Field(..., min_length=3, description="Citizen complaint text")


class PredictResponse(BaseModel):
    category: Category
    urgency: Urgency
    acknowledgment: str
    suggestion: str


class ComplaintRecord(BaseModel):
    id: str
    created_at: datetime
    text: str
    category: Category
    urgency: Urgency


class ComplaintListResponse(BaseModel):
    items: list[ComplaintRecord]


