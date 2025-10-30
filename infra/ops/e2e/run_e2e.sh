#!/usr/bin/env bash
# ops/e2e/run_e2e.sh
# Full E2E: start backend (targeting schoolflow_test_run), truncate test DB, seed, run tests,
# create invoice (manual payment), trigger payment webhook, download invoice+receipt PDFs.
# SAFE WARNING: truncates tables in database schoolflow_test_run.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/../../" && pwd)"
export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-infra}
DB_URL="postgresql://admin:admin@db:5432/schoolflow_test_run"
export DATABASE_URL="$DB_URL"

# Utilities
die(){ echo "ERROR: $*" >&2; exit 1; }
jq_check(){ command -v jq >/dev/null 2>&1 || die "jq is required. Install it (apt: jq / brew: jq / choco: jq)"; }

echo "E2E runner starting from $ROOT_DIR"
cd "$ROOT_DIR"

# 1) Stop backend if running to avoid port collisions, remove run containers
echo "-> Stopping any running backend container (best-effort)..."
docker compose stop backend >/dev/null 2>&1 || true
# remove leftover run containers (best-effort)
docker ps -a --filter "name=infra-backend-run" --format '{{.ID}}' | xargs -r docker rm -f || true

# 2) Start backend with explicit DATABASE_URL for schoolflow_test_run (detached)
echo "-> Starting backend (detached) with DATABASE_URL pointing to schoolflow_test_run..."
docker compose run -d --service-ports -e DATABASE_URL="$DB_URL" backend

# 3) Wait until /docs is reachable
echo "-> Waiting for backend /docs to be reachable..."
for i in $(seq 1 40); do
  if docker compose exec backend sh -c "curl -sSf http://localhost:8000/docs >/dev/null 2>&1" >/dev/null 2>&1; then
    echo "-> /docs reachable"
    break
  fi
  sleep 1
  echo -n "."
  if [ "$i" -eq 40 ]; then
    die "backend /docs not reachable after timeout"
  fi
done
echo

# 4) Truncate test tables (dangerous: this wipes data in schoolflow_test_run)
# echo "-> Truncating tables in schoolflow_test_run (RESTART IDENTITY CASCADE) — last chance to cancel (5s)..."
# sleep 5
# docker compose exec db psql -U admin -d schoolflow_test_run -c \
# "TRUNCATE receipt, payment, fee_assignment, fee_invoice, fee_plan_component, fee_component, fee_plan, students, class_sections, \"user\" RESTART IDENTITY CASCADE;"

# 5) Run seed loader
echo "-> Running seed loader to populate CSV seeds..."
docker compose exec backend sh -c "cd /app/backend && PYTHONPATH=/app/backend DATABASE_URL='$DB_URL' python ops/seeds/load_seeds.py"

