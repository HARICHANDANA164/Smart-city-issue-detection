from __future__ import annotations

import base64
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.db.database import Database


class IssueService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_base64_image(self, image_base64: str | None, folder: str = "issues") -> str | None:
        if not image_base64:
            return None
        settings = get_settings()
        target_dir = settings.upload_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        payload = image_base64
        if "," in image_base64:
            payload = image_base64.split(",", 1)[1]
        try:
            raw = base64.b64decode(payload)
        except Exception:
            return None

        filename = f"{uuid4()}.jpg"
        target_path = target_dir / filename
        with target_path.open("wb") as f:
            f.write(raw)
        return str(target_path)

    def create_issue(self, payload: dict) -> dict:
        return self.db.create_issue(payload)

    def list_issues(self, filters: dict, page: int, page_size: int) -> list[dict]:
        offset = (page - 1) * page_size
        return self.db.list_issues(filters=filters, limit=page_size, offset=offset)

    def delete_issue(self, issue_id: str, current_user: dict) -> None:
        issue = self.db.get_issue(issue_id)
        if not issue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
        if current_user["role"] != "authority" and issue["user_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this issue")
        self.db.delete_issue(issue_id)

    def update_status(self, issue_id: str, status_value: str, comment: str | None, resolution_image_base64: str | None) -> dict:
        resolution_image_path = self.save_base64_image(resolution_image_base64, folder="resolutions")
        issue = self.db.update_issue_status(issue_id, status_value, comment, resolution_image_path)
        if not issue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
        return issue
