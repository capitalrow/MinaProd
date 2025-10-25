# Database Migrations

This directory contains Alembic database migrations managed by Flask-Migrate.

## Overview

Migrations track all database schema changes over time, allowing safe deployment of schema updates to production.

## CI/CD Pipeline

**All migrations are automatically tested on every pull request.**

The GitHub Actions workflow (`.github/workflows/test-migrations.yml`) tests:

1. ✅ **Migration Application (Up)**: Migrations can be applied to an empty database
2. ✅ **Migration Rollback (Down)**: Migrations can be safely rolled back
3. ✅ **Idempotency**: Re-running migrations doesn't cause errors
4. ✅ **Data Integrity**: Migrations work with existing data

**If rollback fails, the PR cannot be merged.**

## Creating a New Migration

### Auto-generate from model changes:

```bash
# 1. Modify your models.py or models/*.py
# 2. Generate migration
flask db migrate -m "Add user_preferences table"

# 3. Review the generated migration in migrations/versions/
# 4. Test it locally (see "Testing Migrations Locally" below)
# 5. Commit and push - CI will auto-test
```

### Manual migration:

```bash
# Create empty migration file
flask db revision -m "Add custom index"

# Edit migrations/versions/XXXX_add_custom_index.py
# Write upgrade() and downgrade() functions
```

## Testing Migrations Locally

**Before pushing, test your migration locally:**

```bash
# Run the local test script
./scripts/test_migrations.sh
```

This script mimics the CI pipeline:
1. Creates a temporary test database
2. Applies all migrations
3. Rolls back latest migration
4. Re-applies latest migration
5. Tests full rollback to base
6. Cleans up test database

## Migration Best Practices

### 1. Always Write Downgrade

❌ **Bad** (no downgrade):
```python
def upgrade():
    op.create_table('users', ...)

def downgrade():
    pass  # ❌ Will fail CI!
```

✅ **Good** (reversible):
```python
def upgrade():
    op.create_table('users', ...)

def downgrade():
    op.drop_table('users')
```

### 2. Handle Existing Data

When adding a non-nullable column to a table with data:

```python
def upgrade():
    # Add column as nullable first
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    
    # Backfill data
    op.execute("UPDATE users SET email = username || '@example.com' WHERE email IS NULL")
    
    # Make non-nullable
    op.alter_column('users', 'email', nullable=False)

def downgrade():
    op.drop_column('users', 'email')
```

### 3. Test with Data

```bash
# Create test data before migration
psql $DATABASE_URL <<EOF
  INSERT INTO users (username) VALUES ('test_user');
EOF

# Apply migration
flask db upgrade

# Verify data still exists
psql $DATABASE_URL -c "SELECT * FROM users;"
```

### 4. Use Batching for Large Tables

For tables with millions of rows:

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Instead of ALTER TABLE (locks table)
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('large_table') as batch_op:
        batch_op.add_column(sa.Column('new_field', sa.String()))
```

### 5. Never Edit Old Migrations

**Once a migration is in `main` branch, never edit it.**

If you need to fix something:
1. Create a new migration that fixes the issue
2. Don't delete or modify the old one

This prevents production databases from getting out of sync.

## Rollback in Production

**CRITICAL: Never roll back production databases** (per deployment playbook).

If a migration causes problems in production:

1. **Option A: Forward Fix**
   ```bash
   # Create a new migration that fixes the issue
   flask db migrate -m "Fix incorrect index"
   flask db upgrade
   ```

2. **Option B: Traffic Reversal**
   ```bash
   # Revert application code (not database)
   git revert HEAD
   git push production main
   ```

3. **Option C: Restore from Backup** (last resort)
   ```bash
   # Restore yesterday's backup
   pg_restore -d $DATABASE_URL backups/mina_prod_2025-01-15.dump
   ```

See [Deployment Playbook](../docs/DEPLOYMENT_PLAYBOOK.md) for full rollback procedures.

## Migration Files

### Structure

```
migrations/
├── versions/           # Migration files (auto-generated)
│   ├── 001_initial.py
│   ├── 002_add_users.py
│   └── 003_add_sessions.py
├── alembic.ini        # Alembic configuration
├── env.py             # Alembic environment
└── README.md          # This file
```

### Naming Convention

Migrations are auto-named: `REVISION_description.py`

Example: `a1b2c3d4e5f6_add_user_preferences.py`

- `a1b2c3d4e5f6`: Unique revision ID
- `add_user_preferences`: Human-readable description

## Troubleshooting

### Problem: Migration fails in CI with "table already exists"

**Cause**: Migration is not idempotent (assumes clean database)

**Solution**: Use `IF NOT EXISTS` or check for table first:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'users' not in inspector.get_table_names():
        op.create_table('users', ...)
```

### Problem: Rollback fails with foreign key constraint

**Cause**: Trying to drop table that other tables reference

**Solution**: Drop foreign keys first, then tables:

```python
def downgrade():
    # Drop foreign keys first
    op.drop_constraint('fk_user_id', 'sessions', type_='foreignkey')
    
    # Then drop table
    op.drop_table('users')
```

### Problem: Migration works locally but fails in CI

**Cause**: Local database has stale state

**Solution**: Test on fresh database:

```bash
# Drop and recreate local database
dropdb mina_dev
createdb mina_dev

# Apply all migrations from scratch
flask db upgrade
```

## See Also

- [MIGRATIONS_GUIDE.md](../docs/MIGRATIONS_GUIDE.md) - Comprehensive migration guide
- [DEPLOYMENT_PLAYBOOK.md](../docs/DEPLOYMENT_PLAYBOOK.md) - Production deployment process
- [STAGING_ENVIRONMENT.md](../docs/STAGING_ENVIRONMENT.md) - Test migrations in staging first
