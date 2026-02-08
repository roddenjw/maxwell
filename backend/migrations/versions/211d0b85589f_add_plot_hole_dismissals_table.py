"""Add plot_hole_dismissals table

Revision ID: 211d0b85589f
Revises: ef33b5c6d4b7
Create Date: 2026-02-08 17:07:06.578613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '211d0b85589f'
down_revision: Union[str, Sequence[str], None] = 'ef33b5c6d4b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('plot_hole_dismissals',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('outline_id', sa.String(), nullable=False),
    sa.Column('plot_hole_hash', sa.String(), nullable=False),
    sa.Column('severity', sa.String(), nullable=False),
    sa.Column('location', sa.String(), nullable=False),
    sa.Column('issue', sa.String(), nullable=False),
    sa.Column('suggestion', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('user_explanation', sa.Text(), nullable=True),
    sa.Column('ai_fix_suggestions', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['outline_id'], ['outlines.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('plot_hole_dismissals')
