# Database Migrations - Quick Start

## Daily Developer Commands

```bash
# 1. After modifying models, create migration
python manage_migrations.py migrate "Add user email verification"

# 2. Apply migration locally
python manage_migrations.py upgrade

# 3. Test your changes
gunicorn --bind 0.0.0.0:5000 main:app

# 4. Commit migration file
git add migrations/versions/*.py
git commit -m "feat: add email verification to users"
```

## Common Commands

```bash
# Check current version
python manage_migrations.py current

# Apply all pending migrations
python manage_migrations.py upgrade

# Rollback last migration
python manage_migrations.py downgrade

# View migration files
ls migrations/versions/
```

## Current State

- **Version**: `6f9f2dd343f5`
- **Tables**: 15 production tables
- **Location**: `migrations/`
- **Documentation**: `docs/database/MIGRATION-WORKFLOW.md`

## Rules

✅ **DO:**
- Test migrations on staging first
- Review auto-generated migrations before applying
- Backup production database before migrating
- Write descriptive migration messages

❌ **DON'T:**
- Modify already-applied migrations
- Apply untested migrations to production
- Skip migrations or apply out of order
- Ignore data loss warnings

## Need Help?

See full documentation: `docs/database/MIGRATION-WORKFLOW.md`
