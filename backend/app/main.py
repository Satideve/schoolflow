# backend/app/main.py

"""
FastAPI app factory for SchoolFlow.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.db import session as dbsession

# Import the central API router aggregator
from app.api.v1.api import api_router


def create_app():
    setup_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    # CORS: allow local dev tools to call the API (e.g., swagger UI, frontend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all versioned API routers
    app.include_router(api_router)

    # attach DB engine/session for graceful shutdown if needed
    @app.on_event("startup")
    def startup_event():
        # Could start scheduler here
        pass

    @app.on_event("shutdown")
    def shutdown_event():
        dbsession.SessionLocal.remove()

    return app


app = create_app()
