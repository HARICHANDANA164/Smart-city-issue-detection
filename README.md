# Smart City Issue Detection (Production-Ready Upgrade)

Full-stack issue reporting platform with JWT auth, role-based workflows, analytics, and map-aware reporting.

## Tech Stack
- Backend: FastAPI + SQLite (easy PostgreSQL migration path)
- Frontend: React (Vite) + Tailwind utility classes
- ML: Existing category/urgency classifier preserved via `/api/v1/ml/predict`

## Folder Structure
- `backend/app/core` - settings + security (JWT, bcrypt)
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

## Run Locally

### 1) Backend
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
# Optional: export VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev -- --host 0.0.0.0 --port 5173
```

## Optional Enhancements Included
- Image preview before upload
- Pagination (`page`, `page_size`) on issue listing
- Status history endpoint usable for notification/timeline UIs
