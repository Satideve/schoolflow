# ops/seeds/load_seeds.py
"""
load_seeds.py

This script seeds the database for SchoolFlow with demo data from CSV files.
It is designed to be:

1. **Idempotent**: Tables are seeded only if they are empty.
2. **Order-aware**: Inserts follow dependencies to respect foreign keys:
    - class_sections → students → fee_plan/components → fee_invoice → payment → receipt
3. **Schema-aware**: Validates required columns in CSV and renames columns if needed.
4. **Safe**: Checks FK existence before inserting dependent tables.

Supported CSV files (in `ops/seeds`):

- class_sections.csv
  Required: name (synthesized if missing)
  Optional: id, standard, section, capacity

- students.csv
  Required: name, roll_number (or roll_no auto-renamed), class_section_id
  Optional: id, parent_email

- seed_fees.csv
  Required: fee_plan_name (renamed to name), academic_year, frequency, component_name, amount
  Optional: id, is_mandatory

- invoices.csv
  Required: student_id, period, due_date, amount_due, status
  Optional: id, invoice_no

- payments.csv
  Required: fee_invoice_id, provider, provider_txn_id, amount, status
  Optional: id, idempotency_key

- receipts.csv
  Required: payment_id, receipt_no, pdf_path
  Optional: id, created_by

This modified version ALSO performs sequence-fixing after seeding:
 - Detects the underlying sequence for the `id` column (pg_get_serial_sequence)
 - Sets the sequence value to max(id) for each table so nextval() will return max(id)+1
 - Uses a safe literal-set approach to avoid the Postgres parameterization pitfalls
   when setting sequence names.

Notes:
 - The script is idempotent: running it multiple times will not duplicate rows if CSVs are unchanged.
 - Running on Postgres requires DATABASE_URL to be set in the environment (the app normally does this).
"""

import csv
from pathlib import Path
from typing import Dict, List
from sqlalchemy import text, Table, MetaData, select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid
import os
import sys
import logging

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import engine, SessionLocal
from app.models.fee import FeePlan, FeeComponent, FeePlanComponent

logger = logging.getLogger("ops.seeds.load_seeds")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

BASE_DIR = Path(__file__).parent

# CSV schema expectations
def _expected_schema() -> Dict[str, Dict[str, List[str]]]:
    return {
        "class_sections": {
            "required": ["name"],
            "optional": ["id", "standard", "section", "capacity"],
        },
        "students": {
            "required": ["name", "roll_number", "class_section_id"],
            "optional": ["id", "parent_email"],
        },
        "fee_plan": {
            "required": ["name", "academic_year", "frequency", "component_name", "amount"],
            "optional": ["id", "is_mandatory"],
        },
        "fee_invoice": {
            "required": ["student_id", "period", "due_date", "amount_due", "status"],
            "optional": ["id", "invoice_no", "created_at"],
        },
        "payment": {
            "required": ["fee_invoice_id", "provider", "provider_txn_id", "amount", "status"],
            "optional": ["id", "idempotency_key", "created_at"],
        },
        "receipt": {
            "required": ["payment_id", "receipt_no", "pdf_path"],
            "optional": ["id", "created_at", "created_by"],
        },
    }

# Column renames
RENAME_MAP = {
    "students": {"roll_no": "roll_number"},
    "fee_plan": {"fee_plan_name": "name"},
}

def _print_schema_help(table: str, headers: List[str]):
    exp = _expected_schema().get(table, {"required": [], "optional": []})
    logger.info("----- CSV schema check -----")
    logger.info("Table: %s", table)
    logger.info("Required headers: %s", exp["required"])
    logger.info("Optional headers: %s", exp["optional"])
    logger.info("Found headers: %s", headers)
    if table == "class_sections":
        logger.info("Note: 'name' will be synthesized from standard+section if missing.")
    if table == "students":
        logger.info("Note: 'roll_no' will be auto-renamed to 'roll_number'.")
    if table == "fee_plan":
        logger.info("Note: 'fee_plan_name' will be auto-renamed to 'name'.")
    logger.info("----------------------------")


