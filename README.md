# Real-Time Smart City Issue Detection and AI-Assisted Resolution System

A demo-ready full-stack project:
- **2x ML models** (TF‑IDF + Logistic Regression):
  - **Category** classification
  - **Urgency** prediction (`Low` / `Medium` / `High`) trained from **pseudo-labels**
- **FastAPI** backend (AWS Lambda / API Gateway ready via Mangum)
- **React (Vite)** frontend:
  - Citizen complaint submission
  - Authority dashboard with filters
- **SQLite** persistence for local demo (easy to swap to DynamoDB)

## Folder structure
- `frontend/` React UI
- `backend/` FastAPI API (Lambda-compatible handler included)
- `models/` ML download + training scripts (2 models)
- `data/` sample NYC 311 subsets (CSV) + SQLite DB (created at runtime)

## Local run (quickstart)

### 1) Backend

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will load model artifacts from `models/artifacts/`.
If missing, it will train them on first run using `TRAIN_DATA_PATH` (default: `data/nyc_311_subset.csv`).

### 2) Frontend

```bash
cd frontend
npm install

# PowerShell:
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev
```

Open the dev server URL shown in the terminal.

## API

### POST `/predict`
Input:
```json
{ "complaint": "Water main leak flooding the street near 5th Ave." }
```

Output:
```json
{
  "category": "Water & Drainage",
  "urgency": "High",
  "acknowledgment": "...",
  "suggestion": "..."
}
```

### GET `/complaints`
Returns stored complaints for the Authority Dashboard.
Optional query params: `category`, `urgency`.

## Train models (optional / recommended)

You can download a bigger subset of NYC 311 and train both models:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r models/requirements.txt

python models/download_nyc_311_subset.py
python models/train_models.py
```

## AWS readiness notes

- **Stateless API**: `/predict` uses saved model artifacts and request text only.
- **Environment variables**:
  - `CATEGORY_MODEL_PATH`
  - `URGENCY_MODEL_PATH`
  - `TRAIN_DATA_PATH`
  - `DB_PATH`
  - `ALLOWED_ORIGINS`
- **Lambda handler**: `backend.app.main:handler`
- **Storage swap**: replace `backend/app/db.py` repository with DynamoDB (schema is simple: `id`, `created_at`, `text`, `category`, `urgency`).

