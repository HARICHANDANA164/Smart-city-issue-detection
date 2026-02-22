from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.db.database import Database


class IssueService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save_upload(self, upload: UploadFile | None, folder: str = "issues") -> str | None:
        if not upload:
            return None
        ext = Path(upload.filename or "").suffix.lower() or ".jpg"
        settings = get_settings()
        target_dir = settings.upload_dir / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4()}{ext}"
        target_path = target_dir / filename
        with target_path.open("wb") as f:
            f.write(upload.file.read())
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

    def update_status(self, issue_id: str, status_value: str, comment: str | None, resolution_upload: UploadFile | None) -> dict:
        resolution_image_path = self.save_upload(resolution_upload, folder="resolutions")
        issue = self.db.update_issue_status(issue_id, status_value, comment, resolution_image_path)
        if not issue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
        return issue
