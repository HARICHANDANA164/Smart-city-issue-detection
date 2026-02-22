from __future__ import annotations

from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService) -> None:
        self.service = service

    def register(self, payload):
        return self.service.register(payload.name, payload.email, payload.password, payload.role)

    def login(self, payload):
        return self.service.login(payload.email, payload.password)
