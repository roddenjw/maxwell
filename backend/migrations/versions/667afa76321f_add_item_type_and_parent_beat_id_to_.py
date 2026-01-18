"""Add item_type and parent_beat_id to plot_beats for scenes

Revision ID: 667afa76321f
Revises: 0d9d99acaca3
Create Date: 2026-01-18 09:30:14.001739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '667afa76321f'
down_revision: Union[str, Sequence[str], None] = '0d9d99acaca3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add item_type and parent_beat_id columns to plot_beats for scene support."""
    # Add columns using simple add_column (SQLite-compatible)
    # item_type: BEAT (major story beat) or SCENE (user-added between beats)
    op.add_column('plot_beats', sa.Column('item_type', sa.String(), nullable=False, server_default='BEAT'))

    # parent_beat_id: For SCENE items, links to the beat this scene follows
    op.add_column('plot_beats', sa.Column('parent_beat_id', sa.String(), nullable=True))

    # Note: Foreign key constraint omitted for SQLite compatibility
    # The relationship is enforced at the application level


def downgrade() -> None:
    """Remove scene support columns from plot_beats."""
    op.drop_column('plot_beats', 'parent_beat_id')
    op.drop_column('plot_beats', 'item_type')
