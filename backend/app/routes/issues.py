from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.issue_controller import IssueController
from app.db.database import Database
from app.dependencies import get_current_user, get_db, require_authority
from app.schemas.issue import IssueCreateRequest, IssueResponse, IssuesListResponse, StatusUpdateRequest, StatusUpdateResponse
from app.services.issue_service import IssueService

router = APIRouter(prefix="/issues", tags=["issues"])


def get_controller(db: Database = Depends(get_db)) -> IssueController:
    return IssueController(IssueService(db))


def get_service(db: Database = Depends(get_db)) -> IssueService:
    return IssueService(db)


@router.post("", response_model=IssueResponse)
def create_issue(
    payload: IssueCreateRequest,
    current_user: dict = Depends(get_current_user),
    service: IssueService = Depends(get_service),
):
    image_path = service.save_base64_image(payload.image_base64, folder="issues")
    issue_payload = {
        "user_id": current_user["id"],
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "image_path": image_path,
    }
    return service.create_issue(issue_payload)


@router.get("", response_model=IssuesListResponse)
def list_issues(
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
    controller: IssueController = Depends(get_controller),
):
    items = controller.list({"status": status, "category": category, "search": search}, page, page_size)
    return {"items": items, "page": page, "page_size": page_size}


@router.delete("/{issue_id}")
def delete_issue(
    issue_id: str,
    current_user: dict = Depends(get_current_user),
    service: IssueService = Depends(get_service),
):
    service.delete_issue(issue_id=issue_id, current_user=current_user)
    return {"message": "Issue deleted"}


@router.patch("/{issue_id}/status", response_model=IssueResponse)
def update_issue_status(
    issue_id: str,
    payload: StatusUpdateRequest,
    _: dict = Depends(require_authority),
    service: IssueService = Depends(get_service),
):
    return service.update_status(
        issue_id=issue_id,
        status_value=payload.status,
        comment=payload.comment,
        resolution_image_base64=payload.resolution_image_base64,
    )


@router.get("/{issue_id}/updates", response_model=list[StatusUpdateResponse])
def issue_updates(issue_id: str, db: Database = Depends(get_db)):
    return db.list_status_updates(issue_id)
