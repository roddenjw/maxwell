"""add_entity_timeline_states

Revision ID: 7b763aadcd27
Revises: ff71c8960d33
Create Date: 2026-01-18 09:57:54.332630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b763aadcd27'
down_revision: Union[str, Sequence[str], None] = 'ff71c8960d33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table already exists (may have been created by another agent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'entity_timeline_states' not in tables:
        # Create entity_timeline_states table
        op.create_table(
            'entity_timeline_states',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('entity_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
            sa.Column('manuscript_id', sa.String(), sa.ForeignKey('manuscripts.id'), nullable=True),
            sa.Column('chapter_id', sa.String(), sa.ForeignKey('chapters.id'), nullable=True),
            sa.Column('timeline_event_id', sa.String(), sa.ForeignKey('timeline_events.id'), nullable=True),
            sa.Column('order_index', sa.Integer(), default=0),
            sa.Column('narrative_timestamp', sa.String(), nullable=True),
            sa.Column('state_data', sa.JSON(), default=dict),
            sa.Column('label', sa.String(), nullable=True),
            sa.Column('is_canonical', sa.Integer(), default=1),
            sa.Column('created_at', sa.DateTime()),
            sa.Column('updated_at', sa.DateTime()),
        )

        # Create indexes for efficient querying
        op.create_index('ix_entity_timeline_states_entity_id', 'entity_timeline_states', ['entity_id'])
        op.create_index('ix_entity_timeline_states_manuscript_id', 'entity_timeline_states', ['manuscript_id'])

    # Add chapter_id index if missing
    indexes = inspector.get_indexes('entity_timeline_states')
    index_names = [idx['name'] for idx in indexes]
    if 'ix_entity_timeline_states_chapter_id' not in index_names:
        op.create_index('ix_entity_timeline_states_chapter_id', 'entity_timeline_states', ['chapter_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_entity_timeline_states_chapter_id', table_name='entity_timeline_states')
    op.drop_index('ix_entity_timeline_states_manuscript_id', table_name='entity_timeline_states')
    op.drop_index('ix_entity_timeline_states_entity_id', table_name='entity_timeline_states')
    op.drop_table('entity_timeline_states')
