from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import Category, IssueStatus


class IssueCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=180)
    description: str = Field(..., min_length=10, max_length=2000)
    category: Category
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    image_base64: str | None = None


class StatusUpdateRequest(BaseModel):
    status: IssueStatus
    comment: str | None = Field(default=None, max_length=500)
    resolution_image_base64: str | None = None


class StatusUpdateResponse(BaseModel):
    id: str
    old_status: IssueStatus | None
    new_status: IssueStatus
    comment: str | None
    created_at: datetime


class IssueResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    category: Category
    status: IssueStatus
    latitude: float
    longitude: float
    image_path: str | None
    resolution_image_path: str | None
    resolution_comment: str | None
    created_at: datetime
    updated_at: datetime
    reporter_name: str
    reporter_email: str


class IssuesListResponse(BaseModel):
    items: list[IssueResponse]
    page: int
    page_size: int


class AnalyticsResponse(BaseModel):
    total_issues: int
    pending: int
    completed: int
