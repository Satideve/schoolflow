# backend/migrations/versions/20251210_user_student_unique.py

"""add unique constraint on user.student_id

Revision ID: 20251210_user_student_unique
Revises: 20251206_fee_invoice_item
Create Date: 2025-12-10 00:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20251210_user_student_unique"
down_revision = "20251206_fee_invoice_item"
branch_labels = None
depends_on = None


def upgrade() -> None:
  """
  Ensure that at most ONE user can be linked to a given student_id.
  student_id is still nullable, but when present it must be unique.
  """
  op.create_unique_constraint(
      "uq_user_student_id",  # constraint name
      "user",                # table name
      ["student_id"],        # column(s)
  )


def downgrade() -> None:
  """
  Drop the unique constraint on user.student_id if we ever roll back.
  """
  op.drop_constraint(
      "uq_user_student_id",
      "user",
      type_="unique",
  )
