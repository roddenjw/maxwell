"""Add source_chapter_id to timeline_events

Revision ID: 6373dd2b7c64
Revises: 84e8effbea54
Create Date: 2026-01-29 20:53:59.553485

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6373dd2b7c64'
down_revision: Union[str, Sequence[str], None] = '84e8effbea54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add source tracking columns to timeline_events."""
    # Only add the new columns - no other schema changes
    op.add_column('timeline_events', sa.Column('source_chapter_id', sa.String(), nullable=True))
    op.add_column('timeline_events', sa.Column('source_text_offset', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove source tracking columns from timeline_events."""
    op.drop_column('timeline_events', 'source_text_offset')
    op.drop_column('timeline_events', 'source_chapter_id')
