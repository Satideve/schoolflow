# ops/seeds/load_seeds.py
"""
Loads seed CSV files into DB for quick demo.
- Idempotent: loads only if tables are empty
- Order-aware: class_sections -> students

CSV expectations (headers and notes):
1) class_sections.csv
   - Required: name (synthesized from standard + section if not present)
   - Recommended: standard, section, capacity
   - Optional: id (if omitted, DB default/sequence is used)
   Example:
     id,standard,section,capacity
     1,IX,A,40
   Synthesized:
     name = "{standard}-{section}" (e.g., "IX-A")

2) students.csv
   - Required: name, roll_number (or roll_no, auto-renamed), class_section_id
   - Optional: id, parent_email
   - roll_no will be auto-renamed to roll_number
   Example:
     id,name,roll_no,class_section_id,parent_email
     1,Anjali Singh,1A-001,1,parent1@example.com

3) seed_fees.csv (fee_plan)
   - Required: name (or fee_plan_name, auto-renamed), academic_year, frequency
   - Optional: id
   Example:
     fee_plan_name,academic_year,frequency
     Standard-IX-2025,2025,monthly
"""

import csv
from pathlib import Path
from typing import Dict, List
from sqlalchemy import text, select, Table, MetaData
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine, SessionLocal


def _expected_schema() -> Dict[str, Dict[str, List[str]]]:
    """Return expected 'required' and 'optional' columns per logical table."""
    return {
        "class_sections": {
            "required": ["name"],                # will be synthesized if absent and standard+section present
            "optional": ["id", "standard", "section", "capacity"],
        },
        "students": {
            "required": ["name", "roll_number", "class_section_id"],  # roll_no auto-renamed
            "optional": ["id", "parent_email"],
        },
        "fee_plan": {
            "required": ["name", "academic_year", "frequency"],       # fee_plan_name auto-renamed
            "optional": ["id"],
        },
    }


def _print_schema_help(table: str, found_headers: List[str]):
    exp = _expected_schema().get(table, {"required": [], "optional": []})
    print("----- CSV schema check -----")
    print(f"Table: {table}")
    print(f"Required headers: {exp['required']}")
    print(f"Optional headers: {exp['optional']}")
    print(f"Found headers: {found_headers}")
    if table == "class_sections":
        print("Note: If 'name' is absent, it will be synthesized as '{standard}-{section}'.")
    if table == "students":
        print("Note: 'roll_no' will be auto-renamed to 'roll_number'.")
    if table == "fee_plan":
        print("Note: 'fee_plan_name' will be auto-renamed to 'name'.")
    print("----------------------------")


def load_csv_to_table(path: Path, table: str):
    print(f"📄 Reading CSV: {path}")

    required_fields = {
         "class_sections": ["name", "academic_year"],
        "students": ["name", "roll_number", "class_section_id"],
        "fee_plan": ["name", "academic_year", "frequency"],
    }

    rename_map: Dict[str, Dict[str, str]] = {
        "students": {
            "roll_no": "roll_number",
        },
        "fee_plan": {
            "fee_plan_name": "name",
        },
    }

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows: List[Dict] = list(reader)
        found_headers = reader.fieldnames or []

    _print_schema_help(table, found_headers)
    print(f"📊 Loaded {len(rows)} rows from {path.name}")

    # Apply auto-rename if any
    if table in rename_map:
        mapping = rename_map[table]
        for r in rows:
            for src, dst in list(mapping.items()):
                if src in r and dst not in r:
                    r[dst] = r.pop(src)
        print(f"🔁 Renamed columns for {table}: {mapping}")

    # Synthesize class_sections.name if possible
    if table == "class_sections":
        synthesized = 0
        for r in rows:
            # Use existing name if already present and non-empty
            if r.get("name"):
                continue
            std = (r.get("standard") or "").strip()
            sec = (r.get("section") or "").strip()
            if std and sec:
                r["name"] = f"{std}-{sec}"
                synthesized += 1
        if synthesized > 0:
            print(f"🧩 Synthesized 'name' for {synthesized} row(s) from standard + section")

    if not rows:
        print(f"ℹ️ No rows to insert for {table}.")
        return

    # Reflect target table and filter columns to known set
    meta = MetaData()
    tgt: Table = Table(table, meta, autoload_with=engine)

    cols = {c.name for c in tgt.columns}
    filtered: List[Dict] = []
    for r in rows:
        item = {k: (v if v != "" else None) for k, v in r.items() if k in cols}
        filtered.append(item)

    # Validate required fields
    missing = []
    for i, r in enumerate(filtered):
        for field in required_fields.get(table, []):
            if r.get(field) in (None, ""):
                missing.append((i + 1, field))

    if missing:
        print(f"❌ Missing required fields in {table}:")
        for row_num, field in missing:
            print(f"  - Row {row_num}: missing '{field}'")
        raise ValueError(f"Seed aborted: {table} has missing required fields.")

    with engine.begin() as conn:
        print(f"📥 Inserting into table: {table}")
        conn.execute(tgt.insert(), filtered)
        print(f"✅ Inserted {len(filtered)} rows into {table}")


