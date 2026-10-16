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
    op.rename_table("users", "job_seekers")
    op.drop_column("job_seekers", "role")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "job_seekers",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="job_seeker",
        ),
    )
    op.alter_column("job_seekers", "role", server_default=None)
    op.rename_table("job_seekers", "users")