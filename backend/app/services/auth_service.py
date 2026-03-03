from __future__ import annotations

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import Database


class AuthService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def register(self, name: str, email: str, password: str, role: str) -> dict:
        if self.db.get_user_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = self.db.create_user(name=name, email=email, password_hash=hash_password(password), role=role)
        token = create_access_token(subject=user["id"], role=user["role"])
        return {"access_token": token, "user": user}

    def login(self, email: str, password: str) -> dict:
        user = self.db.get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        user_dict = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"],
        }
        token = create_access_token(subject=user["id"], role=user["role"])
        return {"access_token": token, "user": user_dict}
