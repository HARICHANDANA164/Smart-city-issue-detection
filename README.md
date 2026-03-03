# Smart City Issue Detection (Production-Ready Upgrade)

Full-stack issue reporting platform with JWT auth, role-based workflows, analytics, and map-aware reporting.

## Tech Stack
- Backend: FastAPI + SQLite (easy PostgreSQL migration path)
- Frontend: React (Vite) + Tailwind utility classes
- ML: Existing category/urgency classifier preserved via `/api/v1/ml/predict`

## Folder Structure
- `backend/app/core` - settings + security (JWT + password hashing)
- `backend/app/routes` - REST routes
- `backend/app/controllers` - route orchestration layer
- `backend/app/services` - domain logic
- `backend/app/db` - persistence layer
- `backend/uploads` - issue and resolution images
- `frontend/src` - responsive dashboards + report form + map embed

## API Endpoints
Base: `/api/v1`

### Authentication
- `POST /auth/register` - register (`citizen` or `authority`)
- `POST /auth/login` - login and receive JWT token

### Issues
- `POST /issues` - create issue (JSON: title, description, category, lat/lng, optional `image_base64`)
- `GET /issues` - public list with filters (`status`, `category`, `search`, `page`, `page_size`)
- `DELETE /issues/{issue_id}` - delete own issue (or any if authority)
- `PATCH /issues/{issue_id}/status` - authority-only status update with optional `resolution_image_base64` and comment
- `GET /issues/{issue_id}/updates` - status timeline for tracking

### Dashboard / Analytics
- `GET /dashboard/analytics` - totals (`total_issues`, `pending`, `completed`)

### ML
- `POST /ml/predict` - complaint classification (category + urgency)

### Other
- `GET /health` - health check
- `GET /uploads/...` - uploaded image serving

---

## Run on your desktop (clear step-by-step)

### Prerequisites
- Python **3.10+**
- Node.js **18+** and npm
- Git

### 1) Clone and open project
```bash
git clone <your-repo-url>
cd Smart-city-issue-detection
```

### 2) Backend setup/start
> Important: run backend commands **inside `backend/`** so imports resolve correctly.

#### macOS/Linux
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Windows (PowerShell)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be live at:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### 3) Frontend setup/start (new terminal)
```bash
cd frontend
npm install
```

#### macOS/Linux
```bash
export VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev -- --host 0.0.0.0 --port 5173
```

#### Windows (PowerShell)
```powershell
$env:VITE_API_BASE_URL="http://localhost:8000/api/v1"
npm run dev -- --host 0.0.0.0 --port 5173
```

Frontend:
- `http://localhost:5173`

### 4) Quick functional check
1. Register a **citizen** account.
2. Create an issue.
3. Register another account as **authority**.
4. Login as authority and update issue status.
5. Verify analytics cards update.

## Optional Enhancements Included
- Image preview before upload
- Pagination (`page`, `page_size`) on issue listing
- Status history endpoint usable for notification/timeline UIs
