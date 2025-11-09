# Quick test: verifies Python, imports, DB connection all work.
.\infra\ops\backend-python.ps1 -Code @'
from app.db.session import SessionLocal
from app.core.config import settings
from sqlalchemy import text

print("PYTHONPATH:", settings.base_dir if hasattr(settings, "base_dir") else "<none>")

db = SessionLocal()
try:
    r = db.execute(text("SELECT NOW()")).fetchone()
    print("DB OK -> NOW():", r[0])
finally:
    db.close()
'@
