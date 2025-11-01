# C:\coding_projects\dev\schoolflow\infra\ops\e2e\truncate_test_db.ps1
param(
  [string]$DbName = "schoolflow_test_run"
)

Write-Host "INFO: Truncating test DB: $DbName (RESTART IDENTITY CASCADE)"
try {
  # stop backend container to avoid races
  Write-Host "INFO: stopping backend..."
  docker compose stop backend | Out-Null
} catch {
  Write-Host "WARN: could not stop backend (continuing): $($_.Exception.Message)"
}

Start-Sleep -Seconds 1

# Run the known-working single-line truncation (matches your manual command)
docker compose exec db psql -U admin -d $DbName -c 'TRUNCATE receipt, payment, fee_assignment, fee_invoice, fee_plan_component, fee_component, fee_plan, students, class_sections, "\"user\"" RESTART IDENTITY CASCADE;'

# Print quick counts to confirm
Write-Host "INFO: post-truncate counts:"
docker compose exec db psql -U admin -d $DbName -c "SELECT 'students', COUNT(*) FROM students;"
docker compose exec db psql -U admin -d $DbName -c "SELECT 'fee_invoice', COUNT(*) FROM fee_invoice;"
docker compose exec db psql -U admin -d $DbName -c "SELECT 'payment', COUNT(*) FROM payment;"
docker compose exec db psql -U admin -d $DbName -c "SELECT 'receipt', COUNT(*) FROM receipt;"

Write-Host "INFO: truncate script finished."
