# C:\coding_projects\dev\schoolflow\infra\run_e2e.ps1
<#
run_e2e.ps1

Full E2E runner for SchoolFlow (PowerShell)

Purpose
-------
Automates the complete E2E flow against a local backend:
  - bring up DB + backend (backend started with DATABASE_URL pointed at schoolflow_test_run)
  - optionally truncate test DB tables (DANGEROUS; off by default)
  - run the idempotent seeder (ops/seeds/load_seeds.py) which also fixes sequences
  - optionally run pytest as a smoke check (USE_REAL_DB=true)
  - perform API E2E steps:
      * register admin (idempotent)
      * login (capture cookies & bearer token)
      * create invoice (with embedded manual payment so invoice/pdf/payment/receipt path is exercised)
      * download generated invoice PDF
      * post payment webhook to mark invoice paid (creates receipt)
      * download generated receipt PDF

Usage
-----
From repo root (where docker-compose.yml lives):
  PowerShell:
    ./run_e2e.ps1                # runs with defaults (runs tests, truncates DB)
    ./run_e2e.ps1 -RunTests:$false -TruncateDB:$false

Caveats and safety
------------------
 - By default this script WILL TRUNCATE the test DB (set -TruncateDB:$false to skip).
 - It tries 'docker compose run' to start a run container with an explicit DATABASE_URL.
   If that fails due to port binding/network issues it will fallback to 'docker compose up -d backend'.
 - Filenames and DB query outputs are aggressively trimmed to avoid spaces/newlines from psql output.
 - Requires docker-compose on PATH and running Docker Desktop (or equivalent).
 - Designed for local dev use only.
#>

param(
  [switch]$RunTests = $true,            # set -RunTests:$false to skip pytest run
  [switch]$TruncateDB = $true           # DANGEROUS: only enable if you want to wipe test DB and reseed; set $false to keep data
)

$ErrorActionPreference = "Stop"

# Configuration (change only if you know what you're doing)
$DB_URL = "postgresql://admin:admin@db:5432/schoolflow_test_run"
$BACKEND_SERVICE = "backend"
$DB_SERVICE = "db"
$BASE_URL = "http://localhost:8000"
$API_BASE = $BASE_URL                      # used by API calls below
$DOCS = "$BASE_URL/docs"
$MAX_WAIT_SECONDS = 60

function Info($m){ Write-Host "INFO: $m" }
function Err($m){ Write-Host "ERROR: $m" -ForegroundColor Red }

# ---- 1) Ensure DB container is up ----
Info "Starting DB container..."
docker compose up -d $DB_SERVICE | Out-Null

# ---- 2) Stop existing backend (if any) then start backend with explicit DATABASE_URL ----
try {
  Info "Stopping any existing backend container (if present)..."
  docker compose stop $BACKEND_SERVICE | Out-Null
} catch {
  # ignore errors stopping container
}

