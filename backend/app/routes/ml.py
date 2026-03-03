from __future__ import annotations

from fastapi import APIRouter

from app.schemas.ml import PredictRequest, PredictResponse
from app.services.model_inference import classify_complaint

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    return classify_complaint(payload.complaint)
