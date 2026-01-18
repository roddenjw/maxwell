"""Add entity templates and source references

Revision ID: ff71c8960d33
Revises: 667afa76321f
Create Date: 2026-01-18 09:48:11.966306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff71c8960d33'
down_revision: Union[str, Sequence[str], None] = '667afa76321f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add entity template support and source references table."""
    # Add template_type column to entities
    op.add_column('entities', sa.Column('template_type', sa.String(), nullable=True))

    # Add template_data column to entities (JSON for structured template fields)
    op.add_column('entities', sa.Column('template_data', sa.JSON(), nullable=True))

    # Create entity_source_references table for tracking text sources
    op.create_table(
        'entity_source_references',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('entity_id', sa.String(), sa.ForeignKey('entities.id'), nullable=False),
        sa.Column('field_path', sa.String(), nullable=False),
        sa.Column('chapter_id', sa.String(), sa.ForeignKey('chapters.id'), nullable=True),
        sa.Column('text_excerpt', sa.Text(), nullable=False),
        sa.Column('character_offset', sa.Integer(), nullable=True),
        sa.Column('is_confirmed', sa.String(), server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Remove entity template support and source references table."""
    op.drop_table('entity_source_references')
    op.drop_column('entities', 'template_data')
    op.drop_column('entities', 'template_type')
