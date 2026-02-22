from __future__ import annotations

from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from .config import get_settings
from .db import ComplaintRepository
from .schemas import ComplaintListResponse, PredictRequest, PredictResponse
from .services.generative_ai import generate_acknowledgment, generate_suggestions
from .services.model import load_models


# Load a local .env if present (optional). In AWS Lambda, env vars come from AWS.
load_dotenv(override=False)


@lru_cache(maxsize=1)
def _repo() -> ComplaintRepository:
    settings = get_settings()
    return ComplaintRepository(db_path=settings.db_path)


@lru_cache(maxsize=1)
def _models() -> Any:
    settings = get_settings()
    return load_models(
        train_data_path=settings.train_data_path,
        category_model_path=settings.category_model_path,
        urgency_model_path=settings.urgency_model_path,
    )


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Real-Time Smart City Issue Detection API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/predict", response_model=PredictResponse)
    def predict(req: PredictRequest) -> PredictResponse:
        complaint_text = req.complaint

        category_model, urgency_model = _models()
        category = category_model.predict([complaint_text])[0]
        urgency = urgency_model.predict([complaint_text])[0]

        # "Generative AI" messages (templated)
        acknowledgment = generate_acknowledgment(category=category, urgency=urgency)  # type: ignore[arg-type]
        suggestions = generate_suggestions(category=category, urgency=urgency)  # type: ignore[arg-type]
        suggestion = " ".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))

        # Persist complaint (local demo). For AWS, swap repository to DynamoDB.
        _repo().create(text=complaint_text, category=category, urgency=urgency)

        return PredictResponse(
            category=category,  # type: ignore[arg-type]
            urgency=urgency,  # type: ignore[arg-type]
            acknowledgment=acknowledgment,
            suggestion=suggestion,
        )

    @app.get("/complaints", response_model=ComplaintListResponse)
    def list_complaints(
        category: str | None = Query(default=None),
        urgency: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=500),
    ) -> ComplaintListResponse:
        items = _repo().list(category=category, urgency=urgency, limit=limit)
        return ComplaintListResponse(items=items)

    return app


app = create_app()

# AWS Lambda entrypoint (API Gateway / ALB)
handler = Mangum(app)

