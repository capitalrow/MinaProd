# Database Migration Workflow
**Mina - Production Database Management with Flask-Migrate (Alembic)**

## Overview

Mina uses **Flask-Migrate** (Alembic wrapper) for safe, versioned database schema changes. This document provides complete migration workflows for development and production environments.

**Current Migration State:**
- **Version**: `6f9f2dd343f5` (Initial clean database schema)
- **Tables**: 15 production tables (users, workspaces, meetings, sessions, segments, analytics, tasks, etc.)
- **Migration Directory**: `migrations/`
- **Management Script**: `manage_migrations.py`

---

## Quick Reference

```bash
# Check current migration version
python manage_migrations.py current

# Apply all pending migrations
python manage_migrations.py upgrade

# Create new migration after model changes
python manage_migrations.py migrate "Add user profile fields"

# Rollback last migration
python manage_migrations.py downgrade

# View migration history
ls migrations/versions/
```

---

## Migration Commands

### 1. Check Current State

```bash
# View current migration version
python manage_migrations.py current

# Or query database directly
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```

**Expected Output:**
```
version_num
6f9f2dd343f5
```

### 2. Create New Migration

When you modify models (add/remove fields, change types, add tables):

```bash
python manage_migrations.py migrate "Descriptive message about changes"
```

**Example:**
```bash
python manage_migrations.py migrate "Add email_verified_at to users table"
```

**What Happens:**
1. Flask-Migrate compares current models to database schema
2. Generates migration file in `migrations/versions/`
3. File contains `upgrade()` and `downgrade()` functions
4. Review the generated migration before applying

**⚠️ ALWAYS REVIEW GENERATED MIGRATIONS** - Auto-generated migrations may:
- Miss data migrations (only schema changes)
- Generate incorrect FK constraints for circular dependencies
- Need custom data transformations

### 3. Apply Migrations

```bash
# Apply all pending migrations
python manage_migrations.py upgrade

# Or apply specific version
python manage_migrations.py upgrade 6f9f2dd343f5
```

**Production Checklist:**
- [ ] Test migration on staging database first
- [ ] Backup production database before migrating
- [ ] Check migration for destructive operations (DROP, ALTER)
- [ ] Plan rollback strategy
- [ ] Schedule during low-traffic window
- [ ] Monitor application after deployment

### 4. Rollback Migrations

```bash
# Rollback one migration
python manage_migrations.py downgrade

# Rollback to specific version
python manage_migrations.py downgrade 6f9f2dd343f5

# Rollback all migrations (DANGEROUS)
python manage_migrations.py downgrade base
```

**⚠️ ROLLBACK RISKS:**
- Data loss if downgrade drops columns
- FK constraint violations
- Application errors if code expects new schema

---

## Development Workflow

### Typical Development Cycle

1. **Modify Models**
   ```python
   # models/user.py
   class User(Base):
       __tablename__ = 'users'
       id = sa.Column(sa.Integer, primary_key=True)
       email = sa.Column(sa.String(120), unique=True, nullable=False)
       # NEW: Add email verification timestamp
       email_verified_at = sa.Column(sa.DateTime, nullable=True)
   ```

2. **Create Migration**
   ```bash
   python manage_migrations.py migrate "Add email_verified_at to users"
   ```

3. **Review Generated Migration**
   ```bash
   cat migrations/versions/xxxx_add_email_verified_at_to_users.py
   ```

   Check for:
   - Correct column type
   - Proper nullable/default values
   - FK constraints
   - Index creation
   - Data migrations if needed

4. **Apply Migration Locally**
   ```bash
   python manage_migrations.py upgrade
   ```

5. **Test Application**
   - Start app: `gunicorn --bind 0.0.0.0:5000 main:app`
   - Verify new field works
   - Check database: `SELECT email_verified_at FROM users LIMIT 1;`

6. **Commit Migration**
   ```bash
   git add migrations/versions/xxxx_add_email_verified_at_to_users.py
   git commit -m "feat: add email verification timestamp to users"
   ```

---

## Production Deployment Workflow

### Pre-Deployment

