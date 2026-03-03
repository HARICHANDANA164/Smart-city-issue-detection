from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.dashboard_controller import DashboardController
from app.db.database import Database
from app.dependencies import get_db
from app.schemas.issue import AnalyticsResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_controller(db: Database = Depends(get_db)) -> DashboardController:
    return DashboardController(db)


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(controller: DashboardController = Depends(get_controller)):
    return controller.analytics()
