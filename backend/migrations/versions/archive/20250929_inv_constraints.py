# backend/app/alembic/versions/20250929_inv_constraints.py

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


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Check if unique constraint already exists
    existing_constraints = conn.execute(
        sa.text(
            "SELECT conname FROM pg_constraint "
            "WHERE conrelid = 'fee_invoice'::regclass"
        )
    ).fetchall()
    existing_constraints = {row[0] for row in existing_constraints}

    if "uq_fee_invoice_invoice_no" not in existing_constraints:
        op.create_unique_constraint("uq_fee_invoice_invoice_no", "fee_invoice", ["invoice_no"])

    # Indexes: check existence before creating
    def ensure_index(name, table, cols, unique=False):
        res = conn.execute(
            sa.text("SELECT indexname FROM pg_indexes WHERE tablename = :t"),
            {"t": table},
        ).fetchall()
        existing = {r[0] for r in res}
        if name not in existing:
            op.create_index(name, table, cols, unique=unique)

    ensure_index("ix_fee_invoice_invoice_no", "fee_invoice", ["invoice_no"], unique=True)
    ensure_index("ix_fee_invoice_student_id", "fee_invoice", ["student_id"])
    ensure_index("ix_fee_invoice_created_at", "fee_invoice", ["created_at"])


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    # Drop indexes if they exist
    for idx in [
        "ix_fee_invoice_created_at",
        "ix_fee_invoice_student_id",
        "ix_fee_invoice_invoice_no",
    ]:
        conn.execute(
            sa.text(
                "DO $$ BEGIN "
                "IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = :i) THEN "
                f"DROP INDEX {idx}; "
                "END IF; END $$;"
            ).bindparams(i=idx)
        )

    # Drop constraint if exists
    conn.execute(
        sa.text(
            "DO $$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_fee_invoice_invoice_no') THEN "
            "ALTER TABLE fee_invoice DROP CONSTRAINT uq_fee_invoice_invoice_no; "
            "END IF; END $$;"
        )
    )
