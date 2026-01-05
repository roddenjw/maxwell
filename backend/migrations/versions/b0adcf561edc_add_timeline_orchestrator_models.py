"""add_timeline_orchestrator_models

Revision ID: b0adcf561edc
Revises: 927396b0fa40
Create Date: 2026-01-05 14:29:11.507167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0adcf561edc'
down_revision: Union[str, Sequence[str], None] = '927396b0fa40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Create TravelLeg table
    op.create_table(
        'travel_legs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('character_id', sa.String(), nullable=False),
        sa.Column('from_location_id', sa.String(), nullable=False),
        sa.Column('to_location_id', sa.String(), nullable=False),
        sa.Column('departure_event_id', sa.String(), nullable=False),
        sa.Column('arrival_event_id', sa.String(), nullable=False),
        sa.Column('travel_mode', sa.String(), nullable=False),
        sa.Column('distance_km', sa.Integer(), nullable=True),
        sa.Column('speed_kmh', sa.Integer(), nullable=True),
        sa.Column('required_hours', sa.Integer(), nullable=True),
        sa.Column('available_hours', sa.Integer(), nullable=True),
        sa.Column('is_feasible', sa.Integer(), nullable=True),
        sa.Column('leg_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['from_location_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['to_location_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['departure_event_id'], ['timeline_events.id'], ),
        sa.ForeignKeyConstraint(['arrival_event_id'], ['timeline_events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_travel_legs_manuscript_id', 'travel_legs', ['manuscript_id'])

    # 2. Create TravelSpeedProfile table
    op.create_table(
        'travel_speed_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('speeds', sa.JSON(), nullable=False),
        sa.Column('default_speed', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_travel_speed_profiles_manuscript_id', 'travel_speed_profiles', ['manuscript_id'], unique=True)

    # 3. Create LocationDistance table
    op.create_table(
        'location_distances',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('location_a_id', sa.String(), nullable=False),
        sa.Column('location_b_id', sa.String(), nullable=False),
        sa.Column('distance_km', sa.Integer(), nullable=False),
        sa.Column('distance_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['location_a_id'], ['entities.id'], ),
        sa.ForeignKeyConstraint(['location_b_id'], ['entities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_location_distances_manuscript_id', 'location_distances', ['manuscript_id'])

    # 4. Add columns to timeline_events
    op.add_column('timeline_events', sa.Column('narrative_importance', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('timeline_events', sa.Column('prerequisite_ids', sa.JSON(), nullable=False, server_default='[]'))

    # 5. Add columns to timeline_inconsistencies
    op.add_column('timeline_inconsistencies', sa.Column('suggestion', sa.Text(), nullable=True))
    op.add_column('timeline_inconsistencies', sa.Column('teaching_point', sa.Text(), nullable=True))
    op.add_column('timeline_inconsistencies', sa.Column('is_resolved', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('timeline_inconsistencies', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    op.add_column('timeline_inconsistencies', sa.Column('resolution_notes', sa.Text(), nullable=True))

    # 6. Add column to scenes
    op.add_column('scenes', sa.Column('pov_character_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_scenes_pov_character', 'scenes', 'entities', ['pov_character_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""

    # Reverse order of upgrade

    # 6. Remove pov_character_id from scenes
    op.drop_constraint('fk_scenes_pov_character', 'scenes', type_='foreignkey')
    op.drop_column('scenes', 'pov_character_id')

    # 5. Remove columns from timeline_inconsistencies
    op.drop_column('timeline_inconsistencies', 'resolution_notes')
    op.drop_column('timeline_inconsistencies', 'resolved_at')
    op.drop_column('timeline_inconsistencies', 'is_resolved')
    op.drop_column('timeline_inconsistencies', 'teaching_point')
    op.drop_column('timeline_inconsistencies', 'suggestion')

    # 4. Remove columns from timeline_events
    op.drop_column('timeline_events', 'prerequisite_ids')
    op.drop_column('timeline_events', 'narrative_importance')

    # 3. Drop LocationDistance table
    op.drop_index('ix_location_distances_manuscript_id', table_name='location_distances')
    op.drop_table('location_distances')

    # 2. Drop TravelSpeedProfile table
    op.drop_index('ix_travel_speed_profiles_manuscript_id', table_name='travel_speed_profiles')
    op.drop_table('travel_speed_profiles')

    # 1. Drop TravelLeg table
    op.drop_index('ix_travel_legs_manuscript_id', table_name='travel_legs')
    op.drop_table('travel_legs')
