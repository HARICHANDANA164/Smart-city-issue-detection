# Backend (FastAPI)

## Endpoints
- `POST /predict` → classify complaint, urgency, AI messages, store record
- `GET /complaints` → list submitted complaints (supports `category`, `urgency`)
- `GET /health` → health check

## Local run

1) Create a venv + install deps:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
```

2) (Optional) set environment variables (see `backend/env.example`).

3) Start API:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## ML models
This backend expects two model artifacts:
- `models/artifacts/category_model.joblib`
- `models/artifacts/urgency_model.joblib`

If they don't exist, the backend will train them on first run using `TRAIN_DATA_PATH`
(default: `data/nyc_311_subset.csv`).

## AWS Lambda readiness
- The Lambda handler is `backend.app.main:handler` (powered by Mangum).
- Use env vars for config (`CATEGORY_MODEL_PATH`, `URGENCY_MODEL_PATH`, `DB_PATH`, etc.).
- For real cloud deployment, replace SQLite repository with DynamoDB (same API contract).

