from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # Paths are resolved relative to the backend/ directory by default.
    category_model_path: Path
    urgency_model_path: Path
    train_data_path: Path
    db_path: Path

    # Comma-separated list of origins (or "*" for demo).
    allowed_origins: list[str]


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return ["*"]
    value = value.strip()
    if value == "*":
        return ["*"]
    return [o.strip() for o in value.split(",") if o.strip()]


def get_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]  # backend/

    category_model_path = Path(
        os.getenv(
            "CATEGORY_MODEL_PATH",
            str(backend_root / ".." / "models" / "artifacts" / "category_model.joblib"),
        )
    ).resolve()
    urgency_model_path = Path(
        os.getenv(
            "URGENCY_MODEL_PATH",
            str(backend_root / ".." / "models" / "artifacts" / "urgency_model.joblib"),
        )
    ).resolve()
    train_data_path = Path(
        os.getenv(
            "TRAIN_DATA_PATH",
            str(backend_root / ".." / "data" / "nyc_311_subset.csv"),
        )
    ).resolve()
    db_path = Path(os.getenv("DB_PATH", str(backend_root / ".." / "data" / "complaints.db"))).resolve()
    # Dev-friendly default: allow Vite from both localhost and 127.0.0.1
    allowed_origins = _parse_origins(
        os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )

    return Settings(
        category_model_path=category_model_path,
        urgency_model_path=urgency_model_path,
        train_data_path=train_data_path,
        db_path=db_path,
        allowed_origins=allowed_origins,
    )


