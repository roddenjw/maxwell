"""Add world and series hierarchy

Revision ID: 0d9d99acaca3
Revises: e78f3edaca04
Create Date: 2026-01-18 09:12:15.306277

"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d9d99acaca3'
down_revision: Union[str, Sequence[str], None] = 'e78f3edaca04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create worlds table
    op.create_table('worlds',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create series table
    op.create_table('series',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('world_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['world_id'], ['worlds.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Add columns to entities
    op.add_column('entities', sa.Column('world_id', sa.String(), nullable=True))
    op.add_column('entities', sa.Column('scope', sa.String(), server_default='MANUSCRIPT', nullable=False))

    # Make manuscript_id nullable for world-scoped entities
    # SQLite doesn't support ALTER COLUMN, so we need to handle this differently
    # The column is already nullable in SQLite, we just need to ensure the model reflects this

    # Create foreign key from entities to worlds
    with op.batch_alter_table('entities') as batch_op:
        batch_op.create_foreign_key('fk_entities_world_id', 'worlds', ['world_id'], ['id'])

    # Add series_id and order_index to manuscripts
    op.add_column('manuscripts', sa.Column('series_id', sa.String(), nullable=True))
    op.add_column('manuscripts', sa.Column('order_index', sa.Integer(), server_default='0', nullable=True))

    # Create foreign key from manuscripts to series
    with op.batch_alter_table('manuscripts') as batch_op:
        batch_op.create_foreign_key('fk_manuscripts_series_id', 'series', ['series_id'], ['id'])

    # Data migration: Create default "My Library" world and "Standalone" series
    # for any existing manuscripts
    bind = op.get_bind()

    # Check if there are any manuscripts
    result = bind.execute(sa.text("SELECT COUNT(*) FROM manuscripts"))
    count = result.scalar()

    if count > 0:
        # Create default world
        default_world_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        bind.execute(
            sa.text(
                "INSERT INTO worlds (id, name, description, settings, created_at, updated_at) "
                "VALUES (:id, :name, :description, :settings, :created_at, :updated_at)"
            ),
            {
                "id": default_world_id,
                "name": "My Library",
                "description": "Default world for standalone manuscripts",
                "settings": "{}",
                "created_at": now,
                "updated_at": now
            }
        )

        # Create default series
        default_series_id = str(uuid.uuid4())
        bind.execute(
            sa.text(
                "INSERT INTO series (id, world_id, name, description, order_index, created_at, updated_at) "
                "VALUES (:id, :world_id, :name, :description, :order_index, :created_at, :updated_at)"
            ),
            {
                "id": default_series_id,
                "world_id": default_world_id,
                "name": "Standalone",
                "description": "Standalone manuscripts not part of a series",
                "order_index": 0,
                "created_at": now,
                "updated_at": now
            }
        )

        # Update existing manuscripts to belong to the default series
        bind.execute(
            sa.text("UPDATE manuscripts SET series_id = :series_id WHERE series_id IS NULL"),
            {"series_id": default_series_id}
        )

        # Set scope to MANUSCRIPT for all existing entities (they're manuscript-scoped by default)
        bind.execute(
            sa.text("UPDATE entities SET scope = 'MANUSCRIPT' WHERE scope IS NULL OR scope = ''")
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign keys and columns from manuscripts
    with op.batch_alter_table('manuscripts') as batch_op:
        batch_op.drop_constraint('fk_manuscripts_series_id', type_='foreignkey')
    op.drop_column('manuscripts', 'order_index')
    op.drop_column('manuscripts', 'series_id')

    # Drop foreign key and columns from entities
    with op.batch_alter_table('entities') as batch_op:
        batch_op.drop_constraint('fk_entities_world_id', type_='foreignkey')
    op.drop_column('entities', 'scope')
    op.drop_column('entities', 'world_id')

    # Drop series and worlds tables
    op.drop_table('series')
    op.drop_table('worlds')
