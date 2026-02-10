"""Add linked_wiki_entry_id to entities

Revision ID: 329badabeec0
Revises: 211d0b85589f
Create Date: 2026-02-09 21:40:48.751538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '329badabeec0'
down_revision: Union[str, Sequence[str], None] = '211d0b85589f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add linked_wiki_entry_id column to entities table."""
    op.add_column('entities', sa.Column('linked_wiki_entry_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove linked_wiki_entry_id column from entities table."""
    op.drop_column('entities', 'linked_wiki_entry_id')
