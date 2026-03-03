from __future__ import annotations

import random
import re

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import Database


def _normalize_identifier(identifier: str) -> str:
    value = identifier.strip()
    if "@" in value:
        return value.lower()
    return re.sub(r"\s+", "", value)


class AuthService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def request_otp(self, identifier: str, purpose: str) -> dict:
        identifier = _normalize_identifier(identifier)
        if "@" not in identifier and not re.fullmatch(r"\+?[0-9]{10,15}", identifier):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid phone format")
        otp = f"{random.randint(0, 999999):06d}"
        self.db.create_otp(identifier=identifier, purpose=purpose, code=otp)
        # Demo mode: return OTP in response. In production, send via SMS/Email provider.
        return {"message": f"OTP sent for {purpose}", "expires_in_seconds": 300, "demo_otp": otp}

    def register(self, name: str, identifier: str, password: str, role: str, otp: str) -> dict:
        identifier = _normalize_identifier(identifier)
        if self.db.get_user_by_identifier(identifier):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Identifier already registered")
        if not self.db.consume_otp(identifier=identifier, purpose="register", code=otp):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

        user = self.db.create_user(name=name, identifier=identifier, password_hash=hash_password(password), role=role, is_verified=True)
        token = create_access_token(subject=user["id"], role=user["role"])
        return {"access_token": token, "user": user}

    def login(self, identifier: str, password: str, otp: str) -> dict:
        identifier = _normalize_identifier(identifier)
        user = self.db.get_user_by_identifier(identifier)
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not bool(user["is_verified"]):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not verified")
        if not self.db.consume_otp(identifier=identifier, purpose="login", code=otp):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

        user_dict = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"],
            "is_verified": bool(user["is_verified"]),
            "created_at": user["created_at"],
        }
        token = create_access_token(subject=user["id"], role=user["role"])
        return {"access_token": token, "user": user_dict}
