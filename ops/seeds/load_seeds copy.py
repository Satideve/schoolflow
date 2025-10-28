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
"""

import csv
from pathlib import Path
from typing import Dict, List
from sqlalchemy import text, Table, MetaData, select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import engine, SessionLocal
from app.models.fee import FeePlan, FeeComponent, FeePlanComponent

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
    print("----- CSV schema check -----")
    print(f"Table: {table}")
    print(f"Required headers: {exp['required']}")
    print(f"Optional headers: {exp['optional']}")
    print(f"Found headers: {headers}")
    if table == "class_sections":
        print("Note: 'name' will be synthesized from standard+section if missing.")
    if table == "students":
        print("Note: 'roll_no' will be auto-renamed to 'roll_number'.")
    if table == "fee_plan":
        print("Note: 'fee_plan_name' will be auto-renamed to 'name'.")
    print("----------------------------")

def _sync_sequence_after_insert(conn, table: str, seq_name: str):
    """
    Ensure the sequence for `table` id column is advanced to at least max(id).
    This prevents duplicate-key errors when inserting rows with explicit ids.
    """
    try:
        # Use COALESCE so setval gets a valid value even when table is empty.
        sql = text(
            "SELECT setval(:seq, (SELECT COALESCE(MAX(id), 1) FROM " + table + "), true)"
        ).bindparams(seq=seq_name)
        conn.execute(sql)
    except Exception as e:
        # Best-effort; log but don't fail the whole seeding step.
        print(f"Warning: failed to sync sequence {seq_name} for table {table}: {e}")

def load_csv_to_table(path: Path, table: str, session: Session):
    """
    Load CSV data into the table using SQLAlchemy.
    - Validates required fields
    - Renames columns if needed
    - Synthesizes missing names for class_sections
    - For fee_invoice: ensures invoice_no exists (generates deterministic values when missing)
    - Checks FK presence for dependent tables
    """
    print(f"📄 Reading CSV: {path}")
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
        print(f"🔁 Renamed columns for {table}: {mapping}")

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
        print(f"❌ Missing required fields in {table}:")
        for row_num, field in missing:
            print(f"  - Row {row_num}: missing '{field}'")
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
        print(f"📥 Inserting into table: {table}")
        conn.execute(tgt.insert(), filtered)
        print(f"✅ Inserted {len(filtered)} rows into {table}")

        # If we inserted explicit ids into fee_invoice, ensure sequence is moved forward
        if table == "fee_invoice":
            # typical sequence name convention: fee_invoice_id_seq
            _sync_sequence_after_insert(conn, "fee_invoice", "fee_invoice_id_seq")


def _table_count(conn, table: str) -> int:
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0

def _print_count(conn, table: str):
    cnt = _table_count(conn, table)
    print(f"Seed check: {table} has {cnt} rows.")
    return cnt

def seed_fee_plans(session: Session, path: Path):
    """Seed fee plans and components from CSV."""
    with path.open(newline="") as f:
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

def run():
    """Main function to run all seeds in order."""
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
            print(f"Seed migrate: updated admin email {OLD_EMAIL} -> {NEW_EMAIL}")
        if not db.execute(select(User).where(User.email == NEW_EMAIL)).scalar_one_or_none():
            user = User(email=NEW_EMAIL, hashed_password=get_password_hash(DEFAULT_PASSWORD), role="admin")
            db.add(user)
            db.commit()
            print(f"Seed done: admin user created ({NEW_EMAIL}).")
        else:
            print(f"Seed skipped: admin already exists ({NEW_EMAIL}).")

        # Sequential seeding
        for tbl, csv_file in [
            ("class_sections", BASE_DIR / "class_sections.csv"),
            ("students", BASE_DIR / "students.csv"),
        ]:
            if csv_file.exists() and _table_count(db.connection(), tbl) == 0:
                print(f"Seeding {tbl}...")
                load_csv_to_table(csv_file, tbl, db)
                _print_count(db.connection(), tbl)
            else:
                print(f"Seed skipped: {tbl} already populated or CSV missing.")

        fees_csv = BASE_DIR / "seed_fees.csv"
        if fees_csv.exists() and _table_count(db.connection(), "fee_component") == 0:
            print("Seeding fee_plan + components...")
            seed_fee_plans(db, fees_csv)
            _print_count(db.connection(), "fee_component")
            _print_count(db.connection(), "fee_plan_component")
        else:
            print("Seed skipped: fee components already populated or CSV missing.")

        # Seed invoice, payment, receipt
        for tbl, csv_file in [
            ("fee_invoice", BASE_DIR / "invoices.csv"),
            ("payment", BASE_DIR / "payments.csv"),
            ("receipt", BASE_DIR / "receipts.csv"),
        ]:
            if csv_file.exists() and _table_count(db.connection(), tbl) == 0:
                print(f"Seeding {tbl}...")
                load_csv_to_table(csv_file, tbl, db)
                _print_count(db.connection(), tbl)
            else:
                print(f"Seed skipped: {tbl} already populated or CSV missing.")

    finally:
        db.close()

if __name__ == "__main__":
    run()
