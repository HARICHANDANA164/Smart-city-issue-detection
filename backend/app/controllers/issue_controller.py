from __future__ import annotations

from app.services.issue_service import IssueService


class IssueController:
    def __init__(self, service: IssueService) -> None:
        self.service = service

    def create(self, payload: dict):
        return self.service.create_issue(payload)

    def list(self, filters: dict, page: int, page_size: int):
        return self.service.list_issues(filters, page, page_size)
