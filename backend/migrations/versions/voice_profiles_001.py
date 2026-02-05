"""Add voice profile models

Revision ID: voice_profiles_001
Revises:
Create Date: 2026-02-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'voice_profiles_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create character_voice_profiles table
    op.create_table(
        'character_voice_profiles',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('character_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('manuscript_id', sa.String(), sa.ForeignKey('manuscripts.id'), nullable=False),
        sa.Column('profile_data', sa.JSON(), default=dict),
        sa.Column('confidence_score', sa.Float(), default=0.0),
        sa.Column('calculated_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    # Create voice_inconsistencies table
    op.create_table(
        'voice_inconsistencies',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('manuscript_id', sa.String(), sa.ForeignKey('manuscripts.id'), nullable=False),
        sa.Column('character_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('chapter_id', sa.String(), sa.ForeignKey('chapters.id'), nullable=False),
        sa.Column('profile_id', sa.String(), sa.ForeignKey('character_voice_profiles.id'), nullable=True),
        sa.Column('inconsistency_type', sa.String()),
        sa.Column('severity', sa.String(), default='medium'),
        sa.Column('description', sa.Text()),
        sa.Column('dialogue_excerpt', sa.Text()),
        sa.Column('start_offset', sa.Integer()),
        sa.Column('end_offset', sa.Integer()),
        sa.Column('expected_value', sa.String()),
        sa.Column('actual_value', sa.String()),
        sa.Column('suggestion', sa.Text()),
        sa.Column('teaching_point', sa.Text()),
        sa.Column('is_resolved', sa.Integer(), default=0),
        sa.Column('user_feedback', sa.String()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('resolved_at', sa.DateTime()),
    )

    # Create voice_comparisons table
    op.create_table(
        'voice_comparisons',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('manuscript_id', sa.String(), sa.ForeignKey('manuscripts.id'), nullable=False),
        sa.Column('character_a_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('character_b_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('overall_similarity', sa.Float()),
        sa.Column('vocabulary_similarity', sa.Float()),
        sa.Column('structure_similarity', sa.Float()),
        sa.Column('formality_similarity', sa.Float()),
        sa.Column('comparison_data', sa.JSON(), default=dict),
        sa.Column('calculated_at', sa.DateTime()),
    )

    # Create indexes for common queries
    op.create_index(
        'ix_voice_profiles_manuscript_character',
        'character_voice_profiles',
        ['manuscript_id', 'character_id']
    )
    op.create_index(
        'ix_voice_inconsistencies_manuscript',
        'voice_inconsistencies',
        ['manuscript_id']
    )
    op.create_index(
        'ix_voice_inconsistencies_character',
        'voice_inconsistencies',
        ['character_id']
    )


def downgrade() -> None:
    op.drop_index('ix_voice_inconsistencies_character')
    op.drop_index('ix_voice_inconsistencies_manuscript')
    op.drop_index('ix_voice_profiles_manuscript_character')
    op.drop_table('voice_comparisons')
    op.drop_table('voice_inconsistencies')
    op.drop_table('character_voice_profiles')