def _table_count(conn, table: str) -> int:
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0


def _print_count(conn, table: str):
    cnt = _table_count(conn, table)
    print(f"Seed check: {table} has {cnt} rows.")
    return cnt


def run():
    base = Path(__file__).parent
    db = SessionLocal()
    try:
        # Idempotent admin creation
        from app.models.user import User

        stmt = select(User).where(User.email == "admin@school.local")
        existing = db.execute(stmt).scalar_one_or_none()

        if not existing:
            user = User(
                email="admin@school.local",
                hashed_password=get_password_hash("ChangeMe123!"),
                role="admin",
            )
            db.add(user)
            db.commit()
            print("Seed done: admin user created.")
        else:
            print("Seed skipped: admin already exists.")

        # CSV seeds in order
        with engine.connect() as conn:
            # class_sections first
            class_sections_csv = base / "class_sections.csv"
            if class_sections_csv.exists():
                cs_rows = _print_count(conn, "class_sections")
                if cs_rows == 0:
                    print("Seeding: class_sections from CSV...")
                    load_csv_to_table(class_sections_csv, "class_sections")
                    conn.commit()
                    _print_count(conn, "class_sections")
                else:
                    print("Seed skipped: class_sections already populated.")
            else:
                print("Seed note: class_sections.csv not found; skipping.")

            # students next
            students_csv = base / "students.csv"
            if students_csv.exists():
                st_rows = _print_count(conn, "students")
                if st_rows == 0:
                    print("Seeding: students from CSV...")
                    load_csv_to_table(students_csv, "students")
                    conn.commit()
                    _print_count(conn, "students")
                else:
                    print("Seed skipped: students already populated.")
            else:
                print("Seed note: students.csv not found; skipping.")

            # fee plans (optional)
            fees_csv = base / "seed_fees.csv"
            if fees_csv.exists():
                try:
                    fp_rows = _print_count(conn, "fee_plan")
                    if fp_rows == 0:
                        print("Seeding: fee_plan (from seed_fees.csv)...")
                        with fees_csv.open(newline="", encoding="utf-8") as f:
                            reader = csv.DictReader(f)
                            rows = list(reader)
                            found_headers = reader.fieldnames or []
                        _print_schema_help("fee_plan", found_headers)

                        # Auto-rename
                        for r in rows:
                            if "fee_plan_name" in r and "name" not in r:
                                r["name"] = r.pop("fee_plan_name")

                        # Reflect and filter
                        meta = MetaData()
                        fee_plan_tbl = Table("fee_plan", meta, autoload_with=engine)
                        cols = {c.name for c in fee_plan_tbl.columns}
                        filtered = [{k: (v if v != "" else None) for k, v in r.items() if k in cols} for r in rows]

                        # Validate required fields
                        missing = []
                        for i, r in enumerate(filtered):
                            for field in ["name", "academic_year", "frequency"]:
                                if r.get(field) in (None, ""):
                                    missing.append((i + 1, field))
                        if missing:
                            print(f"❌ Missing required fields in fee_plan:")
                            for row_num, field in missing:
                                print(f"  - Row {row_num}: missing '{field}'")
                            raise ValueError("Seed aborted: fee_plan has missing required fields.")

                        with engine.begin() as xconn:
                            xconn.execute(fee_plan_tbl.insert(), filtered)
                        _print_count(conn, "fee_plan")
                    else:
                        print("Seed skipped: fee_plan already populated.")
                except Exception as e:
                    print(f"Seed note: fee_plan seed skipped due to mismatch or error: {e}")
            else:
                print("Seed note: seed_fees.csv not found; skipping.")

    finally:
        db.close()


if __name__ == "__main__":
    run()
