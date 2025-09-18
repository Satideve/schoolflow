# backend/app/main.py

"""
FastAPI app factory for SchoolFlow.
"""

from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging

from app.api.v1.routers import auth, health, class_sections, students
from app.api.v1.routers.fees import plans, invoices, payments
from app.api.v1.routers import pdf  # ✅ Added PDF route
from app.db import session as dbsession

def create_app():
    setup_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    # Include routers
    app.include_router(auth.router)
    app.include_router(health.router)
    app.include_router(plans.router)
    app.include_router(invoices.router)
    app.include_router(payments.router)
    app.include_router(class_sections.router)
    app.include_router(students.router)
    app.include_router(pdf.router)  # ✅ Register PDF route

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
