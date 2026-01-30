"""Add premise genre fields to manuscript

Revision ID: 84e8effbea54
Revises: a1b2c3d4e5f6
Create Date: 2026-01-29 20:11:59.126950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84e8effbea54'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add story metadata fields to manuscripts
    op.add_column('manuscripts', sa.Column('premise', sa.Text(), nullable=True))
    op.add_column('manuscripts', sa.Column('premise_source', sa.String(), nullable=True))
    op.add_column('manuscripts', sa.Column('genre', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('manuscripts', 'genre')
    op.drop_column('manuscripts', 'premise_source')
    op.drop_column('manuscripts', 'premise')
