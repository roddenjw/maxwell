"""Add proactive nudges and weekly insights tables

Revision ID: proactive_nudges_001
Revises: maxwell_conv_001
Create Date: 2026-02-02 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'proactive_nudges_001'
down_revision: Union[str, Sequence[str], None] = 'maxwell_conv_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create proactive_nudges table
    op.create_table('proactive_nudges',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=True),
        sa.Column('chapter_id', sa.String(), nullable=True),
        sa.Column('nudge_type', sa.String(), nullable=False),
        sa.Column('priority', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('content_hash', sa.String(), nullable=True),
        sa.Column('dismissed', sa.Boolean(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('viewed', sa.Boolean(), nullable=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_proactive_nudges_user_id'), 'proactive_nudges', ['user_id'], unique=False)
    op.create_index(op.f('ix_proactive_nudges_manuscript_id'), 'proactive_nudges', ['manuscript_id'], unique=False)
    op.create_index(op.f('ix_proactive_nudges_content_hash'), 'proactive_nudges', ['content_hash'], unique=False)

    # Create weekly_insights table
    op.create_table('weekly_insights',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('week_start', sa.DateTime(), nullable=False),
        sa.Column('week_end', sa.DateTime(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('highlights', sa.JSON(), nullable=True),
        sa.Column('areas_to_improve', sa.JSON(), nullable=True),
        sa.Column('word_count_total', sa.Integer(), nullable=True),
        sa.Column('chapters_worked_on', sa.Integer(), nullable=True),
        sa.Column('most_active_day', sa.String(), nullable=True),
        sa.Column('analyses_run', sa.Integer(), nullable=True),
        sa.Column('issues_found', sa.Integer(), nullable=True),
        sa.Column('issues_addressed', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weekly_insights_user_id'), 'weekly_insights', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_weekly_insights_user_id'), table_name='weekly_insights')
    op.drop_table('weekly_insights')
    op.drop_index(op.f('ix_proactive_nudges_content_hash'), table_name='proactive_nudges')
    op.drop_index(op.f('ix_proactive_nudges_manuscript_id'), table_name='proactive_nudges')
    op.drop_index(op.f('ix_proactive_nudges_user_id'), table_name='proactive_nudges')
    op.drop_table('proactive_nudges')
