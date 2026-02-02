"""Add Maxwell conversation, insight, and preferences tables

Revision ID: maxwell_conv_001
Revises: 6373dd2b7c64
Create Date: 2026-02-02 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'maxwell_conv_001'
down_revision: Union[str, Sequence[str], None] = '6373dd2b7c64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create maxwell_conversations table
    op.create_table('maxwell_conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=True),
        sa.Column('chapter_id', sa.String(), nullable=True),
        sa.Column('interaction_type', sa.String(), nullable=False),
        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('analyzed_text', sa.Text(), nullable=True),
        sa.Column('maxwell_response', sa.Text(), nullable=False),
        sa.Column('response_type', sa.String(), nullable=False),
        sa.Column('feedback_data', sa.JSON(), nullable=True),
        sa.Column('agents_consulted', sa.JSON(), nullable=True),
        sa.Column('focus_area', sa.String(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('tokens', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maxwell_conversations_user_id'), 'maxwell_conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_maxwell_conversations_manuscript_id'), 'maxwell_conversations', ['manuscript_id'], unique=False)
    op.create_index(op.f('ix_maxwell_conversations_interaction_type'), 'maxwell_conversations', ['interaction_type'], unique=False)

    # Create maxwell_insights table
    op.create_table('maxwell_insights',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=True),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('insight_text', sa.Text(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('sentiment', sa.String(), nullable=True),
        sa.Column('importance', sa.Float(), nullable=True),
        sa.Column('resolved', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.ForeignKeyConstraint(['conversation_id'], ['maxwell_conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maxwell_insights_user_id'), 'maxwell_insights', ['user_id'], unique=False)
    op.create_index(op.f('ix_maxwell_insights_manuscript_id'), 'maxwell_insights', ['manuscript_id'], unique=False)
    op.create_index(op.f('ix_maxwell_insights_category'), 'maxwell_insights', ['category'], unique=False)
    op.create_index(op.f('ix_maxwell_insights_subject'), 'maxwell_insights', ['subject'], unique=False)

    # Create maxwell_preferences table
    op.create_table('maxwell_preferences',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('preferred_tone', sa.String(), nullable=True),
        sa.Column('feedback_depth', sa.String(), nullable=True),
        sa.Column('teaching_mode', sa.String(), nullable=True),
        sa.Column('priority_focus', sa.String(), nullable=True),
        sa.Column('proactive_suggestions', sa.String(), nullable=True),
        sa.Column('extra_preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('maxwell_preferences')
    op.drop_index(op.f('ix_maxwell_insights_subject'), table_name='maxwell_insights')
    op.drop_index(op.f('ix_maxwell_insights_category'), table_name='maxwell_insights')
    op.drop_index(op.f('ix_maxwell_insights_manuscript_id'), table_name='maxwell_insights')
    op.drop_index(op.f('ix_maxwell_insights_user_id'), table_name='maxwell_insights')
    op.drop_table('maxwell_insights')
    op.drop_index(op.f('ix_maxwell_conversations_interaction_type'), table_name='maxwell_conversations')
    op.drop_index(op.f('ix_maxwell_conversations_manuscript_id'), table_name='maxwell_conversations')
    op.drop_index(op.f('ix_maxwell_conversations_user_id'), table_name='maxwell_conversations')
    op.drop_table('maxwell_conversations')
