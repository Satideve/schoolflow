# backend/app/api/v1/routers/health.py
from fastapi import APIRouter, Depends
from app.db.session import engine
from sqlalchemy.exc import OperationalError
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/health", tags=["health"])
logger = get_logger("health")

# @router.get("/")
# def root_health():
#     return {"status": "ok", "endpoints": ["/liveness", "/readiness"]}


@router.get("/liveness")
def liveness():
    return {"status": "ok", "uptime": True}

from sqlalchemy import text

@router.get("/readiness")
def readiness():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except OperationalError as e:
        logger.error("DB connection failed")
        return {"status": "not ready", "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "error": str(e)}

