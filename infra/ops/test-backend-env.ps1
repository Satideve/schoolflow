# Resolve script directory reliably (works no matter where you run it from)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir  # goes from ops/ -> infra/
$ProjectRoot = Split-Path -Parent $ProjectRoot # infra/ -> project root

# Ensure the helper exists
$helper = Join-Path $ScriptDir "backend-python.ps1"
if (-not (Test-Path $helper)) {
    Write-Error "backend-python.ps1 not found at $helper"
    exit 1
}

Write-Host "Project root detected as: $ProjectRoot"
Write-Host "Using helper: $helper"

# Actually run the Python snippet
& $helper -Code @'
from app.db.session import SessionLocal
from app.core.config import settings
from sqlalchemy import text

db = SessionLocal()
try:
    r = db.execute(text("SELECT NOW()")).fetchone()
    print("DB OK -> NOW():", r[0])
finally:
    db.close()
'@
