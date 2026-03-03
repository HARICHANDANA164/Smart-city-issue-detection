from __future__ import annotations

from app.services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService) -> None:
        self.service = service

    def request_otp(self, payload):
        return self.service.request_otp(payload.identifier, payload.purpose)

    def register(self, payload):
        return self.service.register(payload.name, payload.identifier, payload.password, payload.role, payload.otp)

    def login(self, payload):
        return self.service.login(payload.identifier, payload.password, payload.otp)
