# backend/app/api/v1/routers/health.py
from fastapi import APIRouter, Depends
from app.db.session import engine
from sqlalchemy.exc import OperationalError
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/health", tags=["health"])
logger = get_logger("health")

@router.get("/liveness")
def liveness():
    return {"status": "ok", "uptime": True}

@router.get("/readiness")
def readiness():
    # simple DB ping
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ready"}
    except OperationalError as e:
        logger.error("DB connection failed")
        return {"status": "not ready", "error": str(e)}
