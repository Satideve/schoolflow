# file: 20250929_inv_constraints.py
"""add constraints and indexes to fee_invoice

Revision ID: 20250929_inv_constraints
Revises: 4832b4808674
Create Date: 2025-09-29 19:40:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "20250929_inv_constraints"
down_revision: Union[str, Sequence[str], None] = "4832b4808674"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(bind, table_name: str, column_name: str) -> bool:
    """Return True if the given table has the named column (works across dialects)."""
    try:
        inspector = sa.inspect(bind)
        cols = inspector.get_columns(table_name)
        return any(c.get("name") == column_name for c in cols)
    except Exception:
        return False


def _index_exists_postgres(bind, index_name: str) -> bool:
    """Check pg_indexes for an index name (Postgres only)."""
    res = bind.execute(sa.text("SELECT indexname FROM pg_indexes WHERE indexname = :i"), {"i": index_name}).fetchall()
    return bool(res)


def upgrade() -> None:
    """Upgrade schema: add unique constraint and useful indexes for fee_invoice."""
    conn = op.get_bind()

    if conn.dialect.name == "postgresql":
        # Check if unique constraint already exists
        existing_constraints = conn.execute(
            sa.text(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid = 'fee_invoice'::regclass"
            )
        ).fetchall()
        existing_constraints = {row[0] for row in existing_constraints}

        if "uq_fee_invoice_invoice_no" not in existing_constraints:
            # Attempt to create unique constraint; will fail if column missing, so ensure column exists
            if _has_column(conn, "fee_invoice", "invoice_no"):
                op.create_unique_constraint("uq_fee_invoice_invoice_no", "fee_invoice", ["invoice_no"])

        # Indexes: check existence before creating
        def ensure_index(name, table, cols, unique=False):
            if not _index_exists_postgres(conn, name):
                op.create_index(name, table, cols, unique=unique)

        # Only create invoice_no index if column exists
        if _has_column(conn, "fee_invoice", "invoice_no"):
            ensure_index("ix_fee_invoice_invoice_no", "fee_invoice", ["invoice_no"], unique=True)

        # student_id and created_at indexes are safe to create if their columns exist
        if _has_column(conn, "fee_invoice", "student_id"):
            ensure_index("ix_fee_invoice_student_id", "fee_invoice", ["student_id"])
        if _has_column(conn, "fee_invoice", "created_at"):
            ensure_index("ix_fee_invoice_created_at", "fee_invoice", ["created_at"])

    else:
        # SQLite or other dialects: use batch mode and guard on column existence
        if _has_column(conn, "fee_invoice", "invoice_no"):
            with op.batch_alter_table("fee_invoice") as batch_op:
                try:
                    batch_op.create_unique_constraint("uq_fee_invoice_invoice_no", ["invoice_no"])
                except Exception:
                    pass
                try:
                    batch_op.create_index("ix_fee_invoice_invoice_no", ["invoice_no"], unique=True)
                except Exception:
                    pass

        if _has_column(conn, "fee_invoice", "student_id"):
            with op.batch_alter_table("fee_invoice") as batch_op:
                try:
                    batch_op.create_index("ix_fee_invoice_student_id", ["student_id"])
                except Exception:
                    pass

        if _has_column(conn, "fee_invoice", "created_at"):
            with op.batch_alter_table("fee_invoice") as batch_op:
                try:
                    batch_op.create_index("ix_fee_invoice_created_at", ["created_at"])
                except Exception:
                    pass


def downgrade() -> None:
    """Downgrade schema: remove constraints/indexes if present."""
    conn = op.get_bind()

    if conn.dialect.name == "postgresql":
        # Drop indexes if they exist (using IF EXISTS)
        for idx in [
            "ix_fee_invoice_created_at",
            "ix_fee_invoice_student_id",
            "ix_fee_invoice_invoice_no",
        ]:
            try:
                conn.execute(sa.text(f"DROP INDEX IF EXISTS {idx}"))
            except Exception:
                pass

        # Drop constraint if exists
        try:
            conn.execute(sa.text("ALTER TABLE fee_invoice DROP CONSTRAINT IF EXISTS uq_fee_invoice_invoice_no"))
        except Exception:
            pass

    else:
        # SQLite: use batch_alter_table with guards
        with op.batch_alter_table("fee_invoice") as batch_op:
            for idx in ["ix_fee_invoice_created_at", "ix_fee_invoice_student_id", "ix_fee_invoice_invoice_no"]:
                try:
                    batch_op.drop_index(idx)
                except Exception:
                    pass
            try:
                batch_op.drop_unique_constraint("uq_fee_invoice_invoice_no")
            except Exception:
                pass