def _sync_sequence_after_insert_literal(conn, table: str, seq_name: str):
    """
    Ensure the sequence for `table` id column is advanced to at least max(id).
    This uses literal SQL injection of the sequence name after sanitizing it.
    `seq_name` is expected to be a schema-qualified sequence name as returned by
    pg_get_serial_sequence (e.g. 'public.fee_invoice_id_seq').
    """
    try:
        # Use COALESCE so setval gets a valid value even when table is empty.
        # We must avoid parameterizing the sequence name itself (Postgres does not accept it),
        # so escape single quotes and inject the literal.
        safe_seq = str(seq_name).replace("'", "''")
        sql = f"SELECT setval('{safe_seq}', (SELECT COALESCE(MAX(id), 0) FROM {table}), true);"
        conn.execute(text(sql))
        logger.info("🔧 Sequence %s set for table %s", seq_name, table)
    except Exception as e:
        # Best-effort; log but don't fail the whole seeding step.
        logger.warning("Warning: failed to sync sequence %s for table %s: %s", seq_name, table, e)


def load_csv_to_table(path: Path, table: str, session: Session):
    """
    Load CSV data into the table using SQLAlchemy.
    - Validates required fields
    - Renames columns if needed
    - Synthesizes missing names for class_sections
    - For fee_invoice: ensures invoice_no exists (generates deterministic values when missing)
    - Checks FK presence for dependent tables
    """
    logger.info("📄 Reading CSV: %s", path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows: List[Dict] = list(reader)
        headers = reader.fieldnames or []

    _print_schema_help(table, headers)

    # Rename columns
    if table in RENAME_MAP:
        mapping = RENAME_MAP[table]
        for r in rows:
            for src, dst in mapping.items():
                if src in r and dst not in r:
                    r[dst] = r.pop(src)
        logger.info("🔁 Renamed columns for %s: %s", table, mapping)

    # Synthesize class_sections.name
    if table == "class_sections":
        for r in rows:
            if not r.get("name"):
                std, sec = r.get("standard", ""), r.get("section", "")
                if std and sec:
                    r["name"] = f"{std}-{sec}"

    # Validate required fields
    missing = []
    required = _expected_schema()[table]["required"]
    for i, r in enumerate(rows):
        for f in required:
            if r.get(f) in (None, ""):
                missing.append((i + 1, f))
    if missing:
        logger.error("❌ Missing required fields in %s:", table)
        for row_num, field in missing:
            logger.error("  - Row %s: missing '%s'", row_num, field)
        raise ValueError(f"Seed aborted: {table} has missing required fields.")

    # For fee_invoice: generate invoice_no when missing to avoid blank invoice_no in DB
    if table == "fee_invoice":
        for r in rows:
            inv_no = r.get("invoice_no")
            if inv_no is None or inv_no == "":
                # If CSV supplied an explicit id, use it to build deterministic invoice_no
                id_val = r.get("id")
                if id_val not in (None, ""):
                    try:
                        id_int = int(id_val)
                        r["invoice_no"] = f"INV-{id_int}"
                    except Exception:
                        # fallback to uuid if id is non-integer
                        r["invoice_no"] = f"INV-{uuid.uuid4().hex[:12].upper()}"
                else:
                    # no id in CSV — generate a stable-ish uuid-based invoice_no
                    r["invoice_no"] = f"INV-{uuid.uuid4().hex[:12].upper()}"

    # Check FK for payment and receipt
    if table == "payment":
        fee_invoice_ids = {id_ for (id_,) in session.execute(text("SELECT id FROM fee_invoice")).fetchall()}
        for r in rows:
            if int(r["fee_invoice_id"]) not in fee_invoice_ids:
                raise ValueError(f"FK violation: fee_invoice_id={r['fee_invoice_id']} not found")
    if table == "receipt":
        payment_ids = {id_ for (id_,) in session.execute(text("SELECT id FROM payment")).fetchall()}
        for r in rows:
            if int(r["payment_id"]) not in payment_ids:
                raise ValueError(f"FK violation: payment_id={r['payment_id']} not found")

    # Insert rows
    meta = MetaData()
    tgt: Table = Table(table, meta, autoload_with=engine)
    filtered = [{k: (v if v != "" else None) for k, v in r.items() if k in tgt.columns} for r in rows]

    with engine.begin() as conn:
        logger.info("📥 Inserting into table: %s", table)
        conn.execute(tgt.insert(), filtered)
        logger.info("✅ Inserted %s rows into %s", len(filtered), table)

        # If we inserted explicit ids into fee_invoice, ensure sequence is moved forward
        if table == "fee_invoice":
            # Typical sequence name convention: fee_invoice_id_seq
            try:
                seq_name = conn.execute(text("SELECT pg_get_serial_sequence('fee_invoice', 'id')")).scalar_one()
                if seq_name:
                    _sync_sequence_after_insert_literal(conn, "fee_invoice", seq_name)
            except Exception as e:
                logger.warning("Could not determine or set sequence for fee_invoice: %s", e)


def _table_count(conn, table: str) -> int:
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0

def _print_count(conn, table: str):
    cnt = _table_count(conn, table)
    logger.info("Seed check: %s has %s rows.", table, cnt)
    return cnt

def seed_fee_plans(session: Session, path: Path):
    """Seed fee plans and components from CSV."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        plan_cache, comp_cache = {}, {}
        for row in reader:
            # CSV may use 'fee_plan_name' or 'name' depending on source; normalize
            plan_name = row.get("fee_plan_name") or row.get("name")
            plan_key = (plan_name, row["academic_year"])
            if plan_key not in plan_cache:
                plan = FeePlan(name=plan_name, academic_year=row["academic_year"], frequency=row["frequency"])
                session.add(plan)
                session.flush()
                plan_cache[plan_key] = plan.id
            component_name = row["component_name"]
            if component_name not in comp_cache:
                comp = FeeComponent(name=component_name, description=component_name)
                session.add(comp)
                session.flush()
                comp_cache[component_name] = comp.id
            session.add(FeePlanComponent(fee_plan_id=plan_cache[plan_key],
                                         fee_component_id=comp_cache[component_name],
                                         amount=row["amount"]))
    session.commit()

# ---------------------------------------------------------------------------
# New: sequence-fix utilities integrated into load_seeds so one command seeds + fixes
# ---------------------------------------------------------------------------

def fix_sequences_for_tables(conn_or_engine, tables: List[str]):
    """
    For each table in `tables`, attempt to detect the serial sequence for `id`
    using pg_get_serial_sequence and set its value to COALESCE(MAX(id), 1).

    Notes / improvements applied:
      - Use a fresh short-lived connection per table so one failure doesn't abort others.
      - Normalize the table literal used for MAX(id) queries; special-case `user`.
      - Ensure we never call setval(..., 0, true) which fails for Postgres sequences.
        Instead use at least 1 as the sequence value (so nextval() will return 2).
      - Safely escape sequence name when interpolating into SQL text().
      - All exceptions are logged per-table and do not abort the overall pass.
    """
    def _qualified_table_literal(tbl: str) -> str:
        # If caller passed schema-qualified name already, pass through (no quoting).
        if "." in tbl:
            return tbl
        # 'user' is a reserved word — reference it as public."user"
        if tbl.lower() == "user":
            return 'public."user"'
        # Default: reference public."table"
        return f'public."{tbl}"'

    engine_local = conn_or_engine if hasattr(conn_or_engine, "connect") else engine

    for tbl in tables:
        try:
            with engine_local.connect() as c:
                qual_tbl = _qualified_table_literal(tbl)

                # Discover sequence backing the id column
                try:
                    # pg_get_serial_sequence expects a plain schema.table string (no double quotes)
                    # For safety, pass the unquoted schema.table when possible.
                    # If qual_tbl used double-quotes (e.g. public."user"), strip them for this call.
                    pg_arg = qual_tbl.replace('"', "")
                    seq_sql = f"SELECT pg_get_serial_sequence('{pg_arg}', 'id')"
                    seq_name = c.execute(text(seq_sql)).scalar_one()
                except Exception as e:
                    logger.warning("Could not query pg_get_serial_sequence for %s: %s", tbl, e)
                    seq_name = None

                if not seq_name:
                    logger.info("No serial sequence found for table %s (skipping).", tbl)
                    continue

                # Compute MAX(id) for the (possibly quoted) qualified table
                try:
                    max_sql = f"SELECT COALESCE(MAX(id), 0) FROM {qual_tbl}"
                    max_id = c.execute(text(max_sql)).scalar_one()
                except Exception as e:
                    logger.warning("Could not compute MAX(id) for table %s: %s", tbl, e)
                    continue

                # Ensure we never call setval(..., 0, true) — sequences expect >= 1
                desired = int(max_id) if int(max_id) >= 1 else 1

                # Safely set the sequence value. seq_name can include schema; escape single quotes.
                try:
                    safe_seq = str(seq_name).replace("'", "''")
                    set_sql = f"SELECT setval('{safe_seq}', {desired}, true);"
                    c.execute(text(set_sql))
                    logger.info("🔧 Sequence %s set to %s for table %s", seq_name, desired, tbl)
                except Exception as e:
                    logger.warning("Failed to set sequence %s for table %s: %s", seq_name, tbl, e)
        except Exception as e:
            logger.warning("Unexpected error while fixing sequence for %s: %s", tbl, e)
            continue



# ---------------------------------------------------------------------------
# Main run / orchestrator
# ---------------------------------------------------------------------------
def run():
    """Main function to run all seeds in order, and then fix sequences for Postgres."""
    db = SessionLocal()
    try:
        from app.models.user import User
        # Admin user creation
        OLD_EMAIL = "admin@school.local"
        NEW_EMAIL = "admin@example.com"
        DEFAULT_PASSWORD = "ChangeMe123!"
        migrated = db.execute(select(User).where(User.email == OLD_EMAIL)).scalar_one_or_none()
        if migrated:
            db.execute(update(User).where(User.id == migrated.id).values(email=NEW_EMAIL))
            db.commit()
            logger.info("Seed migrate: updated admin email %s -> %s", OLD_EMAIL, NEW_EMAIL)
        if not db.execute(select(User).where(User.email == NEW_EMAIL)).scalar_one_or_none():
            user = User(email=NEW_EMAIL, hashed_password=get_password_hash(DEFAULT_PASSWORD), role="admin")
            db.add(user)
            db.commit()
            logger.info("Seed done: admin user created (%s).", NEW_EMAIL)
        else:
            logger.info("Seed skipped: admin already exists (%s).", NEW_EMAIL)

        # Sequential seeding
        seq = [
            ("class_sections", BASE_DIR / "class_sections.csv"),
            ("students", BASE_DIR / "students.csv"),
        ]
        for tbl, csv_file in seq:
            if csv_file.exists() and _table_count(db.connection(), tbl) == 0:
                logger.info("Seeding %s from %s ...", tbl, csv_file)
                load_csv_to_table(csv_file, tbl, db)
                _print_count(db.connection(), tbl)
            else:
                logger.info("Seed skipped: %s already populated or CSV missing.", tbl)

        fees_csv = BASE_DIR / "seed_fees.csv"
        if fees_csv.exists() and _table_count(db.connection(), "fee_component") == 0:
            logger.info("Seeding fee_plan + components...")
            seed_fee_plans(db, fees_csv)
            _print_count(db.connection(), "fee_component")
            _print_count(db.connection(), "fee_plan_component")
        else:
            logger.info("Seed skipped: fee components already populated or CSV missing.")

        # Seed invoice, payment, receipt
        tail_seq = [
            ("fee_invoice", BASE_DIR / "invoices.csv"),
            ("payment", BASE_DIR / "payments.csv"),
            ("receipt", BASE_DIR / "receipts.csv"),
        ]
        for tbl, csv_file in tail_seq:
            if csv_file.exists() and _table_count(db.connection(), tbl) == 0:
                logger.info("Seeding %s from %s ...", tbl, csv_file)
                load_csv_to_table(csv_file, tbl, db)
                _print_count(db.connection(), tbl)
            else:
                logger.info("Seed skipped: %s already populated or CSV missing.", tbl)

        # After inserts: fix sequences for common tables (idempotent)
        try:
            with engine.connect() as conn:
                tables_to_fix = [
                    "class_sections",
                    "students",
                    "user",
                    "fee_plan",
                    "fee_component",
                    "fee_plan_component",
                    "fee_assignment",
                    "fee_invoice",
                    "payment",
                    "receipt",
                ]
                logger.info("🔧 Fixing sequences for tables: %s", tables_to_fix)
                fix_sequences_for_tables(conn, tables_to_fix)
        except Exception as e:
            logger.warning("Sequence-fix step failed: %s", e)

    finally:
        db.close()

if __name__ == "__main__":
    run()
