from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class Settings:
    app_name: str
    api_prefix: str
    db_path: Path
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    upload_dir: Path
    allowed_origins: list[str]
    train_data_path: Path
    category_model_path: Path
    urgency_model_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    raw_origins = os.getenv("ALLOWED_ORIGINS", '["http://localhost:5173"]')
    try:
        allowed_origins = json.loads(raw_origins)
    except json.JSONDecodeError:
        allowed_origins = [x.strip() for x in raw_origins.split(",") if x.strip()]

    settings = Settings(
        app_name=os.getenv("APP_NAME", "Smart City Issue Detection API"),
        api_prefix=os.getenv("API_PREFIX", "/api/v1"),
        db_path=Path(os.getenv("DB_PATH", "backend/data/app.db")),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-this-in-prod-min-16-chars"),
        jwt_algorithm="HS256",
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
        upload_dir=Path(os.getenv("UPLOAD_DIR", "backend/uploads")),
        allowed_origins=allowed_origins,
        train_data_path=Path(os.getenv("TRAIN_DATA_PATH", "data/sample_issues.csv")),
        category_model_path=Path(os.getenv("CATEGORY_MODEL_PATH", "models/category_model.joblib")),
        urgency_model_path=Path(os.getenv("URGENCY_MODEL_PATH", "models/urgency_model.joblib")),
    )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
