# backend/migrations/versions/20251201_user_student_link.py

"""link user to student via student_id FK

Revision ID: 20251201_user_student_link
Revises: 20251108_payidempkey
Create Date: 2025-12-01 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251201_user_student_link"
down_revision: Union[str, Sequence[str], None] = "20251108_payidempkey"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(bind, table_name: str, column_name: str) -> bool:
    """
    Return True if the given table has the named column.
    Safe across dialects.
    """
    try:
        inspector = sa.inspect(bind)
        cols = inspector.get_columns(table_name)
        return any(c.get("name") == column_name for c in cols)
    except Exception:
        return False


def _pg_constraint_exists(bind, constraint_name: str) -> bool:
    """
    Postgres-only: check if a constraint with this name exists.
    """
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_constraint WHERE conname = :c"
            ),
            {"c": constraint_name},
        ).fetchall()
        return bool(res)
    except Exception:
        return False


def _pg_index_exists(bind, index_name: str) -> bool:
    """
    Postgres-only: check if an index with this name exists.
    """
    try:
        res = bind.execute(
            sa.text(
                "SELECT 1 FROM pg_indexes WHERE indexname = :i"
            ),
            {"i": index_name},
        ).fetchall()
        return bool(res)
    except Exception:
        return False


def upgrade() -> None:
    """
    Add user.student_id (nullable) and link it to students.id via FK.
    Safe even if column/FK already exist (as in your current DB).
    """
    bind = op.get_bind()

    # 1) Ensure column exists
    if not _has_column(bind, "user", "student_id"):
        # batch_alter_table works for both Postgres and SQLite
        with op.batch_alter_table("user", schema=None) as batch_op:
            batch_op.add_column(sa.Column("student_id", sa.Integer(), nullable=True))

    # 2) Add index + FK (best-effort, guarded)
    if bind.dialect.name == "postgresql":
        # Index on student_id for quick lookups
        if not _pg_index_exists(bind, "ix_user_student_id"):
            try:
                op.create_index(
                    "ix_user_student_id",
                    "user",
                    ["student_id"],
                    unique=False,
                )
            except Exception:
                # don't fail upgrade if index creation has issues
                pass

        # FK to students(id); in your manual ALTER TABLE you used this name:
        #   user_student_id_fkey
        if not _pg_constraint_exists(bind, "user_student_id_fkey"):
            try:
                op.create_foreign_key(
                    "user_student_id_fkey",
                    "user",
                    "students",
                    ["student_id"],
                    ["id"],
                )
            except Exception:
                # if something is odd, don't break migrations
                pass
    else:
        # SQLite / others: best-effort index + FK using batch mode
        # (Some SQLite setups may ignore FK operations; that's OK.)
        with op.batch_alter_table("user", schema=None) as batch_op:
            # index
            try:
                batch_op.create_index(
                    "ix_user_student_id",
                    ["student_id"],
                    unique=False,
                )
            except Exception:
                pass

            # FK
            try:
                batch_op.create_foreign_key(
                    "user_student_id_fkey",
                    "students",
                    ["student_id"],
                    ["id"],
                )
            except Exception:
                # If SQLite cannot alter FKs in-place, just skip – column is still usable.
                pass


def downgrade() -> None:
    """
    Remove FK, index, and student_id column (if present).
    """
    bind = op.get_bind()

    # 1) Drop FK + index
    if bind.dialect.name == "postgresql":
        # FK
        try:
            op.drop_constraint(
                "user_student_id_fkey",
                "user",
                type_="foreignkey",
            )
        except Exception:
            pass

        # index
        try:
            op.drop_index(
                "ix_user_student_id",
                table_name="user",
            )
        except Exception:
            pass
    else:
        # SQLite / others: batch_alter_table
        with op.batch_alter_table("user", schema=None) as batch_op:
            try:
                batch_op.drop_constraint(
                    "user_student_id_fkey",
                    type_="foreignkey",
                )
            except Exception:
                pass
            try:
                batch_op.drop_index("ix_user_student_id")
            except Exception:
                pass

    # 2) Drop column if it exists
    if _has_column(bind, "user", "student_id"):
        with op.batch_alter_table("user", schema=None) as batch_op:
            try:
                batch_op.drop_column("student_id")
            except Exception:
                pass
