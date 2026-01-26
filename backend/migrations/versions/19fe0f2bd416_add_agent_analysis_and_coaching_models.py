"""Add agent analysis and coaching models

Revision ID: 19fe0f2bd416
Revises: e8d7af9fed4c
Create Date: 2026-01-25 21:03:50.188249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19fe0f2bd416'
down_revision: Union[str, Sequence[str], None] = 'e8d7af9fed4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create new agent-related tables
    op.create_table('author_learning',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('pattern_type', sa.String(), nullable=False),
    sa.Column('pattern_key', sa.String(), nullable=False),
    sa.Column('pattern_data', sa.JSON(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('observation_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['writing_profiles.user_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_author_learning_user_id'), 'author_learning', ['user_id'], unique=False)

    op.create_table('coach_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('manuscript_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('initial_context', sa.JSON(), nullable=True),
    sa.Column('message_count', sa.Integer(), nullable=True),
    sa.Column('total_cost', sa.Float(), nullable=True),
    sa.Column('total_tokens', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('last_message_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coach_sessions_user_id'), 'coach_sessions', ['user_id'], unique=False)

    op.create_table('agent_analyses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('manuscript_id', sa.String(), nullable=False),
    sa.Column('chapter_id', sa.String(), nullable=True),
    sa.Column('input_text', sa.Text(), nullable=False),
    sa.Column('input_hash', sa.String(), nullable=True),
    sa.Column('agent_types', sa.JSON(), nullable=False),
    sa.Column('recommendations', sa.JSON(), nullable=True),
    sa.Column('issues', sa.JSON(), nullable=True),
    sa.Column('teaching_points', sa.JSON(), nullable=True),
    sa.Column('agent_results', sa.JSON(), nullable=True),
    sa.Column('total_cost', sa.Float(), nullable=True),
    sa.Column('total_tokens', sa.Integer(), nullable=True),
    sa.Column('execution_time_ms', sa.Integer(), nullable=True),
    sa.Column('user_rating', sa.Integer(), nullable=True),
    sa.Column('user_feedback', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
    sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_analyses_manuscript_id'), 'agent_analyses', ['manuscript_id'], unique=False)
    op.create_index(op.f('ix_agent_analyses_user_id'), 'agent_analyses', ['user_id'], unique=False)

    op.create_table('coach_messages',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('tools_used', sa.JSON(), nullable=True),
    sa.Column('tool_results', sa.JSON(), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.Column('tokens', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['coach_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('suggestion_feedback',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=True),
    sa.Column('agent_type', sa.String(), nullable=False),
    sa.Column('suggestion_type', sa.String(), nullable=False),
    sa.Column('suggestion_text', sa.Text(), nullable=False),
    sa.Column('original_text', sa.Text(), nullable=True),
    sa.Column('manuscript_id', sa.String(), nullable=True),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('modified_text', sa.Text(), nullable=True),
    sa.Column('user_explanation', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['agent_analyses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suggestion_feedback_user_id'), 'suggestion_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_suggestion_feedback_user_id'), table_name='suggestion_feedback')
    op.drop_table('suggestion_feedback')
    op.drop_table('coach_messages')
    op.drop_index(op.f('ix_agent_analyses_user_id'), table_name='agent_analyses')
    op.drop_index(op.f('ix_agent_analyses_manuscript_id'), table_name='agent_analyses')
    op.drop_table('agent_analyses')
    op.drop_index(op.f('ix_coach_sessions_user_id'), table_name='coach_sessions')
    op.drop_table('coach_sessions')
    op.drop_index(op.f('ix_author_learning_user_id'), table_name='author_learning')
    op.drop_table('author_learning')