# 6) Fix sequences (load_seeds should do this; included for safety)
echo "-> Ensuring sequences are synced (best-effort)..."
docker compose exec backend sh -c "cd /app/backend && PYTHONPATH=/app/backend DATABASE_URL='$DB_URL' python - <<'PY'
from sqlalchemy import create_engine, text
import os
DB=os.getenv('DATABASE_URL')
e=create_engine(DB)
tables = ['class_sections','students','user','fee_plan','fee_component','fee_plan_component','fee_assignment','fee_invoice','payment','receipt']
with e.connect() as c:
    for t in tables:
        try:
            seq = c.execute(text(f\"SELECT pg_get_serial_sequence('public.\"{t}\"','id')\")).scalar()
            if not seq:
                seq = c.execute(text(f\"SELECT pg_get_serial_sequence('{t}','id')\")).scalar()
            if not seq:
                print('no seq for',t); continue
            max_id = c.execute(text(f\"SELECT COALESCE(MAX(id),0) FROM {t}\")).scalar() or 0
            c.execute(text(f\"SELECT setval('{seq}', {int(max_id)}, true)\"))
            print('set',seq,'->',max_id)
        except Exception as e:
            print('skip',t, e)
PY"

# 7) Run unit tests (USE_REAL_DB=true to run against the test DB)
echo "-> Running pytest (USE_REAL_DB=true)..."
docker compose exec backend sh -c "cd /app/backend && PYTHONPATH=/app/backend DATABASE_URL='$DB_URL' USE_REAL_DB=true pytest -q --maxfail=1 --tb=short"

# 8) Register & login admin; obtain bearer token (requires jq)
jq_check
echo "-> Registering testadmin (noop if already exists) and logging in to get token..."
docker compose exec backend sh -c "cd /app/backend && python - <<'PY'
import requests, os, json
base='http://localhost:8000/api/v1'
# register
try:
    requests.post(base+'/auth/register', json={'email':'testadmin@example.com','password':'ChangeMe123!','full_name':'Test Admin','role':'admin'}, timeout=5)
except Exception:
    pass
# login
r=requests.post(base+'/auth/login', data={'username':'testadmin@example.com','password':'ChangeMe123!','grant_type':'password'}, timeout=5)
print(r.text)
PY"

# 9) Create an invoice (with manual payment) and capture its id
echo "-> Creating invoice with manual payment (server will return JSON including id)..."
CREATE_OUT=$(docker compose exec backend sh -c "cd /app/backend && python - <<'PY'
import requests, json
base='http://localhost:8000/api/v1'
payload = {
  'student_id': 2,
  'invoice_no': 'INV-AUTO-' + __import__('uuid').uuid4().hex[:8].upper(),
  'period': '2025-11',
  'amount_due': 3500.00,
  'due_date': '2025-11-30T00:00:00Z',
  'payment': {'provider':'manual','amount':3500.00,'status':'captured'}
}
r=requests.post(base+'/invoices/', json=payload, timeout=10)
print(r.text)
PY")
echo "Create response:"
echo "$CREATE_OUT"
INV_ID=$(echo "$CREATE_OUT" | jq -r '.id // empty')
[ -n "$INV_ID" ] || die "Could not find invoice id in create output"

# 10) Download invoice PDF
echo "-> Downloading invoice PDF for id $INV_ID"
docker compose exec backend sh -c "cd /app/backend && python - <<'PY'
import requests,sys
inv=$INV_ID
r=requests.get(f'http://localhost:8000/api/v1/invoices/{inv}/download', timeout=20)
open(f'/tmp/invoice_{inv}.pdf','wb').write(r.content)
print('/tmp/invoice_%s.pdf' % inv)
PY"
docker cp "$(docker compose ps -q backend)":/tmp/invoice_"$INV_ID".pdf ./invoice_"$INV_ID".pdf || true
echo "Invoice PDF saved as ./invoice_${INV_ID}.pdf (if docker cp failed, file exists inside container at /tmp)"

# 11) Trigger payment webhook (two acceptable formats: top-level invoice_id or nested data)
echo "-> Triggering payment webhook (top-level invoice_id payload)..."
WEBHOOK_OUT=$(docker compose exec backend sh -c "cd /app/backend && python - <<'PY'
import requests,json
base='http://localhost:8000/api/v1'
payload={'invoice_id': int($INV_ID),'event':'payment.captured','provider':'fake','provider_txn_id':'FAKE-TXN-%s'%$INV_ID,'amount':3500.00,'idempotency_key':'IDEMP-%s'%$INV_ID}
r=requests.post(base+'/payments/webhook', json=payload, timeout=10)
print(r.text)
PY")
echo "$WEBHOOK_OUT"

# 12) Find latest receipt id for the invoice
RECEIPT_ID=$(docker compose exec db psql -U admin -d schoolflow_test_run -t -c \
"SELECT r.id FROM receipt r JOIN payment p ON p.id = r.payment_id WHERE p.fee_invoice_id = $INV_ID ORDER BY r.id DESC LIMIT 1;" | tr -d '[:space:]')
if [ -z "$RECEIPT_ID" ]; then
  die "couldn't find receipt id for invoice $INV_ID"
fi
echo "Found receipt id: $RECEIPT_ID"

# 13) Download receipt PDF
echo "-> Downloading receipt PDF id $RECEIPT_ID"
docker compose exec backend sh -c "cd /app/backend && python - <<'PY'
import requests
rid=$RECEIPT_ID
r=requests.get(f'http://localhost:8000/api/v1/receipts/{rid}/download', timeout=20)
open(f'/tmp/receipt_{rid}.pdf','wb').write(r.content)
print('/tmp/receipt_%s.pdf' % rid)
PY"
docker cp "$(docker compose ps -q backend)":/tmp/receipt_"$RECEIPT_ID".pdf ./receipt_"$RECEIPT_ID".pdf || true
echo "Receipt PDF saved as ./receipt_${RECEIPT_ID}.pdf"

echo "E2E run complete. Files: ./invoice_${INV_ID}.pdf ./receipt_${RECEIPT_ID}.pdf"
EOF
