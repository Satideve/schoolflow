# backend/migrations/versions/20251026_add_inv_id.py

"""add invoice_id to fee_assignment

Revision ID: 20251026_add_inv_id
Revises: 20251024_add_invoice_no
Create Date: 2025-10-26 12:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251026_add_inv_id"
down_revision: Union[str, Sequence[str], None] = "20251024_add_invoice_no"
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
    """Postgres-only check for an index name."""
    try:
        res = bind.execute(sa.text("SELECT indexname FROM pg_indexes WHERE indexname = :i"), {"i": index_name}).fetchall()
        return bool(res)
    except Exception:
        return False


def _constraint_exists_postgres(bind, constraint_name: str) -> bool:
    """Postgres-only check for a constraint name."""
    try:
        res = bind.execute(sa.text(
            "SELECT 1 FROM pg_constraint WHERE conname = :c"
        ), {"c": constraint_name}).fetchall()
        return bool(res)
    except Exception:
        return False


def upgrade() -> None:
    """Add invoice_id column to fee_assignment (nullable), plus index and FK."""

    bind = op.get_bind()
    # If column already exists, do nothing
    if _has_column(bind, "fee_assignment", "invoice_id"):
        # ensure index/constraint exist if possible (attempt best-effort for Postgres)
        if bind.dialect.name == "postgresql":
            if not _index_exists_postgres(bind, "ix_fee_assignment_invoice_id"):
                op.create_index("ix_fee_assignment_invoice_id", "fee_assignment", ["invoice_id"], unique=False)
            if not _constraint_exists_postgres(bind, "fk_fee_assignment_invoice_id"):
                try:
                    op.create_foreign_key("fk_fee_assignment_invoice_id", "fee_assignment", "fee_invoice", ["invoice_id"], ["id"])
                except Exception:
                    # if FK cannot be created, skip (we don't want to fail an upgrade)
                    pass
        return

    # Add column safely using batch_alter_table (works for sqlite and pg)
    with op.batch_alter_table("fee_assignment", schema=None) as batch_op:
        batch_op.add_column(sa.Column("invoice_id", sa.Integer(), nullable=True))
        # create index (batch_op.create_index is available)
        try:
            batch_op.create_index("ix_fee_assignment_invoice_id", ["invoice_id"], unique=False)
        except Exception:
            # ignore on dialects where this fails inside batch
            pass

    # Add FK constraint for Postgres (best-effort)
    if bind.dialect.name == "postgresql":
        # Check again and create FK if not present
        if not _constraint_exists_postgres(bind, "fk_fee_assignment_invoice_id"):
            try:
                op.create_foreign_key(
                    "fk_fee_assignment_invoice_id",
                    "fee_assignment",
                    "fee_invoice",
                    ["invoice_id"],
                    ["id"],
                )
            except Exception:
                # don't fail the migration if FK creation is problematic (leave column nullable)
                pass


def downgrade() -> None:
    """Remove invoice_id column and related index/constraint if present."""
    bind = op.get_bind()

    # Drop FK constraint on Postgres if exists
    if bind.dialect.name == "postgresql":
        if _constraint_exists_postgres(bind, "fk_fee_assignment_invoice_id"):
            try:
                op.drop_constraint("fk_fee_assignment_invoice_id", "fee_assignment", type_="foreignkey")
            except Exception:
                pass
        # drop index if exists
        if _index_exists_postgres(bind, "ix_fee_assignment_invoice_id"):
            try:
                op.drop_index("ix_fee_assignment_invoice_id")
            except Exception:
                pass

    # Use batch to drop column (works for sqlite + pg)
    if _has_column(bind, "fee_assignment", "invoice_id"):
        with op.batch_alter_table("fee_assignment", schema=None) as batch_op:
            try:
                batch_op.drop_index("ix_fee_assignment_invoice_id")
            except Exception:
                pass
            try:
                batch_op.drop_column("invoice_id")
            except Exception:
                pass
