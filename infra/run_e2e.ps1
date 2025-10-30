# C:\coding_projects\dev\schoolflow\infra\run_e2e.ps1
# Full E2E runner for SchoolFlow (PowerShell)
# - safe / idempotent: will not truncate unless you uncomment the dangerous block
# - uses DATABASE_URL=postgresql://admin:admin@db:5432/schoolflow_test_run
# - requires docker-compose and the repo to be at the current working directory

param(
  [switch]$RunTests = $true,            # set -RunTests:$false to skip pytest run
  [switch]$TruncateDB = $false          # DANGEROUS: only enable if you want to wipe test DB and reseed
)

$ErrorActionPreference = "Stop"

$DB_URL = "postgresql://admin:admin@db:5432/schoolflow_test_run"
$BACKEND_SERVICE = "backend"
$DB_SERVICE = "db"
$HOST = "http://localhost:8000"
$DOCS = "$HOST/docs"
$MAX_WAIT_SECONDS = 60

function Info($m){ Write-Host "INFO: $m" }
function Err($m){ Write-Host "ERROR: $m" -ForegroundColor Red }

# 1) Ensure DB container is up
Info "Starting DB container..."
docker compose up -d $DB_SERVICE | Out-Null

# 2) Stop any running backend to avoid port collisions, then start backend with explicit DATABASE_URL
try {
  Info "Stopping any existing backend container (if present)..."
  docker compose stop $BACKEND_SERVICE | Out-Null
} catch {
  # ignore
}

