# backend/migrations/versions/20251108_payidempkey.py

"""add unique index on payment.idempotency_key

Revision ID: 20251108_payidempkey
Revises: 20251026_add_inv_id
Create Date: 2025-11-08 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251108_payidempkey"
down_revision = "20251026_add_inv_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create a UNIQUE index on payment.idempotency_key so duplicate non-null keys are rejected.
    - In PostgreSQL and SQLite, UNIQUE allows multiple NULLs, which is what we want.
    """
    op.create_index(
        "uq_payment_idempotency_key",
        "payment",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    """Drop the UNIQUE index."""
    op.drop_index("uq_payment_idempotency_key", table_name="payment")
