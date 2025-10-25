# Database Migrations Guide

## Overview
This project uses **Alembic** (via Flask-Migrate) for database schema versioning and migrations. All schema changes MUST go through migrations - never modify `db.create_all()` or run raw SQL against production.

## Quick Reference

### Check Current Migration Status
```bash
flask db current
```

### Create a New Migration
```bash
# Auto-generate migration from model changes
flask db migrate -m "Add audio_timestamps to Segment"

# Review the generated file in migrations/versions/
# Edit if needed, then apply it
flask db upgrade
```

### Rollback Migration
```bash
# Rollback one migration
flask db downgrade -1

# Rollback to specific version
flask db downgrade <revision_id>
```

### View Migration History
```bash
flask db history
```

## Step-by-Step Migration Workflow

### 1. Modify Models (models/*.py)
```python
# Example: Adding new columns to Segment model
class Segment(db.Model):
    # ... existing fields ...
    audio_start_ms = db.Column(db.Integer, nullable=True)
    audio_end_ms = db.Column(db.Integer, nullable=True)
    word_timestamps = db.Column(db.JSON, nullable=True)
```

### 2. Generate Migration
```bash
flask db migrate -m "Add audio timestamps to Segment model"
```

This creates a file like: `migrations/versions/abc123_add_audio_timestamps.py`

### 3. Review Generated Migration
**CRITICAL**: Always review the generated migration before applying:

```python
# migrations/versions/abc123_add_audio_timestamps.py
def upgrade():
    # Check these operations match your intent
    op.add_column('segment', sa.Column('audio_start_ms', sa.Integer(), nullable=True))
    op.add_column('segment', sa.Column('audio_end_ms', sa.Integer(), nullable=True))
    op.add_column('segment', sa.Column('word_timestamps', sa.JSON(), nullable=True))

def downgrade():
    # Verify rollback will work cleanly
    op.drop_column('segment', 'word_timestamps')
    op.drop_column('segment', 'audio_end_ms')
    op.drop_column('segment', 'audio_start_ms')
```

### 4. Test Migration in Staging First
```bash
# NEVER run migrations directly in production
# Always test in staging environment first

# Apply migration
flask db upgrade

# Verify tables updated correctly
psql $DATABASE_URL -c "\d segment"

# Test rollback works
flask db downgrade -1
flask db upgrade  # Re-apply
```

### 5. Deploy to Production
Once tested in staging:
1. Commit migration file to git
2. Deploy code with migrations
3. Run `flask db upgrade` on production database
4. Verify with smoke tests

## Safety Rules

### ✅ DO
- Always create migrations for schema changes
- Test migrations in staging before production
- Review auto-generated migrations manually
- Add indexes in separate migrations (not with table creation)
- Make migrations reversible when possible
- Add comments explaining complex migrations

### ❌ DON'T
- Never run `db.create_all()` in production
- Never skip testing rollback (`downgrade`)
- Never edit applied migrations (create new ones instead)
- Never delete migration files
- Never run migrations on production without staging test
- Never add breaking changes without data migration strategy

## Advanced: Data Migrations

When you need to transform existing data:

```python
# migrations/versions/xyz789_migrate_legacy_timestamps.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Add new columns first
    op.add_column('segment', sa.Column('audio_start_ms', sa.Integer(), nullable=True))
    
    # Migrate existing data using raw SQL or SQLAlchemy Core
    segment = table('segment',
        column('id', sa.Integer),
        column('timestamp', sa.String),
        column('audio_start_ms', sa.Integer)
    )
    
    # Example: Convert string timestamp to milliseconds
    op.execute(
        segment.update().values(
            audio_start_ms=sa.text("EXTRACT(EPOCH FROM timestamp::timestamp) * 1000")
        )
    )

def downgrade():
    op.drop_column('segment', 'audio_start_ms')
```

## Handling Migration Conflicts

### Multiple Developers
If two developers create migrations simultaneously:

```bash
# Pull latest code
git pull

# Check for conflicts
flask db heads  # Shows if multiple heads exist

# Merge migrations
flask db merge <revision1> <revision2> -m "Merge migrations"

# Test merged migration
flask db upgrade
```

### Production Hotfix
If production database is ahead of staging:

```bash
# Mark migration as applied without running it
flask db stamp <revision_id>

# Then normal workflow continues
```

## Rollback Strategy

### Emergency Rollback Plan
1. **Identify current version**: `flask db current`
2. **Review rollback script**: Check `downgrade()` function
3. **Backup database**: `pg_dump $DATABASE_URL > backup.sql`
4. **Execute rollback**: `flask db downgrade -1`
5. **Verify data integrity**: Run smoke tests
6. **Redeploy previous code version**

### Point-in-Time Recovery
If rollback fails:
```bash
# Restore from backup
psql $DATABASE_URL < backup.sql

# Or use PostgreSQL point-in-time recovery
# (requires WAL archiving configured)
```

## CI/CD Integration

### GitHub Actions Example
```yaml
# .github/workflows/test-migrations.yml
name: Test Database Migrations

on: [pull_request]

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Test Migration Up
        run: |
          export DATABASE_URL=postgresql://postgres:test@localhost/test
          flask db upgrade
      
      - name: Test Migration Down
        run: |
          flask db downgrade -1
      
      - name: Test Re-Apply
        run: |
          flask db upgrade
      
      - name: Block Merge if Rollback Fails
        if: failure()
        run: exit 1
```

## Troubleshooting

### "Target database is not up to date"
```bash
# Check current version
flask db current

# Check available migrations
flask db history

# Stamp to specific version if needed
flask db stamp head
```

### "Can't locate revision identified by 'xxx'"
Migration file missing or renamed. Restore from git:
```bash
git checkout migrations/versions/xxx_migration_name.py
```

### "Multiple head revisions present"
Merge conflicting migrations:
```bash
flask db heads
flask db merge <head1> <head2> -m "Merge migrations"
```

## Best Practices Summary

1. **One logical change per migration** - Don't combine table creation + data migration
2. **Test rollback immediately** - Run `downgrade` then `upgrade` to verify
3. **Use staging environment** - Never test migrations in production first
4. **Commit migrations with code** - Migration + code change in same PR
5. **Add migration to CI/CD** - Auto-test upgrades and downgrades
6. **Document complex migrations** - Add comments explaining data transformations
7. **Backup before migration** - Always have a rollback plan

## Wave 0 Checklist

- [x] Alembic installed and configured
- [x] Flask-Migrate integrated with app.py
- [x] migrations/ folder structure created
- [x] Initial migrations present and tested
- [ ] Staging environment configured
- [ ] CI/CD migration tests added
- [ ] Emergency rollback procedures documented
- [ ] Team trained on migration workflow

---

**Next Steps**: Review this guide, then proceed with Wave 1 database schema changes using the migration workflow above.
