"""Add foreshadowing tracking

Revision ID: b82e33877858
Revises: c7a0692cc159
Create Date: 2026-01-21 21:11:10.354126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b82e33877858'
down_revision: Union[str, Sequence[str], None] = 'c7a0692cc159'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create foreshadowing_pairs table
    op.create_table(
        'foreshadowing_pairs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('foreshadowing_event_id', sa.String(), nullable=False),
        sa.Column('foreshadowing_type', sa.String(), nullable=False, server_default='HINT'),
        sa.Column('foreshadowing_text', sa.Text(), nullable=False),
        sa.Column('payoff_event_id', sa.String(), nullable=True),
        sa.Column('payoff_text', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['foreshadowing_event_id'], ['timeline_events.id']),
        sa.ForeignKeyConstraint(['payoff_event_id'], ['timeline_events.id']),
    )
    op.create_index('ix_foreshadowing_pairs_manuscript_id', 'foreshadowing_pairs', ['manuscript_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_foreshadowing_pairs_manuscript_id', table_name='foreshadowing_pairs')
    op.drop_table('foreshadowing_pairs')
