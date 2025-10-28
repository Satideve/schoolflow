"""add created_by to receipt

Revision ID: 4832b4808674
Revises: 'd29d4f37f099'
Create Date: 2025-09-25 16:11:28.872458
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4832b4808674'
down_revision: Union[str, Sequence[str], None] = "d29d4f37f099"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Add column as nullable (to avoid NOT NULL violation on existing rows)
    op.add_column('receipt', sa.Column('created_by', sa.Integer(), nullable=True))

    # 2) Create index early (doesn't depend on NOT NULL)
    op.create_index(op.f('ix_receipt_created_by'), 'receipt', ['created_by'], unique=False)

    # 3) Backfill existing rows with a valid user id if available
    bind = op.get_bind()
    user_id = bind.execute(sa.text('SELECT id FROM "user" ORDER BY id LIMIT 1')).scalar()

    if user_id is not None:
        # Backfill with the existing user's id
        bind.execute(sa.text('UPDATE "receipt" SET created_by = :uid').bindparams(uid=user_id))

        # 4) Enforce NOT NULL after backfill
        op.alter_column('receipt', 'created_by', existing_type=sa.Integer(), nullable=False)

        # 5) Add FK constraint now that data is valid
        op.create_foreign_key(
            'fk_receipt_created_by_user',
            'receipt',
            'user',
            ['created_by'],
            ['id'],
        )
    else:
        # No users present; leave column nullable and skip FK to avoid invalid references.
        # You can add a user and a follow-up migration to enforce NOT NULL and FK later.
        pass


def downgrade() -> None:
    """Downgrade schema."""
    # Drop FK if it exists (use the named constraint)
    with op.get_context().autocommit_block():
        try:
            op.drop_constraint('fk_receipt_created_by_user', 'receipt', type_='foreignkey')
        except Exception:
            # Constraint may not exist if upgrade skipped FK due to no users
            pass

    # Drop index
    op.drop_index(op.f('ix_receipt_created_by'), table_name='receipt')

    # Drop column
    op.drop_column('receipt', 'created_by')
