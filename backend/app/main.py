from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mangum import Mangum

from app.core.config import get_settings
from app.routes import auth, dashboard, issues, ml

load_dotenv(override=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="2.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(issues.router, prefix=settings.api_prefix)
    app.include_router(dashboard.router, prefix=settings.api_prefix)
    app.include_router(ml.router, prefix=settings.api_prefix)

    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
handler = Mangum(app)