# Robust attempt to start a fresh backend run container with explicit DB env.
# If `docker compose run` fails due to port bind / networking, fall back to `docker compose up -d backend`.
Info "Starting backend in detached 'run' mode with DATABASE_URL set to test DB..."
$runCmd = "docker compose run -d --service-ports -e DATABASE_URL=`"$DB_URL`" $BACKEND_SERVICE"
Write-Host $runCmd

$runSucceeded = $false
try {
  # Invoke-Expression returns output; on success compose prints container id(s) or similar
  $runOutput = Invoke-Expression $runCmd 2>&1
  if ($LASTEXITCODE -eq 0 -or ($runOutput -match "^[0-9a-f]{8,}" -or $runOutput -match "Creating")) {
    $runSucceeded = $true
    Info "docker compose run succeeded (container started or created)."
  } else {
    Write-Host "WARN: docker compose run returned non-success output:"
    Write-Host $runOutput
  }
} catch {
  Write-Host "WARN: docker compose run failed with exception: $($_.Exception.Message)"
}

if (-not $runSucceeded) {
  Write-Host "INFO: Falling back to 'docker compose up -d backend' (reusing existing backend container if present)."
  try {
    docker compose up -d $BACKEND_SERVICE | Out-Null
    Info "'docker compose up -d backend' executed."
  } catch {
    Err "Failed to start backend with fallback 'docker compose up -d backend': $($_.Exception.Message)"
    throw
  }
}

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
    } else {
      # Even if DATABASE_URL didn't show (some compose starts may not propagate env), still check /docs once
      try {
        Invoke-WebRequest -Uri $DOCS -UseBasicParsing -TimeoutSec 3 | Out-Null
        Info "/docs reachable (even if DB env not shown)"
        break
      } catch {
        # not up yet
      }
    }
  } catch {
    # container might not be ready yet; ignore and retry
  }
  Start-Sleep -Seconds 1
}
if ((Get-Date) -ge $deadline) {
  Err "Backend didn't become healthy or /docs unreachable within $MAX_WAIT_SECONDS seconds."
  docker compose logs --no-color $BACKEND_SERVICE | Select-Object -Last 200
  exit 2
}

# ---- Optional: TRUNCATE DB (dangerous) ----
# This block is robust to PowerShell quoting and captures stdout/stderr reliably.
# if ($TruncateDB) {
#   Info "WARNING: Truncating test DB tables (RESTART IDENTITY CASCADE)..."

#   # Stop any backend containers (avoid race where an old backend writes while we truncate)
#   try {
#     Info "Stopping backend containers to avoid races..."
#     docker compose stop $BACKEND_SERVICE | Out-Null
#   } catch {
#     # ignore stop errors but log
#     Err "Warning: unable to stop backend container (non-fatal): $($_.Exception.Message)"
#   }

#   Start-Sleep -Seconds 1

#   # Helper to run a psql query and return output as string (captures stdout/stderr).
#   function Run-PSQL {
#     param(
#       [string]$sql
#     )
#     # Escape single quotes for safe single-quote wrapper in the docker/psql command
#     $escapedSql = $sql -replace "'", "''"

#     # Build command string; wrap SQL in single-quotes so double-quotes inside SQL can be preserved
#     $cmd = "docker compose exec $DB_SERVICE psql -U admin -d schoolflow_test_run -t -A -c '$escapedSql'"
#     Write-Host "DEBUG: Running: $cmd"
#     try {
#       $out = Invoke-Expression $cmd 2>&1
#       return @{ Success = $true; Output = ($out -join "`n") }
#     } catch {
#       return @{ Success = $false; Output = $_.Exception.Message }
#     }
#   }

#   # Show counts before truncate
#   Info "DEBUG: Counts BEFORE truncate (payment / receipt / fee_invoice / students)..."
#   $pre_payment  = Run-PSQL -sql "SELECT COUNT(*) FROM payment;"
#   $pre_receipt  = Run-PSQL -sql "SELECT COUNT(*) FROM receipt;"
#   $pre_invoice  = Run-PSQL -sql "SELECT COUNT(*) FROM fee_invoice;"
#   $pre_students = Run-PSQL -sql "SELECT COUNT(*) FROM students;"
#   Write-Host "PRE truncate: payment=`$($pre_payment.Output.Trim())`, receipt=`$($pre_receipt.Output.Trim())`, invoice=`$($pre_invoice.Output.Trim())`, students=`$($pre_students.Output.Trim())`"

#   # The safe truncate SQL — uses the working quoting form you confirmed
#   $truncateSql = 'TRUNCATE receipt, payment, fee_assignment, fee_invoice, fee_plan_component, fee_component, fee_plan, students, class_sections, "\"user\"" RESTART IDENTITY CASCADE;'

#   # Run truncate and capture the result
#   Info "Executing TRUNCATE..."
#   $truncateResult = Run-PSQL -sql $truncateSql
#   if (-not $truncateResult.Success) {
#     Err "Truncate failed: $($truncateResult.Output)"
#     Err "Aborting E2E run. Please inspect DB and retry."
#     exit 3
#   } else {
#     Info "Truncate command executed. psql output (first 400 chars):"
#     $outSnippet = $truncateResult.Output.ToString()
#     if ($outSnippet.Length -gt 400) { $outSnippet = $outSnippet.Substring(0,400) + "..." }
#     Write-Host $outSnippet
#   }

#   Start-Sleep -Seconds 1

