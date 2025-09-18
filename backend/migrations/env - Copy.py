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

# ------------------------------------------------------------------------------
# 2) Import your Base and all model classes
# ------------------------------------------------------------------------------
from app.db.base import Base    # noqa
from app.models.user import User
from app.models.student import Student
from app.models.class_section import ClassSection
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

# Override alembic.ini’s URL with the one loaded from .env
db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except Exception as e:
        print(">>> Warning: skipping logging config:", e)

# ------------------------------------------------------------------------------
# 4) Debug DB URL and metadata
# ------------------------------------------------------------------------------
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
# 6) Online Migrations with stamp detection and debug
# ------------------------------------------------------------------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=get_url(),
    )

    with connectable.connect() as connection:
        # detect if this invocation is 'stamp'
        # is_stamp = getattr(config.cmd_opts, "cmd", None) == "stamp"
        raw_cmd = getattr(config.cmd_opts, "cmd", None)
        if isinstance(raw_cmd, tuple) and raw_cmd:
            invoked = raw_cmd[0].__name__
        else:
            invoked = None
        is_stamp = invoked == "stamp"
        # is_stamp = "stamp" in context.get_x_argument(as_dictionary=True)
        if is_stamp:
            # stamp should only write the version, no metadata comparison
            context.configure(connection=connection)
        else:
            # Inspect live DB schema
            inspector = inspect(connection)
            db_tables = inspector.get_table_names()
            model_tables = list(target_metadata.tables.keys())

            print(">>> Tables in DATABASE (inspector):", db_tables)
            print(">>> Tables in METADATA:", model_tables)

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
# debug: show which cmd_opts keys are available


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
