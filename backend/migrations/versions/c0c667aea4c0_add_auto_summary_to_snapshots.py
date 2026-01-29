"""Add auto_summary to snapshots

Revision ID: c0c667aea4c0
Revises: 19fe0f2bd416
Create Date: 2026-01-29 14:04:25.833189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0c667aea4c0'
down_revision: Union[str, Sequence[str], None] = '19fe0f2bd416'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add auto_summary column to snapshots table for auto-generated changeset summaries."""
    op.add_column('snapshots', sa.Column('auto_summary', sa.Text(), nullable=True, server_default=''))


def downgrade() -> None:
    """Remove auto_summary column from snapshots table."""
    op.drop_column('snapshots', 'auto_summary')