#   # Show counts after truncate
#   Info "DEBUG: Counts AFTER truncate (payment / receipt / fee_invoice / students)..."
#   $post_payment  = Run-PSQL -sql "SELECT COUNT(*) FROM payment;"
#   $post_receipt  = Run-PSQL -sql "SELECT COUNT(*) FROM receipt;"
#   $post_invoice  = Run-PSQL -sql "SELECT COUNT(*) FROM fee_invoice;"
#   $post_students = Run-PSQL -sql "SELECT COUNT(*) FROM students;"
#   Write-Host "POST truncate: payment=`$($post_payment.Output.Trim())`, receipt=`$($post_receipt.Output.Trim())`, invoice=`$($post_invoice.Output.Trim())`, students=`$($post_students.Output.Trim())`"

#   # Verify we actually cleared the key tables (abort if not zero)
#   if (($post_payment.Output.Trim() -ne '0') -or ($post_receipt.Output.Trim() -ne '0') -or ($post_invoice.Output.Trim() -ne '0')) {
#     Err "Truncate did NOT clear tables as expected. Aborting."
#     Err "If you intentionally want to keep data, re-run with -TruncateDB:$false."
#     exit 4
#   }

#   Info "Truncate complete."
# }
#   # end of ($TruncateDB)

# ---- 3) Run seed script inside backend container (ensures sequences fixed as load_seeds includes fix) ----
Info "Running load_seeds.py (idempotent seeding + sequence fix)..."
$seedCmd = "cd /app/backend ; PYTHONPATH=/app/backend DATABASE_URL=$DB_URL python ops/seeds/load_seeds.py"
docker compose exec $BACKEND_SERVICE sh -c $seedCmd

# ---- 4) Optionally run pytest (fast smoke) ----
if ($RunTests) {
  Info "Running pytest (USE_REAL_DB=true) - will use test DB"
  $pytestCmd = "cd /app/backend ; PYTHONPATH=/app/backend DATABASE_URL=$DB_URL USE_REAL_DB=true pytest -q --maxfail=1 --tb=short"
  docker compose exec $BACKEND_SERVICE sh -c $pytestCmd
}

# ---- 5) Perform E2E API steps (register -> login -> create invoice -> download invoice -> webhook -> download receipt) ----
Info "Starting API E2E steps (register -> login -> create invoice -> download invoice -> webhook -> download receipt)"

