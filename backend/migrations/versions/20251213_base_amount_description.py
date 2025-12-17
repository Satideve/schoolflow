# backend/migrations/versions/20251213_base_amount_description.py
"""add base_amount_description to fee_invoice

Revision ID: 20251213_base_amount_description
Revises: 20251210_user_student_unique
Create Date: 2025-12-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251213_base_amount_description"
down_revision = "20251210_user_student_unique"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "fee_invoice",
        sa.Column("base_amount_description", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_column("fee_invoice", "base_amount_description")
