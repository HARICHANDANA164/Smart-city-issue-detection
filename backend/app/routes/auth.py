from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.auth_controller import AuthController
from app.dependencies import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_controller(db=Depends(get_db)) -> AuthController:
    return AuthController(AuthService(db))


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, controller: AuthController = Depends(get_controller)):
    return controller.register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, controller: AuthController = Depends(get_controller)):
    return controller.login(payload)
