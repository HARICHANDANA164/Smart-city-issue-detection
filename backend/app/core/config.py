from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart City Issue Detection API"
    api_prefix: str = "/api/v1"
    db_path: Path = Path("backend/data/app.db")
    jwt_secret_key: str = Field("change-me-in-env", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    upload_dir: Path = Path("backend/uploads")
    allowed_origins: list[str] = ["http://localhost:5173"]

    # Existing ML assets
    train_data_path: Path = Path("data/sample_issues.csv")
    category_model_path: Path = Path("models/category_model.joblib")
    urgency_model_path: Path = Path("models/urgency_model.joblib")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
