# Backend (FastAPI)

## Highlights
- JWT authentication with role-based authorization
- Secure password hashing
- Issue CRUD + workflow states (`Pending`, `Processing`, `Completed`)
- Authority-only status updates + resolution comments/image payload support
- Public analytics API
- Modular architecture (`routes`, `controllers`, `services`, `db`)

## Start backend
> Run from `backend/` directory.

### macOS/Linux
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Windows PowerShell
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger docs:
- `http://localhost:8000/docs`

Health:
- `GET /health`
