# backend/migrations/versions/20251206_add_fee_invoice_item_table.py
"""add fee_invoice_item table

Revision ID: 20251206_fee_invoice_item
Revises: 20251201_user_student_link
Create Date: 2025-12-06 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251206_fee_invoice_item"
down_revision = "20251201_user_student_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = inspector.get_table_names()

    # Create table only if it does not already exist
    if "fee_invoice_item" not in tables:
        op.create_table(
            "fee_invoice_item",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("fee_invoice_id", sa.Integer(), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=False),
            sa.Column("amount", sa.Numeric(10, 2), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["fee_invoice_id"],
                ["fee_invoice.id"],
                name="fk_fee_invoice_item_fee_invoice_id",
            ),
        )

    # Ensure index exists on fee_invoice_id
    if "fee_invoice_item" in tables:
        existing_indexes = {
            idx["name"] for idx in inspector.get_indexes("fee_invoice_item")
        }
        if "ix_fee_invoice_item_fee_invoice_id" not in existing_indexes:
            op.create_index(
                "ix_fee_invoice_item_fee_invoice_id",
                "fee_invoice_item",
                ["fee_invoice_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    tables = inspector.get_table_names()

    if "fee_invoice_item" in tables:
        existing_indexes = {
            idx["name"] for idx in inspector.get_indexes("fee_invoice_item")
        }
        if "ix_fee_invoice_item_fee_invoice_id" in existing_indexes:
            op.drop_index(
                "ix_fee_invoice_item_fee_invoice_id",
                table_name="fee_invoice_item",
            )

        op.drop_table("fee_invoice_item")
