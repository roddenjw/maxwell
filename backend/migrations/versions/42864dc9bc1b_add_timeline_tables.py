"""add_timeline_tables

Revision ID: 42864dc9bc1b
Revises: b8b0d4d0f396
Create Date: 2025-12-22 23:48:28.583326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42864dc9bc1b'
down_revision: Union[str, Sequence[str], None] = 'b8b0d4d0f396'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create timeline_events table
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('manuscript_id', sa.String(), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, default=0),
        sa.Column('timestamp', sa.String(), nullable=True),
        sa.Column('location_id', sa.String(), sa.ForeignKey('entities.id'), nullable=True),
        sa.Column('character_ids', sa.JSON(), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # Create character_locations table
    op.create_table(
        'character_locations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('manuscript_id', sa.String(), nullable=False, index=True),
        sa.Column('character_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('event_id', sa.String(), sa.ForeignKey('timeline_events.id'), nullable=False),
        sa.Column('location_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # Create timeline_inconsistencies table
    op.create_table(
        'timeline_inconsistencies',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('manuscript_id', sa.String(), nullable=False, index=True),
        sa.Column('inconsistency_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('affected_event_ids', sa.JSON(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('timeline_inconsistencies')
    op.drop_table('character_locations')
    op.drop_table('timeline_events')
