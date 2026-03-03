from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import Category


class PredictRequest(BaseModel):
    complaint: str = Field(..., min_length=3)


class PredictResponse(BaseModel):
    category: Category
    urgency: str
    acknowledgment: str
    suggestion: str
