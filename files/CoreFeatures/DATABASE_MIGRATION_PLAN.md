# Maxwell/Codex IDE: Database Migration & Evolution Plan

**Last Updated**: 2025-12-15
**Database**: SQLite (Development/MVP) → PostgreSQL (Production)
**Migration Tool**: Alembic (Python) / Prisma (TypeScript)

---

## Table of Contents

1. [Overview](#overview)
2. [Database Evolution Strategy](#database-evolution-strategy)
3. [Phase-by-Phase Schema Evolution](#phase-by-phase-schema-evolution)
4. [Migration Scripts](#migration-scripts)
5. [Data Migration Patterns](#data-migration-patterns)
6. [Rollback Strategy](#rollback-strategy)
7. [Testing Migrations](#testing-migrations)
8. [Production Deployment](#production-deployment)

---

## Overview

### Migration Philosophy

- **Incremental**: Add features phase-by-phase without breaking existing data
- **Reversible**: Every migration has a rollback path
- **Tested**: All migrations tested in development before deployment
- **Zero-downtime**: (Future) Migrations run without app downtime
- **Version-controlled**: All migrations in Git with semantic versioning

### Tools

**Python (FastAPI) Backend:**
- **Alembic**: Database migration tool
- **SQLAlchemy**: ORM for database operations
- **Commands**:
  ```bash
  # Create migration
  alembic revision --autogenerate -m "description"

  # Run migrations
  alembic upgrade head

  # Rollback
  alembic downgrade -1
  ```

**TypeScript (if using Prisma):**
- **Prisma Migrate**: Schema evolution
- **Commands**:
  ```bash
  # Create migration
  npx prisma migrate dev --name description

  # Deploy to production
  npx prisma migrate deploy
  ```

---

## Database Evolution Strategy

### Semantic Versioning for Schema

```
v1.0.0 - Phase 1: Core manuscripts + versioning
v1.1.0 - Phase 2: Codex (entities + relationships)
v1.2.0 - Phase 2A: Timeline Orchestrator
v1.3.0 - Phase 3: AI generation (LangChain + Coach)
v1.4.0 - Phase 4: Structural analysis
v2.0.0 - Breaking change (SQLite → PostgreSQL)
```

### Migration Naming Convention

```
YYYYMMDD_HHMM_<phase>_<feature>_<action>

Examples:
20251215_1000_phase1_manuscripts_initial_schema
20251222_1400_phase1_versioning_add_snapshots
20260105_0900_phase2_codex_add_entities
20260112_1030_phase2a_timeline_add_events
```

---

## Phase-by-Phase Schema Evolution

### Phase 1: Foundation (Weeks 1-3)

#### Migration 1.0.0: Initial Schema
**File**: `migrations/20251215_1000_phase1_manuscripts_initial_schema.py`

```python
"""Initial schema - manuscripts and scenes

Revision ID: 001_initial
Revises:
Create Date: 2025-12-15 10:00:00
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Manuscripts table
    op.create_table(
        'manuscripts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('word_count', sa.Integer, default=0),
        sa.Column('lexical_state', sa.Text),
        sa.Column('genre', sa.String(100)),
        sa.Column('target_word_count', sa.Integer)
    )

    # Index for common queries
    op.create_index('idx_manuscripts_updated_at', 'manuscripts', ['updated_at'])

def downgrade():
    op.drop_index('idx_manuscripts_updated_at')
    op.drop_table('manuscripts')
```

#### Migration 1.0.1: Add Scenes
**File**: `migrations/20251218_1400_phase1_scenes_add_table.py`

```python
"""Add scenes table

Revision ID: 002_add_scenes
Revises: 001_initial
Create Date: 2025-12-18 14:00:00
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'scenes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('manuscript_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('position', sa.Integer, nullable=False),
        sa.Column('content', sa.Text),
        sa.Column('word_count', sa.Integer, default=0),
        sa.Column('pov_character_id', sa.String(36), nullable=True),  # FK added in Phase 2
        sa.Column('setting_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    op.create_index('idx_scenes_manuscript', 'scenes', ['manuscript_id', 'position'])

def downgrade():
    op.drop_index('idx_scenes_manuscript')
    op.drop_table('scenes')
```

#### Migration 1.0.2: Add Versioning
**File**: `migrations/20251222_1000_phase1_versioning_add_snapshots.py`

```python
"""Add version control tables

Revision ID: 003_add_versioning
Revises: 002_add_scenes
Create Date: 2025-12-22 10:00:00
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Snapshots table
    op.create_table(
        'snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('manuscript_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('git_commit_hash', sa.String(40), nullable=False),
        sa.Column('label', sa.String(255)),
        sa.Column('trigger_type', sa.String(50)),  # AUTO_SAVE, MANUAL, PRE_GENERATION
        sa.Column('word_count', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Variants table (multiverse)
    op.create_table(
        'variants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('scene_id', sa.String(36), sa.ForeignKey('scenes.id', ondelete='CASCADE')),
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('content', sa.Text),
        sa.Column('is_main', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Indexes
    op.create_index('idx_snapshots_manuscript_date', 'snapshots', ['manuscript_id', 'created_at'])
    op.create_index('idx_variants_scene', 'variants', ['scene_id'])

def downgrade():
    op.drop_index('idx_variants_scene')
    op.drop_index('idx_snapshots_manuscript_date')
    op.drop_table('variants')
    op.drop_table('snapshots')
```

---

### Phase 2: Knowledge Layer (Weeks 4-6)

#### Migration 1.1.0: Add Codex Tables
**File**: `migrations/20260105_0900_phase2_codex_add_entities.py`

```python
"""Add Codex entities and relationships

Revision ID: 004_add_codex
Revises: 003_add_versioning
Create Date: 2026-01-05 09:00:00
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Entities table
    op.create_table(
        'entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('manuscript_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('type', sa.String(50), nullable=False),  # CHARACTER, LOCATION, ITEM, LORE
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('aliases', sa.Text),  # JSON array
        sa.Column('attributes', sa.Text),  # JSON object
        sa.Column('appearance_history', sa.Text),  # JSON array
        sa.Column('image_seed', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    # Relationships table
    op.create_table(
        'relationships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source_entity_id', sa.String(36), sa.ForeignKey('entities.id', ondelete='CASCADE')),
        sa.Column('target_entity_id', sa.String(36), sa.ForeignKey('entities.id', ondelete='CASCADE')),
        sa.Column('relationship_type', sa.String(100)),
        sa.Column('strength', sa.Integer, default=1),
        sa.Column('context', sa.Text),  # JSON array
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Entity suggestions (NLP-detected)
    op.create_table(
        'entity_suggestions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('manuscript_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('scene_id', sa.String(36), sa.ForeignKey('scenes.id', ondelete='CASCADE')),
        sa.Column('suggested_name', sa.String(255)),
        sa.Column('suggested_type', sa.String(50)),
        sa.Column('confidence', sa.Float),
        sa.Column('status', sa.String(50), default='PENDING'),  # PENDING, APPROVED, REJECTED
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Indexes
    op.create_index('idx_entities_manuscript', 'entities', ['manuscript_id'])
    op.create_index('idx_entities_type', 'entities', ['type'])
    op.create_index('idx_relationships_source', 'relationships', ['source_entity_id'])
    op.create_index('idx_relationships_target', 'relationships', ['target_entity_id'])

    # Now add FK to scenes table
    op.add_column('scenes', sa.Column('pov_character_fk', sa.String(36)))
    op.create_foreign_key(
        'fk_scenes_pov_character',
        'scenes', 'entities',
        ['pov_character_fk'], ['id']
    )

def downgrade():
    op.drop_constraint('fk_scenes_pov_character', 'scenes')
    op.drop_column('scenes', 'pov_character_fk')

    op.drop_index('idx_relationships_target')
    op.drop_index('idx_relationships_source')
    op.drop_index('idx_entities_type')
    op.drop_index('idx_entities_manuscript')

    op.drop_table('entity_suggestions')
    op.drop_table('relationships')
    op.drop_table('entities')
```

---

### Phase 2A: Timeline Orchestrator (Weeks 7-8)

#### Migration 1.2.0: Add Timeline Tables
**File**: `migrations/20260112_1030_phase2a_timeline_add_tables.py`

```python
"""Add Timeline Orchestrator tables

Revision ID: 005_add_timeline
Revises: 004_add_codex
Create Date: 2026-01-12 10:30:00
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Locations table (shared with Codex)
    op.create_table(
        'locations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('travel_distance_km', sa.Float),
        sa.Column('known_travel_methods', sa.Text),  # JSON array
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    # Timeline events
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('story_date', sa.DateTime),
        sa.Column('position', sa.Float),  # 0-1 position in manuscript
        sa.Column('event_type', sa.String(100)),
        sa.Column('character_ids', sa.Text),  # JSON array
        sa.Column('location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('prerequisite_ids', sa.Text),  # JSON array
        sa.Column('narrative_importance', sa.Float, default=0.5),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    # Travel legs
    op.create_table(
        'travel_legs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('character_id', sa.String(36), nullable=False),
        sa.Column('from_location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('to_location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('depart_date', sa.DateTime, nullable=False),
        sa.Column('arrival_date', sa.DateTime),
        sa.Column('travel_method', sa.String(100)),
        sa.Column('estimated_days', sa.Integer),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    # Timeline issues
    op.create_table(
        'timeline_issues',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('issue_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('affected_event_ids', sa.Text),  # JSON array
        sa.Column('affected_character_id', sa.String(36)),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('suggestion', sa.Text, nullable=False),
        sa.Column('teaching_point', sa.Text),
        sa.Column('is_resolved', sa.Boolean, default=False),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    # Travel speed profiles
    op.create_table(
        'travel_speed_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE'), unique=True),
        sa.Column('walking', sa.Float, default=40),
        sa.Column('horse', sa.Float, default=80),
        sa.Column('carriage', sa.Float, default=60),
        sa.Column('sailing', sa.Float, default=150),
        sa.Column('flying', sa.Float, default=200),
        sa.Column('teleportation', sa.Float, default=999999),
        sa.Column('custom1_name', sa.String(100)),
        sa.Column('custom1_speed', sa.Float),
        sa.Column('custom2_name', sa.String(100)),
        sa.Column('custom2_speed', sa.Float),
        sa.Column('rules', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    # Location distances
    op.create_table(
        'location_distances',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('from_location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('to_location_id', sa.String(36), sa.ForeignKey('locations.id')),
        sa.Column('distance_km', sa.Float, nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Indexes
    op.create_index('idx_timeline_events_project', 'timeline_events', ['project_id'])
    op.create_index('idx_timeline_events_story_date', 'timeline_events', ['story_date'])
    op.create_index('idx_travel_legs_character', 'travel_legs', ['character_id'])
    op.create_index('idx_timeline_issues_severity', 'timeline_issues', ['severity', 'is_resolved'])

    # Unique constraint for location distances
    op.create_unique_constraint(
        'uq_location_distance',
        'location_distances',
        ['project_id', 'from_location_id', 'to_location_id']
    )

def downgrade():
    op.drop_constraint('uq_location_distance', 'location_distances')
    op.drop_index('idx_timeline_issues_severity')
    op.drop_index('idx_travel_legs_character')
    op.drop_index('idx_timeline_events_story_date')
    op.drop_index('idx_timeline_events_project')

    op.drop_table('location_distances')
    op.drop_table('travel_speed_profiles')
    op.drop_table('timeline_issues')
    op.drop_table('travel_legs')
    op.drop_table('timeline_events')
    op.drop_table('locations')
```

---

### Phase 3: Generative Layer (Weeks 9-14)

#### Migration 1.3.0: Add Coach Tables
**File**: `migrations/20260126_1000_phase3_coach_add_tables.py`

```python
"""Add Coach (learning agent) tables

Revision ID: 006_add_coach
Revises: 005_add_timeline
Create Date: 2026-01-26 10:00:00
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Coaching history
    op.create_table(
        'coaching_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('manuscript_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('scene_id', sa.String(36), sa.ForeignKey('scenes.id', ondelete='SET NULL')),
        sa.Column('feedback_category', sa.String(100)),
        sa.Column('severity', sa.String(50)),
        sa.Column('issue', sa.Text),
        sa.Column('suggestion', sa.Text),
        sa.Column('teaching_point', sa.Text),
        sa.Column('user_reaction', sa.String(50)),  # helpful, not_helpful, ignored
        sa.Column('user_applied', sa.Boolean),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Writing profile
    op.create_table(
        'writing_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('manuscript_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE'), unique=True),
        sa.Column('average_scene_length', sa.Integer),
        sa.Column('preferred_pacing', sa.String(50)),
        sa.Column('common_patterns', sa.Text),  # JSON array
        sa.Column('improvement_areas', sa.Text),  # JSON array
        sa.Column('learned_preferences', sa.Text),  # JSON object
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )

    # Feedback patterns
    op.create_table(
        'feedback_patterns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('manuscript_id', sa.String(36), sa.ForeignKey('manuscripts.id', ondelete='CASCADE')),
        sa.Column('pattern_type', sa.String(100)),
        sa.Column('occurrences', sa.Integer, default=1),
        sa.Column('first_detected', sa.DateTime),
        sa.Column('last_detected', sa.DateTime),
        sa.Column('resolution_rate', sa.Float)  # % of times user fixed this issue
    )

    # Indexes
    op.create_index('idx_coaching_manuscript', 'coaching_history', ['manuscript_id', 'created_at'])
    op.create_index('idx_feedback_patterns_type', 'feedback_patterns', ['pattern_type'])

def downgrade():
    op.drop_index('idx_feedback_patterns_type')
    op.drop_index('idx_coaching_manuscript')
    op.drop_table('feedback_patterns')
    op.drop_table('writing_profiles')
    op.drop_table('coaching_history')
```

---

## Data Migration Patterns

### Pattern 1: Adding a New Column with Default Value

```python
def upgrade():
    # Add column with default
    op.add_column('manuscripts', sa.Column('genre', sa.String(100), server_default='fiction'))

    # Remove server default after backfill (optional)
    op.alter_column('manuscripts', 'genre', server_default=None)

def downgrade():
    op.drop_column('manuscripts', 'genre')
```

### Pattern 2: Renaming a Column

```python
def upgrade():
    # SQLite doesn't support RENAME COLUMN, so we need to:
    # 1. Create new column
    # 2. Copy data
    # 3. Drop old column

    op.add_column('manuscripts', sa.Column('target_word_count', sa.Integer))
    op.execute('UPDATE manuscripts SET target_word_count = goal_word_count')
    op.drop_column('manuscripts', 'goal_word_count')

def downgrade():
    op.add_column('manuscripts', sa.Column('goal_word_count', sa.Integer))
    op.execute('UPDATE manuscripts SET goal_word_count = target_word_count')
    op.drop_column('manuscripts', 'target_word_count')
```

### Pattern 3: Migrating JSON Data Structure

```python
def upgrade():
    # Migrate entity attributes from flat structure to nested
    connection = op.get_bind()

    # Get all entities
    entities = connection.execute('SELECT id, attributes FROM entities').fetchall()

    for entity_id, old_attrs in entities:
        # Parse old JSON
        attrs = json.loads(old_attrs) if old_attrs else {}

        # Transform structure
        new_attrs = {
            'physical': {
                'age': attrs.get('age'),
                'height': attrs.get('height'),
                'description': attrs.get('description')
            },
            'background': {
                'house': attrs.get('house'),
                'title': attrs.get('title')
            },
            'skills': attrs.get('skills', [])
        }

        # Update entity
        connection.execute(
            'UPDATE entities SET attributes = ? WHERE id = ?',
            (json.dumps(new_attrs), entity_id)
        )

def downgrade():
    # Flatten structure back
    connection = op.get_bind()
    entities = connection.execute('SELECT id, attributes FROM entities').fetchall()

    for entity_id, new_attrs in entities:
        attrs = json.loads(new_attrs) if new_attrs else {}

        old_attrs = {
            'age': attrs.get('physical', {}).get('age'),
            'height': attrs.get('physical', {}).get('height'),
            'description': attrs.get('physical', {}).get('description'),
            'house': attrs.get('background', {}).get('house'),
            'title': attrs.get('background', {}).get('title'),
            'skills': attrs.get('skills', [])
        }

        connection.execute(
            'UPDATE entities SET attributes = ? WHERE id = ?',
            (json.dumps(old_attrs), entity_id)
        )
```

### Pattern 4: SQLite → PostgreSQL Migration

```python
# Separate migration for production deployment

def upgrade_to_postgres():
    # 1. Export SQLite data
    import sqlite3
    import psycopg2

    sqlite_conn = sqlite3.connect('maxwell.db')
    pg_conn = psycopg2.connect('postgresql://localhost/maxwell')

    # 2. For each table, migrate data
    tables = ['manuscripts', 'scenes', 'entities', 'timeline_events', ...]

    for table in tables:
        # Read from SQLite
        cursor = sqlite_conn.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Write to PostgreSQL
        pg_cursor = pg_conn.cursor()
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f'INSERT INTO {table} ({", ".join(columns)}) VALUES ({placeholders})'

        for row in rows:
            pg_cursor.execute(insert_sql, row)

        pg_conn.commit()

    sqlite_conn.close()
    pg_conn.close()
```

---

## Rollback Strategy

### Automatic Rollback (Development)

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 003_add_versioning

# Rollback all migrations
alembic downgrade base
```

### Manual Rollback (Production)

1. **Stop application**
2. **Backup database**
   ```bash
   cp maxwell.db maxwell_backup_20260112.db
   ```
3. **Run rollback**
   ```bash
   alembic downgrade -1
   ```
4. **Test database integrity**
5. **Restart application**
6. **Verify functionality**

### Emergency Restore

```bash
# If rollback fails, restore from backup
cp maxwell_backup_20260112.db maxwell.db

# Sync Alembic version table
alembic stamp 004_add_codex
```

---

## Testing Migrations

### Test Checklist

```python
# tests/migrations/test_timeline_migration.py

def test_timeline_migration_upgrade():
    """Test that timeline tables are created correctly"""
    # 1. Start with clean database
    engine = create_engine('sqlite:///:memory:')
    alembic_cfg = Config("alembic.ini")

    # 2. Run migration
    command.upgrade(alembic_cfg, "005_add_timeline")

    # 3. Verify tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert 'timeline_events' in tables
    assert 'locations' in tables
    assert 'travel_legs' in tables
    assert 'timeline_issues' in tables

    # 4. Verify columns
    columns = [col['name'] for col in inspector.get_columns('timeline_events')]
    assert 'story_date' in columns
    assert 'event_type' in columns

    # 5. Verify indexes
    indexes = inspector.get_indexes('timeline_events')
    assert any(idx['name'] == 'idx_timeline_events_project' for idx in indexes)

def test_timeline_migration_downgrade():
    """Test that downgrade removes tables"""
    engine = create_engine('sqlite:///:memory:')
    alembic_cfg = Config("alembic.ini")

    # Upgrade then downgrade
    command.upgrade(alembic_cfg, "005_add_timeline")
    command.downgrade(alembic_cfg, "004_add_codex")

    # Verify tables removed
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert 'timeline_events' not in tables
    assert 'locations' not in tables

def test_timeline_with_sample_data():
    """Test migration with actual data"""
    engine = create_engine('sqlite:///:memory:')

    # Create tables
    command.upgrade(alembic_cfg, "005_add_timeline")

    # Insert test data
    with engine.connect() as conn:
        conn.execute("""
            INSERT INTO timeline_events (id, project_id, name, story_date, event_type)
            VALUES ('evt-1', 'ms-1', 'Test Event', '2024-01-01', 'world_event')
        """)

        # Verify data
        result = conn.execute('SELECT name FROM timeline_events WHERE id = "evt-1"')
        assert result.fetchone()[0] == 'Test Event'
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All migrations tested in development
- [ ] Database backed up
- [ ] Migration scripts reviewed
- [ ] Rollback plan prepared
- [ ] Downtime window scheduled (if needed)
- [ ] Monitoring alerts configured

### Deployment Script

```bash
#!/bin/bash
# deploy_migration.sh

set -e  # Exit on error

echo "=== Maxwell Database Migration ==="
echo "Target version: $1"

# 1. Backup database
echo "Creating backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
cp maxwell.db "backups/maxwell_${timestamp}.db"

# 2. Check current version
echo "Current database version:"
alembic current

# 3. Run migration
echo "Running migration to $1..."
alembic upgrade "$1"

# 4. Verify migration
echo "New database version:"
alembic current

# 5. Run integrity check
echo "Running integrity check..."
python scripts/verify_database.py

echo "=== Migration complete ==="
```

### Verification Script

```python
# scripts/verify_database.py

import sqlite3

def verify_database():
    conn = sqlite3.connect('maxwell.db')
    cursor = conn.cursor()

    # Check table counts
    tables = ['manuscripts', 'scenes', 'entities', 'timeline_events']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'{table}: {count} rows')

    # Check for orphaned records
    cursor.execute('''
        SELECT COUNT(*) FROM scenes
        WHERE manuscript_id NOT IN (SELECT id FROM manuscripts)
    ''')
    orphans = cursor.fetchone()[0]
    if orphans > 0:
        print(f'WARNING: {orphans} orphaned scenes found')

    # Check timeline integrity
    cursor.execute('''
        SELECT COUNT(*) FROM timeline_events
        WHERE location_id NOT IN (SELECT id FROM locations)
        AND location_id IS NOT NULL
    ''')
    invalid_locations = cursor.fetchone()[0]
    if invalid_locations > 0:
        print(f'WARNING: {invalid_locations} events with invalid locations')

    conn.close()
    print('Database verification complete')

if __name__ == '__main__':
    verify_database()
```

---

## Migration Timeline

| Phase | Week | Migration | Tables Added | Breaking Changes |
|-------|------|-----------|--------------|------------------|
| 1 | 1 | 001_initial | manuscripts | No |
| 1 | 1 | 002_add_scenes | scenes | No |
| 1 | 2 | 003_add_versioning | snapshots, variants | No |
| 2 | 4 | 004_add_codex | entities, relationships, entity_suggestions | No |
| 2A | 7 | 005_add_timeline | timeline_events, locations, travel_legs, timeline_issues, travel_speed_profiles, location_distances | No |
| 3 | 12 | 006_add_coach | coaching_history, writing_profiles, feedback_patterns | No |
| Production | TBD | 007_sqlite_to_postgres | (all tables recreated in PostgreSQL) | **Yes** |

---

## Best Practices

1. **Always backup before migration**
2. **Test migrations in development first**
3. **Use transactions** (Alembic does this automatically)
4. **Write reversible migrations** (include downgrade())
5. **Document breaking changes**
6. **Version control all migration files**
7. **Never edit old migrations** (create new ones instead)
8. **Use descriptive migration names**
9. **Keep migrations small and focused**
10. **Monitor migration performance**

---

## Troubleshooting

### Migration Fails Mid-Way

```bash
# Check current state
alembic current

# If stuck, manually set version
alembic stamp 004_add_codex

# Try migration again
alembic upgrade head
```

### Duplicate Column Error

```bash
# Drop the column manually
sqlite3 maxwell.db
> ALTER TABLE manuscripts DROP COLUMN genre;

# Retry migration
alembic upgrade head
```

### Performance Issues

```sql
-- Check table sizes
SELECT name, COUNT(*) as rows
FROM sqlite_master, pragma_table_info(name)
WHERE type='table';

-- Add missing indexes
CREATE INDEX idx_scenes_manuscript ON scenes(manuscript_id);
```

---

**Status**: Ready for implementation
**Next Update**: After Phase 1 completion
**Maintained By**: Database Team