1. **Backup Database**
   ```bash
   # PostgreSQL backup
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # Verify backup
   ls -lh backup_*.sql
   ```

2. **Test on Staging**
   ```bash
   # Apply to staging database
   DATABASE_URL=$STAGING_DATABASE_URL python manage_migrations.py upgrade
   
   # Run smoke tests
   pytest tests/integration/
   ```

3. **Review Migration Impact**
   - Check for `ALTER TABLE` operations (may lock table)
   - Estimate migration duration
   - Plan for downtime if needed
   - Notify users if maintenance window required

### Deployment

1. **Put App in Maintenance Mode** (if needed)
   ```bash
   # Set maintenance flag
   replit deployments maintenance enable
   ```

2. **Apply Migration**
   ```bash
   python manage_migrations.py upgrade
   ```

3. **Verify Migration**
   ```bash
   # Check alembic_version
   psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
   
   # Verify schema changes
   psql $DATABASE_URL -c "\d users"
   ```

4. **Deploy Application Code**
   ```bash
   git push production main
   ```

5. **Smoke Test**
   ```bash
   curl https://mina.replit.app/health
   curl https://mina.replit.app/api/sessions
   ```

6. **Exit Maintenance Mode**
   ```bash
   replit deployments maintenance disable
   ```

### Post-Deployment Monitoring

- Check Sentry for migration-related errors
- Monitor response times (migrations may affect performance)
- Watch database query performance
- Verify all features work with new schema

---

## Rollback Procedures

### When to Rollback

- Critical errors after deployment
- Data corruption detected
- Performance degradation
- Unexpected schema conflicts

### Rollback Steps

1. **Assess Situation**
   - Check Sentry errors
   - Check database state
   - Determine if forward fix is possible

2. **Rollback Application Code**
   ```bash
   git revert HEAD
   git push production main
   ```

3. **Rollback Database Migration**
   ```bash
   python manage_migrations.py downgrade
   ```

4. **Verify Rollback**
   ```bash
   psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
   pytest tests/integration/
   ```

5. **Monitor Application**
   - Check logs for errors
   - Verify critical flows work
   - Monitor user reports

---

## Advanced Scenarios

### Data Migrations

When renaming columns or transforming data:

```python
# migrations/versions/xxxx_rename_user_name_fields.py
def upgrade():
    # Add new columns
    op.add_column('users', sa.Column('first_name', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(64), nullable=True))
    
    # Migrate data (split full_name into first_name/last_name)
    op.execute("""
        UPDATE users 
        SET 
            first_name = split_part(full_name, ' ', 1),
            last_name = split_part(full_name, ' ', 2)
        WHERE full_name IS NOT NULL
    """)
    
    # Drop old column
    op.drop_column('users', 'full_name')

def downgrade():
    # Add old column back
    op.add_column('users', sa.Column('full_name', sa.String(128), nullable=True))
    
    # Reverse data migration
    op.execute("""
        UPDATE users 
        SET full_name = first_name || ' ' || last_name
        WHERE first_name IS NOT NULL OR last_name IS NOT NULL
    """)
    
    # Drop new columns
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
```

### Circular Foreign Key Dependencies

Example from initial migration (users ↔ workspaces):

```python
def upgrade():
    # 1. Create both tables WITHOUT foreign keys
    op.create_table('users', ...)
    op.create_table('workspaces', ...)
    
    # 2. Add foreign keys AFTER both tables exist
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_users_workspace_id', 'workspaces', ['workspace_id'], ['id'])
    
    with op.batch_alter_table('workspaces', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_workspaces_owner_id', 'users', ['owner_id'], ['id'])
```

### Zero-Downtime Migrations

For large tables or high-traffic applications:

```python
# Phase 1: Add new column (nullable)
def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))

# Deploy application code that writes to both old and new fields

# Phase 2: Backfill data
def upgrade():
    op.execute("""
        UPDATE users 
        SET email_verified = (email_verified_at IS NOT NULL)
        WHERE email_verified IS NULL
    """)

# Phase 3: Make column non-nullable (after backfill)
def upgrade():
    op.alter_column('users', 'email_verified', nullable=False)

# Phase 4: Drop old column
def upgrade():
    op.drop_column('users', 'email_verified_at')
```

