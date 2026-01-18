"""extend_outline_scope

Revision ID: c7a0692cc159
Revises: 7b763aadcd27
Create Date: 2026-01-18 10:05:05.915024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a0692cc159'
down_revision: Union[str, Sequence[str], None] = '7b763aadcd27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing columns for outlines table
    outline_columns = [col['name'] for col in inspector.get_columns('outlines')]

    # Add scope field to outlines (defaults to MANUSCRIPT for existing rows)
    if 'scope' not in outline_columns:
        op.add_column('outlines', sa.Column('scope', sa.String(), nullable=False, server_default='MANUSCRIPT'))

    # Add series_id FK to outlines
    if 'series_id' not in outline_columns:
        op.add_column('outlines', sa.Column('series_id', sa.String(), nullable=True))
        # Create FK constraint - use batch mode for SQLite
        with op.batch_alter_table('outlines') as batch_op:
            batch_op.create_foreign_key('fk_outlines_series_id', 'series', ['series_id'], ['id'])

    # Add world_id FK to outlines
    if 'world_id' not in outline_columns:
        op.add_column('outlines', sa.Column('world_id', sa.String(), nullable=True))
        with op.batch_alter_table('outlines') as batch_op:
            batch_op.create_foreign_key('fk_outlines_world_id', 'worlds', ['world_id'], ['id'])

    # Add arc_type and book_count for series outlines
    if 'arc_type' not in outline_columns:
        op.add_column('outlines', sa.Column('arc_type', sa.String(), nullable=True))
    if 'book_count' not in outline_columns:
        op.add_column('outlines', sa.Column('book_count', sa.Integer(), nullable=True))

    # Get existing columns for plot_beats table
    beat_columns = [col['name'] for col in inspector.get_columns('plot_beats')]

    # Add linked_manuscript_outline_id FK to plot_beats
    if 'linked_manuscript_outline_id' not in beat_columns:
        op.add_column('plot_beats', sa.Column('linked_manuscript_outline_id', sa.String(), nullable=True))
        with op.batch_alter_table('plot_beats') as batch_op:
            batch_op.create_foreign_key('fk_plot_beats_linked_outline', 'outlines', ['linked_manuscript_outline_id'], ['id'])

    # Add target_book_index to plot_beats
    if 'target_book_index' not in beat_columns:
        op.add_column('plot_beats', sa.Column('target_book_index', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove plot_beats columns
    with op.batch_alter_table('plot_beats') as batch_op:
        batch_op.drop_constraint('fk_plot_beats_linked_outline', type_='foreignkey')
        batch_op.drop_column('linked_manuscript_outline_id')
        batch_op.drop_column('target_book_index')

    # Remove outlines columns
    with op.batch_alter_table('outlines') as batch_op:
        batch_op.drop_constraint('fk_outlines_series_id', type_='foreignkey')
        batch_op.drop_constraint('fk_outlines_world_id', type_='foreignkey')
        batch_op.drop_column('series_id')
        batch_op.drop_column('world_id')
        batch_op.drop_column('scope')
        batch_op.drop_column('arc_type')
        batch_op.drop_column('book_count')
