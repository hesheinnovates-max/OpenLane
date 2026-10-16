"""rename users to job seekers

Revision ID: b207b80184db
Revises: eba2c160d559
Create Date: 2026-10-16 00:11:51.704343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b207b80184db'
down_revision: Union[str, Sequence[str], None] = 'eba2c160d559'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("users","job_seekers")
    op.drop_column("job_seekers","role")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "job_seekers",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="job_seeker")
    )
    op.alter_column("job_seekers", "role", server_default=None)
    op.rename_table("job_seekers", "users")