---

## Best Practices

### ✅ DO

- **Write descriptive migration messages**: "Add user email verification" not "update users"
- **Review auto-generated migrations**: Check for correctness before applying
- **Test on staging first**: Never apply untested migrations to production
- **Backup before production migrations**: Always have a rollback plan
- **Use batch operations for large tables**: Minimize lock time
- **Add indexes concurrently**: Use `CONCURRENTLY` for PostgreSQL
- **Version control migrations**: Commit migration files to git
- **Document complex migrations**: Add comments explaining data transformations

### ❌ DON'T

- **Don't modify applied migrations**: Create new migration instead
- **Don't skip migrations**: Apply migrations in order
- **Don't use raw SQL without downgrade**: Always provide rollback logic
- **Don't ignore migration warnings**: Address data loss warnings
- **Don't deploy without testing**: Test migrations on staging
- **Don't rollback without planning**: Understand data loss implications
- **Don't commit sensitive data**: No passwords, tokens, or PII in migrations

---

## Troubleshooting

### Migration Fails: "relation already exists"

**Cause**: Database schema out of sync with migrations

**Solution**:
```bash
# Option 1: Stamp current version without running migration
python -c "from app import create_app; from flask_migrate import stamp; app = create_app(); \
    with app.app_context(): stamp(revision='6f9f2dd343f5')"

# Option 2: Drop and recreate database (DEVELOPMENT ONLY)
dropdb mina_dev && createdb mina_dev
python manage_migrations.py upgrade
```

### Migration Fails: "column does not exist"

**Cause**: Application code expects schema that doesn't exist yet

**Solution**:
1. Apply migration first: `python manage_migrations.py upgrade`
2. Then deploy application code
3. Use feature flags if necessary

### Migration Hangs on Large Table

**Cause**: Table lock during `ALTER TABLE` on busy table

**Solution**:
1. Schedule during low-traffic window
2. Use `SET lock_timeout = '5s'` in migration
3. Break into smaller migrations
4. Consider online schema change tools (pg_repack, gh-ost)

### Cannot Rollback: "data would be lost"

**Cause**: Downgrade would drop data

**Solution**:
1. Accept data loss (if acceptable)
2. Manually backup data before rollback
3. Modify downgrade() to preserve data in temporary table
4. Forward fix instead of rollback

---

## Migration Checklist

### Before Creating Migration
- [ ] Review model changes
- [ ] Consider backward compatibility
- [ ] Plan data migration if needed
- [ ] Check for circular dependencies

### After Creating Migration
- [ ] Review generated migration file
- [ ] Add data migration logic if needed
- [ ] Test upgrade on development database
- [ ] Test downgrade (rollback)
- [ ] Write tests for new schema
- [ ] Update API documentation if needed

### Before Production Deployment
- [ ] Backup production database
- [ ] Test migration on staging
- [ ] Review migration for destructive operations
- [ ] Estimate migration duration
- [ ] Plan maintenance window if needed
- [ ] Notify team/users if downtime expected
- [ ] Prepare rollback plan

### After Production Deployment
- [ ] Verify migration applied successfully
- [ ] Run smoke tests
- [ ] Check Sentry for errors
- [ ] Monitor application performance
- [ ] Verify data integrity
- [ ] Update team on successful deployment

---

## Emergency Contacts

**Database Issues:**
- Check Sentry: https://sentry.io/mina
- Check logs: `replit deployments logs`
- Runbook: `docs/ops/RUNBOOK.md`

**Escalation:**
1. Check Sentry error tracking
2. Review application logs
3. Check database connectivity
4. Consider rollback if critical

---

## Additional Resources

- **Flask-Migrate Docs**: https://flask-migrate.readthedocs.io/
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Database Reliability Engineering** (O'Reilly book)
- **Google SRE Book** (Chapter on safe migrations)

---

**Last Updated**: October 2025  
**Current Version**: `6f9f2dd343f5`  
**Maintainer**: Mina DevOps Team
