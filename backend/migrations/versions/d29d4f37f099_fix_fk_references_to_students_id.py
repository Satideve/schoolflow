"""fix FK references to students.id

Revision ID: d29d4f37f099
Revises: 'b9bec1465e3a'
Create Date: 2025-09-22 15:32:17.415748
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd29d4f37f099'
down_revision: Union[str, Sequence[str], None] = 'b9bec1465e3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite: batch mode requires named constraints
        with op.batch_alter_table("fee_assignment") as batch_op:
            batch_op.create_foreign_key(
                "fk_fee_assignment_student_id", "students", ["student_id"], ["id"]
            )
        with op.batch_alter_table("fee_invoice") as batch_op:
            batch_op.create_foreign_key(
                "fk_fee_invoice_student_id", "students", ["student_id"], ["id"]
            )
    else:
        # Postgres or other DBs: normal FK creation with names
        op.create_foreign_key(
            "fk_fee_assignment_student_id", "fee_assignment", "students", ["student_id"], ["id"]
        )
        op.create_foreign_key(
            "fk_fee_invoice_student_id", "fee_invoice", "students", ["student_id"], ["id"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite: use batch mode
        with op.batch_alter_table("fee_invoice") as batch_op:
            batch_op.drop_constraint("fk_fee_invoice_student_id", type_="foreignkey")
        with op.batch_alter_table("fee_assignment") as batch_op:
            batch_op.drop_constraint("fk_fee_assignment_student_id", type_="foreignkey")
    else:
        # Postgres or other DBs: normal FK drop
        op.drop_constraint("fk_fee_invoice_student_id", "fee_invoice", type_="foreignkey")
        op.drop_constraint("fk_fee_assignment_student_id", "fee_assignment", type_="foreignkey")
