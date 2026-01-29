"""Add document types to chapters

Revision ID: a1b2c3d4e5f6
Revises: c0c667aea4c0
Create Date: 2026-01-29 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c0c667aea4c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add document_type, linked_entity_id, and document_metadata columns to chapters.
    Migrate existing is_folder values to document_type.
    """
    # Add columns one at a time (SQLite-compatible approach)
    op.add_column('chapters', sa.Column('document_type', sa.String(), nullable=True, server_default='CHAPTER'))
    op.add_column('chapters', sa.Column('linked_entity_id', sa.String(), nullable=True))
    op.add_column('chapters', sa.Column('document_metadata', sa.JSON(), nullable=True))

    # Note: SQLite doesn't support adding foreign key constraints to existing tables.
    # The FK relationship is defined in the SQLAlchemy model and will be enforced
    # at the application layer. For new databases, the FK will be created properly.

    # Migrate existing data: is_folder=1 -> FOLDER, is_folder=0 -> CHAPTER
    op.execute("""
        UPDATE chapters
        SET document_type = CASE
            WHEN is_folder = 1 THEN 'FOLDER'
            ELSE 'CHAPTER'
        END
    """)


def downgrade() -> None:
    """Remove document type columns from chapters."""
    op.drop_column('chapters', 'document_metadata')
    op.drop_column('chapters', 'linked_entity_id')
    op.drop_column('chapters', 'document_type')