# 5.1 Register admin (idempotent)
$regBody = @{
  email     = "testadmin@example.com"
  password  = "ChangeMe123!"
  full_name = "Test Admin"
  role      = "admin"
}
try {
  $regResp = Invoke-RestMethod -Uri "$API_BASE/api/v1/auth/register" -Method Post -Body ($regBody | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
  Write-Host "INFO: Register: created or returned: $($regResp.id) $($regResp.email)"
} catch {
  Write-Host "INFO: Register: already exists or ignored (continuing)"
}

# 5.2 Login: capture cookie session AND bearer token (preferred)
$loginBody = @{ grant_type="password"; username="testadmin@example.com"; password="ChangeMe123!" }

# create an explicit session object for cookie storage
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

try {
  $loginResp = Invoke-RestMethod -Uri "$API_BASE/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded" -WebSession $session -ErrorAction Stop
  $token = $null
  if ($loginResp -and $loginResp.access_token) {
    $token = $loginResp.access_token
    Write-Host "INFO: Logged in, obtained bearer token (length $($token.Length)) and stored cookies in session."
  } else {
    Write-Host "WARN: Login response did not contain access_token; continuing with cookie session only."
  }
} catch {
  Err "Login failed: $($_.Exception.Message)"
  throw
}

# Helper function: download using cookie session first, then bearer token fallback
function Download-WithSessionOrToken {
  param(
    [string]$Url,
    [string]$OutFile
  )
  # Try cookie session first
  if ($session) {
    try {
      Invoke-WebRequest -Uri $Url -Method Get -WebSession $session -OutFile $OutFile -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
      return $true
    } catch {
      Write-Host "WARN: cookie-based download failed for $Url; will try bearer token fallback."
    }
  }

  if ($token) {
    try {
      Invoke-WebRequest -Uri $Url -Method Get -Headers @{ Authorization = "Bearer $token" } -OutFile $OutFile -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
      return $true
    } catch {
      Write-Host "ERROR: download failed with bearer token: $($_.Exception.Message)"
      return $false
    }
  }

  Write-Host "ERROR: No session or token available to download $Url"
  return $false
}

# 5.3 Create invoice (with manual payment) — use bearer token if available
$invoicePayload = @{
  student_id = 2
  invoice_no = "INV-AUTO-" + ([guid]::NewGuid().ToString().Substring(0,8).ToUpper())
  period     = "2025-11"
  amount_due = 3500.00
  due_date   = (Get-Date -Year 2025 -Month 11 -Day 30).ToString("s")
  payment    = @{ provider="manual"; amount=3500.00; status="captured" }
}
$createHeaders = @{}
if ($token) { $createHeaders.Add("Authorization","Bearer $token") }

try {
  $createResp = Invoke-RestMethod -Uri "$API_BASE/api/v1/invoices/" -Method Post -Body ($invoicePayload | ConvertTo-Json) -ContentType "application/json" -Headers $createHeaders -ErrorAction Stop
  $invId = $createResp.id
  Write-Host "INFO: Created invoice id = $invId"
} catch {
  Err "Create invoice failed: $($_.Exception.Message)"
  throw
}

# 5.4 Download invoice PDF (cookie session preferred, fallback to token)
$outInv = ("invoice_{0}.pdf" -f $invId).Replace(" ", "")
$invDownloadUrl = "$API_BASE/api/v1/invoices/$invId/download"
Write-Host "INFO: Downloading invoice PDF from $invDownloadUrl -> $outInv ..."
if (-not (Download-WithSessionOrToken -Url $invDownloadUrl -OutFile $outInv)) {
  Err "Failed to download invoice PDF"
  throw "Invoice download failed"
}
Write-Host "INFO: Downloaded invoice PDF to $outInv"

# 5.5 Trigger payment webhook (top-level invoice_id shape)
$webhookTop = @{
  invoice_id = $invId
  event = "payment.captured"
  provider = "fake"
  provider_txn_id = "FAKE-TXN-$invId"
  amount = 3500.00
  idempotency_key = "IDEMP-$invId"
} | ConvertTo-Json -Depth 5

try {
  $webResp = Invoke-RestMethod -Uri "$API_BASE/api/v1/payments/webhook" -Method Post -Body $webhookTop -ContentType "application/json" -ErrorAction Stop
  Write-Host "INFO: Webhook response:"; $webResp | ConvertTo-Json -Depth 5
} catch {
  if ($_.Exception.Response) {
    try {
      $stream = $_.Exception.Response.GetResponseStream()
      $sr = New-Object System.IO.StreamReader($stream)
      $body = $sr.ReadToEnd()
      Err "Webhook post failed; response body: $body"
    } catch {
      Err "Webhook post failed; could not read response body: $($_.Exception.Message)"
    }
  } else {
    Err "Webhook post failed: $($_.Exception.Message)"
  }
  throw
}

# 5.6 Wait briefly for DB work to complete then fetch receipt id created for this invoice
Start-Sleep -Seconds 1
$ridQuery = "SELECT id FROM receipt WHERE payment_id IN (SELECT id FROM payment WHERE fee_invoice_id = $invId) ORDER BY id DESC LIMIT 1;"
$ridRaw = docker compose exec $DB_SERVICE psql -U admin -d schoolflow_test_run -t -c "$ridQuery" 2>$null
if ($null -eq $ridRaw) { $ridRaw = "" }
$rid = ($ridRaw -replace '\s','').Trim()
if (-not $rid) {
  Err "Could not find receipt for invoice $invId (raw: '$ridRaw')"
  throw "No receipt"
}
Write-Host "INFO: Found receipt id = $rid"

# 5.7 Download receipt PDF (cookie session preferred, fallback token)
$outRec = ("receipt_{0}.pdf" -f $rid).Replace(" ", "")
$recDownloadUrl = "$API_BASE/api/v1/receipts/$rid/download"
Write-Host "INFO: Downloading receipt PDF from $recDownloadUrl -> $outRec ..."
if (-not (Download-WithSessionOrToken -Url $recDownloadUrl -OutFile $outRec)) {
  Err "Failed to download receipt PDF"
  throw "Receipt download failed"
}
Write-Host "INFO: Downloaded receipt PDF to $outRec"

Info "E2E run complete. Files: $outInv, $outRec"

# End of script
