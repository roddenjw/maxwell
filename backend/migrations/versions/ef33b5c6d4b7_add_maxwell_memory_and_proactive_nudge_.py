"""Add Maxwell memory and proactive nudge tables

Revision ID: ef33b5c6d4b7
Revises: 017c14e9d06a
Create Date: 2026-02-04 21:06:03.831114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ef33b5c6d4b7'
down_revision: Union[str, Sequence[str], None] = '017c14e9d06a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add Maxwell memory, proactive nudges, and related tables."""

    # Maxwell Preferences
    op.create_table('maxwell_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('preferred_tone', sa.String(), nullable=True),
        sa.Column('feedback_depth', sa.String(), nullable=True),
        sa.Column('teaching_mode', sa.String(), nullable=True),
        sa.Column('priority_focus', sa.String(), nullable=True),
        sa.Column('proactive_suggestions', sa.String(), nullable=True),
        sa.Column('extra_preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maxwell_preferences_user_id'), 'maxwell_preferences', ['user_id'], unique=True)

    # Weekly Insights
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

    # Wiki Entries
    op.create_table('wiki_entries',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('world_id', sa.String(), nullable=False),
        sa.Column('entry_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('structured_data', sa.JSON(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('image_seed', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('linked_entity_id', sa.String(), nullable=True),
        sa.Column('source_manuscripts', sa.JSON(), nullable=True),
        sa.Column('source_chapters', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['linked_entity_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['wiki_entries.id'], ),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # World Rules
    op.create_table('world_rules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('wiki_entry_id', sa.String(), nullable=True),
        sa.Column('world_id', sa.String(), nullable=False),
        sa.Column('rule_type', sa.String(), nullable=True),
        sa.Column('rule_name', sa.String(), nullable=False),
        sa.Column('rule_description', sa.Text(), nullable=True),
        sa.Column('condition', sa.Text(), nullable=True),
        sa.Column('requirement', sa.Text(), nullable=True),
        sa.Column('validation_keywords', sa.JSON(), nullable=True),
        sa.Column('validation_pattern', sa.Text(), nullable=True),
        sa.Column('exception_keywords', sa.JSON(), nullable=True),
        sa.Column('exception_pattern', sa.Text(), nullable=True),
        sa.Column('valid_examples', sa.JSON(), nullable=True),
        sa.Column('violation_examples', sa.JSON(), nullable=True),
        sa.Column('violation_message', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('check_scope', sa.JSON(), nullable=True),
        sa.Column('violation_count', sa.Integer(), nullable=True),
        sa.Column('last_violation_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['wiki_entry_id'], ['wiki_entries.id'], ),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Character Arcs
    op.create_table('character_arcs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('wiki_entry_id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('arc_template', sa.String(), nullable=True),
        sa.Column('arc_name', sa.String(), nullable=True),
        sa.Column('planned_arc', sa.JSON(), nullable=True),
        sa.Column('detected_arc', sa.JSON(), nullable=True),
        sa.Column('arc_beats', sa.JSON(), nullable=True),
        sa.Column('custom_stages', sa.JSON(), nullable=True),
        sa.Column('arc_completion', sa.Float(), nullable=True),
        sa.Column('arc_health', sa.String(), nullable=True),
        sa.Column('arc_deviation_notes', sa.Text(), nullable=True),
        sa.Column('last_analyzed_at', sa.DateTime(), nullable=True),
        sa.Column('analysis_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.ForeignKeyConstraint(['wiki_entry_id'], ['wiki_entries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Maxwell Conversations
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
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maxwell_conversations_manuscript_id'), 'maxwell_conversations', ['manuscript_id'], unique=False)
    op.create_index(op.f('ix_maxwell_conversations_user_id'), 'maxwell_conversations', ['user_id'], unique=False)

    # Proactive Nudges
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
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_proactive_nudges_content_hash'), 'proactive_nudges', ['content_hash'], unique=False)
    op.create_index(op.f('ix_proactive_nudges_manuscript_id'), 'proactive_nudges', ['manuscript_id'], unique=False)
    op.create_index(op.f('ix_proactive_nudges_user_id'), 'proactive_nudges', ['user_id'], unique=False)

    # Rule Violations
    op.create_table('rule_violations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('chapter_id', sa.String(), nullable=True),
        sa.Column('text_excerpt', sa.Text(), nullable=False),
        sa.Column('character_offset', sa.Integer(), nullable=True),
        sa.Column('surrounding_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('dismissed_reason', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['world_rules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Wiki Changes
    op.create_table('wiki_changes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('wiki_entry_id', sa.String(), nullable=True),
        sa.Column('world_id', sa.String(), nullable=False),
        sa.Column('change_type', sa.String(), nullable=False),
        sa.Column('field_changed', sa.String(), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=False),
        sa.Column('proposed_entry', sa.JSON(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('source_chapter_id', sa.String(), nullable=True),
        sa.Column('source_manuscript_id', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewer_note', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_chapter_id'], ['chapters.id'], ),
        sa.ForeignKeyConstraint(['source_manuscript_id'], ['manuscripts.id'], ),
        sa.ForeignKeyConstraint(['wiki_entry_id'], ['wiki_entries.id'], ),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Wiki Cross References
    op.create_table('wiki_cross_references',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_entry_id', sa.String(), nullable=False),
        sa.Column('target_entry_id', sa.String(), nullable=False),
        sa.Column('reference_type', sa.String(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('context_chapter_id', sa.String(), nullable=True),
        sa.Column('bidirectional', sa.Integer(), nullable=True),
        sa.Column('display_label', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['context_chapter_id'], ['chapters.id'], ),
        sa.ForeignKeyConstraint(['source_entry_id'], ['wiki_entries.id'], ),
        sa.ForeignKeyConstraint(['target_entry_id'], ['wiki_entries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Maxwell Insights
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
        sa.ForeignKeyConstraint(['conversation_id'], ['maxwell_conversations.id'], ),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_maxwell_insights_manuscript_id'), 'maxwell_insights', ['manuscript_id'], unique=False)
    op.create_index(op.f('ix_maxwell_insights_user_id'), 'maxwell_insights', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_maxwell_insights_user_id'), table_name='maxwell_insights')
    op.drop_index(op.f('ix_maxwell_insights_manuscript_id'), table_name='maxwell_insights')
    op.drop_table('maxwell_insights')
    op.drop_table('wiki_cross_references')
    op.drop_table('wiki_changes')
    op.drop_table('rule_violations')
    op.drop_index(op.f('ix_proactive_nudges_user_id'), table_name='proactive_nudges')
    op.drop_index(op.f('ix_proactive_nudges_manuscript_id'), table_name='proactive_nudges')
    op.drop_index(op.f('ix_proactive_nudges_content_hash'), table_name='proactive_nudges')
    op.drop_table('proactive_nudges')
    op.drop_index(op.f('ix_maxwell_conversations_user_id'), table_name='maxwell_conversations')
    op.drop_index(op.f('ix_maxwell_conversations_manuscript_id'), table_name='maxwell_conversations')
    op.drop_table('maxwell_conversations')
    op.drop_table('character_arcs')
    op.drop_table('world_rules')
    op.drop_table('wiki_entries')
    op.drop_index(op.f('ix_weekly_insights_user_id'), table_name='weekly_insights')
    op.drop_table('weekly_insights')
    op.drop_index(op.f('ix_maxwell_preferences_user_id'), table_name='maxwell_preferences')
    op.drop_table('maxwell_preferences')
