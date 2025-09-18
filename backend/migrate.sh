#!/bin/sh

# migrate.sh — upgrade DB, autogenerate a new Alembic migration, then apply it
# Place this in: backend/migrate.sh

set -e   # Exit on any error

echo "🔄 Setting PYTHONPATH..."
export PYTHONPATH=/app/backend

echo "🔧 Ensuring 'public' schema is owned by admin..."
docker exec infra-db-1 psql -U admin -d schoolflow -c "ALTER SCHEMA public OWNER TO admin;" || {
  echo "❌ Failed to alter schema ownership"
  exit 1
}

echo "📦 Upgrading DB to latest revision..."
alembic upgrade head

echo "🛠️ Autogenerating migration: $1"
alembic revision --autogenerate -m "$1"

echo "✨ Applying the newly created migration..."
alembic upgrade head

echo "🎉 Done. Your DB is current and migration is applied."

echo "🌱 Running seed loader..."
docker exec infra-backend-1 sh -c "
  PYTHONPATH=/app/backend python3 /app/backend/ops/seeds/load_seeds.py
"
