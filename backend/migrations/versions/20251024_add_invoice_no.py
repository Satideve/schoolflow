# file: 20251024_add_invoice_no.py
"""add invoice_no column to fee_invoice

Revision ID: 20251024_add_invoice_no
Revises: 20250929_inv_constraints
Create Date: 2025-10-24 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '20251024_add_invoice_no'
down_revision = '20250929_inv_constraints'
branch_labels = None
depends_on = None


def _pg_index_exists(conn, index_name: str) -> bool:
    res = conn.execute(sa.text("SELECT 1 FROM pg_indexes WHERE indexname = :i"), {"i": index_name}).fetchall()
    return bool(res)


def _pg_constraint_exists(conn, constraint_name: str) -> bool:
    res = conn.execute(sa.text("SELECT 1 FROM pg_constraint WHERE conname = :c"), {"c": constraint_name}).fetchall()
    return bool(res)


def upgrade() -> None:
    """Add invoice_no column and unique/index constraints if missing (safe checks)."""
    conn = op.get_bind()

    # Use inspector for portable column detection
    inspector = Inspector.from_engine(conn)
    try:
        columns = [col["name"] for col in inspector.get_columns("fee_invoice")]
    except Exception:
        columns = []

    # 1) Add column if missing
    if "invoice_no" not in columns:
        with op.batch_alter_table("fee_invoice") as batch_op:
            batch_op.add_column(sa.Column("invoice_no", sa.String(length=64), nullable=True))

    # 2) On Postgres: ensure constraint/index only if they don't already exist
    if conn.dialect.name == "postgresql":
        # create unique constraint only if not present
        if not _pg_constraint_exists(conn, "uq_fee_invoice_invoice_no"):
            # Only create constraint if the column exists
            if "invoice_no" in columns or True:
                # If invoice_no was just added above, it exists in DB now; create constraint
                try:
                    with op.batch_alter_table("fee_invoice") as batch_op:
                        batch_op.create_unique_constraint("uq_fee_invoice_invoice_no", ["invoice_no"])
                except Exception:
                    # guard against races or unexpected conditions
                    pass

        # create index only if not present
        if not _pg_index_exists(conn, "ix_fee_invoice_invoice_no"):
            try:
                # Prefer to let the unique constraint create the unique index,
                # but if constraint exists and index doesn't, create index explicitly.
                with op.batch_alter_table("fee_invoice") as batch_op:
                    batch_op.create_index("ix_fee_invoice_invoice_no", ["invoice_no"], unique=True)
            except Exception:
                pass

    else:
        # For SQLite or other dialects, use inspector checks and batch alter
        try:
            unique_constraints = [c["name"] for c in inspector.get_unique_constraints("fee_invoice")]
        except Exception:
            unique_constraints = []

        if "uq_fee_invoice_invoice_no" not in unique_constraints and "invoice_no" in columns:
            with op.batch_alter_table("fee_invoice") as batch_op:
                try:
                    batch_op.create_unique_constraint("uq_fee_invoice_invoice_no", ["invoice_no"])
                except Exception:
                    pass
                try:
                    batch_op.create_index("ix_fee_invoice_invoice_no", ["invoice_no"], unique=True)
                except Exception:
                    pass


def downgrade() -> None:
    """Remove invoice_no column and related constraints/indexes."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Drop constraint and index if present
    try:
        if conn.dialect.name == "postgresql":
            if _pg_index_exists(conn, "ix_fee_invoice_invoice_no"):
                conn.execute(sa.text("DROP INDEX IF EXISTS ix_fee_invoice_invoice_no"))
            if _pg_constraint_exists(conn, "uq_fee_invoice_invoice_no"):
                conn.execute(sa.text("ALTER TABLE fee_invoice DROP CONSTRAINT IF EXISTS uq_fee_invoice_invoice_no"))
        else:
            try:
                constraints = [c["name"] for c in inspector.get_unique_constraints("fee_invoice")]
            except Exception:
                constraints = []
            if "uq_fee_invoice_invoice_no" in constraints:
                with op.batch_alter_table("fee_invoice") as batch_op:
                    try:
                        batch_op.drop_index("ix_fee_invoice_invoice_no")
                    except Exception:
                        pass
                    try:
                        batch_op.drop_unique_constraint("uq_fee_invoice_invoice_no")
                    except Exception:
                        pass
    except Exception:
        # best-effort drop, ignore errors during downgrade cleanup
        pass

    # Drop column if exists
    try:
        cols = [c["name"] for c in inspector.get_columns("fee_invoice")]
    except Exception:
        cols = []
    if "invoice_no" in cols:
        with op.batch_alter_table("fee_invoice") as batch_op:
            try:
                batch_op.drop_column("invoice_no")
            except Exception:
                pass