Info "Starting backend in detached 'run' mode with DATABASE_URL set to test DB..."
# use docker compose run -d --service-ports -e DATABASE_URL=... backend
$runCmd = "docker compose run -d --service-ports -e DATABASE_URL=`"$DB_URL`" $BACKEND_SERVICE"
Write-Host $runCmd
Invoke-Expression $runCmd | Out-Null

# Wait until backend container env shows correct DATABASE_URL and /docs reachable
$deadline = (Get-Date).AddSeconds($MAX_WAIT_SECONDS)
while((Get-Date) -lt $deadline) {
  try {
    $envOut = docker compose exec $BACKEND_SERVICE sh -c 'echo $DATABASE_URL || true' 2>$null
    if ($envOut -and $envOut.Trim() -eq $DB_URL) {
      Info "/docs check..."
      try {
        Invoke-WebRequest -Uri $DOCS -UseBasicParsing -TimeoutSec 3 | Out-Null
        Info "/docs reachable"
        break
      } catch {
        # not up yet
      }
    }
  } catch {
    # container might not be ready yet
  }
  Start-Sleep -Seconds 1
}
if ((Get-Date) -ge $deadline) {
  Err "Backend didn't become healthy or /docs unreachable within $MAX_WAIT_SECONDS seconds."
  docker compose logs --no-color $BACKEND_SERVICE | Select-Object -Last 200
  exit 2
}

# Optional: TRUNCATE DB (commented by default)
if ($TruncateDB) {
  Write-Host "WARNING: Truncating test DB tables (RESTART IDENTITY CASCADE)..."
  Start-Sleep -Seconds 3
  $truncateSql = 'TRUNCATE receipt, payment, fee_assignment, fee_invoice, fee_plan_component, fee_component, fee_plan, students, class_sections, "user" RESTART IDENTITY CASCADE;'
  docker compose exec $DB_SERVICE psql -U admin -d schoolflow_test_run -c $truncateSql
  Info "Truncate complete."
}

# 3) Run seed script inside backend container (ensures sequences fixed as load_seeds includes fix)
Info "Running load_seeds.py (idempotent seeding + sequence fix)..."
$seedCmd = "cd /app/backend && PYTHONPATH=/app/backend DATABASE_URL=$DB_URL python ops/seeds/load_seeds.py"
docker compose exec $BACKEND_SERVICE sh -c $seedCmd

# 4) Optionally run pytest (fast smoke)
if ($RunTests) {
  Info "Running pytest (USE_REAL_DB=true) - will use test DB"
  $pytestCmd = "cd /app/backend && PYTHONPATH=/app/backend DATABASE_URL=$DB_URL USE_REAL_DB=true pytest -q --maxfail=1 --tb=short"
  docker compose exec $BACKEND_SERVICE sh -c $pytestCmd
}

# 5) Perform E2E API steps with PowerShell:
#    register admin (noop if exists), login (get token), create invoice with manual payment,
#    download invoice PDF, trigger webhook (payment.captured), download receipt PDF.
Info "Starting API E2E steps (register -> login -> create invoice -> download invoice -> webhook -> download receipt)"

# 5.1 register (safe-if-exists)
$registerBody = @{
  email = "testadmin@example.com"
  password = "ChangeMe123!"
  full_name = "Test Admin"
  role = "admin"
}
try {
  $regResp = Invoke-RestMethod -Uri "$HOST/api/v1/auth/register" -Method Post -Body ($registerBody | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
  Info "Registered admin: $($regResp.email) (id=$($regResp.id))"
} catch {
  # If already exists, the API returns 400; still proceed
  Info "Register: already exists or ignored (continuing)"
}

# 5.2 login -> pick token
$loginBody = @{ grant_type = "password"; username = "testadmin@example.com"; password = "ChangeMe123!" }
$loginResp = Invoke-RestMethod -Uri "$HOST/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded"
$token = $loginResp.access_token
if (-not $token) { Err "Login failed, no access_token"; exit 3 }
Info "Logged in; token obtained (len=$($token.Length))"

# 5.3 create invoice with manual payment (API will create invoice + payment => invoice status paid)
$invoicePayload = @{
  student_id = 2
  invoice_no = "INV-AUTO-" + ([guid]::NewGuid().ToString().Substring(0,8).ToUpper())
  period = "2025-11"
  amount_due = 3500.00
  due_date = (Get-Date -Year 2025 -Month 11 -Day 30).ToString("s")
  payment = @{
    provider = "manual"
    amount = 3500.00
    status = "captured"
  }
}
$createResp = Invoke-RestMethod -Uri "$HOST/api/v1/invoices/" -Method Post -Body ($invoicePayload | ConvertTo-Json) -ContentType "application/json" -Headers @{ Authorization = "Bearer $token" }
$invId = $createResp.id
Info "Created invoice id = $invId (invoice_no=$($createResp.invoice_no), status=$($createResp.status))"

# 5.4 Download invoice PDF (bearer)
$outInvoice = "invoice_$invId.pdf"
Invoke-WebRequest -Uri "$HOST/api/v1/invoices/$invId/download" -Method Get -Headers @{ Authorization = "Bearer $token" } -OutFile $outInvoice
Info "Downloaded invoice PDF -> $outInvoice (size = $((Get-Item $outInvoice).Length) bytes)"

# 5.5 Post payment webhook (top-level invoice_id or data.invoice_id accepted by the webhook)
# Use a fake provider and idempotency key
$webhookTop = @{
  invoice_id = $invId
  event = "payment.captured"
  provider = "fake"
  provider_txn_id = "FAKE-TXN-$invId"
  amount = 3500.00
  idempotency_key = "IDEMP-$invId"
}
$webResp = Invoke-RestMethod -Uri "$HOST/api/v1/payments/webhook" -Method Post -Body ($webhookTop | ConvertTo-Json) -ContentType "application/json"
Info "Webhook response: $($webResp | ConvertTo-Json -Depth 5)"

# 5.6 find latest receipt id for this invoice (via psql)
$psqlCmd = "SELECT id FROM receipt WHERE payment_id IN (SELECT id FROM payment WHERE fee_invoice_id = $invId) ORDER BY id DESC LIMIT 1;"
$ridRaw = docker compose exec $DB_SERVICE psql -U admin -d schoolflow_test_run -t -c $psqlCmd
$rid = ($ridRaw -replace '\s','')
if (-not $rid) { Err "Could not find receipt id for invoice $invId"; exit 4 }
Info "Found receipt id = $rid"

# 5.7 download receipt PDF
$outReceipt = "receipt_$rid.pdf"
Invoke-WebRequest -Uri "$HOST/api/v1/receipts/$rid/download" -Method Get -Headers @{ Authorization = "Bearer $token" } -OutFile $outReceipt
Info "Downloaded receipt PDF -> $outReceipt (size = $((Get-Item $outReceipt).Length) bytes)"

Info "E2E run complete. Invoice id=$invId, Receipt id=$rid"
exit 0
