"""fix job seekers table name

Revision ID: 7b875fad9535
Revises: b207b80184db
Create Date: 2026-10-16 00:27:02.710897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b875fad9535'
down_revision: Union[str, Sequence[str], None] = 'b207b80184db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The previous revision (b207b80184db) already renames the table.
    # Only rename here if the old "users" table is still there, so a fresh
    # database can run every migration from the start without failing.
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("users") and not inspector.has_table("job_seekers"):
        op.rename_table("users", "job_seekers")
        op.drop_column("job_seekers", "role")


def downgrade() -> None:
    """Downgrade schema."""
    # Nothing to undo, b207b80184db handles the rename on downgrade.
    pass