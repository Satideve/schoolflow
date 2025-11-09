# infra/ops/backend-python.ps1
[CmdletBinding()]
param(
  [string]$Code,
  [string]$File,
  [switch]$UseRealDb = $true,
  [string]$DatabaseUrl = "postgresql://admin:admin@db:5432/schoolflow_test_run"
)

$envs = @()
if ($UseRealDb) { $envs += "USE_REAL_DB=true" }
if ($DatabaseUrl) { $envs += "DATABASE_URL=$DatabaseUrl" }
$envs += "PYTHONPATH=/app/backend"

if ($File) {
  if (-not (Test-Path $File)) { throw "File not found: $File" }
  $Code = Get-Content -Raw -LiteralPath $File
}
if (-not $Code) { throw "Provide -Code '...' or -File path" }

# Pipe code via STDIN to avoid quoting issues on Windows
$Code | docker compose exec -T backend sh -lc "$($envs -join ' ') python -"
