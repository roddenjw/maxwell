"""add_chapters_table

Revision ID: 6ee849b26379
Revises: 42864dc9bc1b
Create Date: 2025-12-23 22:21:58.158245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ee849b26379'
down_revision: Union[str, Sequence[str], None] = '42864dc9bc1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create chapters table
    op.create_table(
        'chapters',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('manuscript_id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('is_folder', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('lexical_state', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['chapters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add chapter_id column to scenes table
    op.add_column('scenes', sa.Column('chapter_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_scenes_chapter_id', 'scenes', 'chapters', ['chapter_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove chapter_id from scenes
    op.drop_constraint('fk_scenes_chapter_id', 'scenes', type_='foreignkey')
    op.drop_column('scenes', 'chapter_id')

    # Drop chapters table
    op.drop_table('chapters')
