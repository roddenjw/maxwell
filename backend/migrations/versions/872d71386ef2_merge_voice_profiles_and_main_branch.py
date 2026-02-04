"""Merge voice profiles and main branch

Revision ID: 872d71386ef2
Revises: 6373dd2b7c64, voice_profiles_001
Create Date: 2026-02-04 01:58:01.305071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '872d71386ef2'
down_revision: Union[str, Sequence[str], None] = ('6373dd2b7c64', 'voice_profiles_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
