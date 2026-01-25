"""Add extracted_description and extracted_attributes to entity_suggestions

Revision ID: e8d7af9fed4c
Revises: b82e33877858
Create Date: 2026-01-25 15:40:26.637382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8d7af9fed4c'
down_revision: Union[str, Sequence[str], None] = 'b82e33877858'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add extracted information columns to entity_suggestions
    op.add_column('entity_suggestions', sa.Column('extracted_description', sa.Text(), nullable=True))
    op.add_column('entity_suggestions', sa.Column('extracted_attributes', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('entity_suggestions', 'extracted_attributes')
    op.drop_column('entity_suggestions', 'extracted_description')
