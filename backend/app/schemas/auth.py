from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import Role


class OtpRequest(BaseModel):
    identifier: str = Field(..., min_length=5, max_length=255, description="Email or phone number")
    purpose: str = Field(..., pattern="^(register|login)$")


class OtpResponse(BaseModel):
    message: str
    expires_in_seconds: int
    demo_otp: str


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    identifier: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    otp: str = Field(..., min_length=6, max_length=6)
    role: Role = "citizen"


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    otp: str = Field(..., min_length=6, max_length=6)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str | None
    phone: str | None
    role: Role
    is_verified: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
