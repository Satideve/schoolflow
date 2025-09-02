# backend/migrations/env.py

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, inspect

# ------------------------------------------------------------------------------
# 1) Project Setup: add root to path + load .env
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
load_dotenv(dotenv_path=BASE_DIR / ".env")

# print(">>> LOADED ENV.PY:", __file__)
# print(">>> sys.path[0]:", sys.path[0])

# ------------------------------------------------------------------------------
# 2) Import your Base and all model classes
# ------------------------------------------------------------------------------
from app.db.base import Base    # noqa
from app.models.user import User
from app.models.fee.fee_plan import FeePlan
from app.models.fee.fee_component import FeeComponent
from app.models.fee.fee_plan_component import FeePlanComponent
from app.models.fee.fee_assignment import FeeAssignment
from app.models.fee.fee_invoice import FeeInvoice
from app.models.fee.payment import Payment
from app.models.fee.receipt import Receipt

# ------------------------------------------------------------------------------
# 3) Alembic Config + safe logging setup
# ------------------------------------------------------------------------------
config = context.config
if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except Exception as e:
        print(">>> Warning: skipping logging config:", e)

# ------------------------------------------------------------------------------
# 4) Debug DB URL and metadata
# ------------------------------------------------------------------------------
db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
# print(">>> Alembic DB URL:", db_url)
# print(">>> Tables in Base.metadata:", list(Base.metadata.tables.keys()))
assert Base.metadata.tables, "No tables found in Base.metadata!"

target_metadata = Base.metadata

def get_url():
    return db_url

# ------------------------------------------------------------------------------
# 5) Offline Migrations
# ------------------------------------------------------------------------------
def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

# ------------------------------------------------------------------------------
# 6) Online Migrations with extra debug
# ------------------------------------------------------------------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=get_url(),
    )

    with connectable.connect() as connection:
        # Inspect live DB schema
        inspector = inspect(connection)
        db_tables = inspector.get_table_names()
        # print(">>> Tables in DATABASE (inspector):", db_tables)

        # Compare to metadata
        model_tables = list(target_metadata.tables.keys())
        # print(">>> Tables in METADATA:", model_tables)

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# ------------------------------------------------------------------------------
# 7) Branch on mode
# ------------------------------------------------------------------------------
# Always run migrations online
run_migrations_online()

