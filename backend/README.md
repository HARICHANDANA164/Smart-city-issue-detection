# Backend (FastAPI)

## Highlights
- JWT authentication with role-based authorization
- Bcrypt password hashing
- Issue CRUD + workflow states (`Pending`, `Processing`, `Completed`)
- Authority-only status updates + resolution uploads/comments
- Public analytics API
- Modular architecture (`routes`, `controllers`, `services`, `db`)

## Start backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger docs:
- `http://localhost:8000/docs`

Health:
- `GET /health`
