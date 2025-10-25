# Row-Level Security (RLS) Guide

## Overview

Mina implements Postgres Row-Level Security (RLS) to enforce multi-tenant data isolation at the database level. This provides defense-in-depth security beyond application-level authorization.

**Key Principle**: Users can only access their own data, even if application-level authorization is bypassed.

## Protected Tables

RLS is enabled on the following tables:

| Table    | Access Control                                                                 |
|----------|-------------------------------------------------------------------------------|
| sessions | User owns session (user_id) OR session is anonymous (user_id IS NULL)        |
| segments | User owns the parent session                                                  |
| tasks    | User is assigned, created the task, OR organizes the parent meeting          |

## How It Works

### 1. Application Sets Current User Context

Before each request, the application sets the current user ID in a Postgres session variable:

```python
# In middleware or before_request hook
from flask import g
from sqlalchemy import text

@app.before_request
def set_postgres_user_context():
    if current_user.is_authenticated:
        # Set current user ID in Postgres context
        db.session.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": current_user.id}
        )
```

### 2. Postgres Enforces Policies Automatically

When queries execute, Postgres automatically adds `WHERE` clauses based on RLS policies:

```sql
-- Application query:
SELECT * FROM sessions;

-- Postgres executes (with RLS):
SELECT * FROM sessions
WHERE user_id = get_current_user_id() OR user_id IS NULL;
```

### 3. Admins Bypass All Policies

Users with `role = 'admin'` bypass all RLS policies and see all data:

```sql
-- Admin query:
SELECT * FROM sessions;

-- Postgres executes (is_admin_user() = TRUE):
SELECT * FROM sessions;  -- No WHERE clause added
```

## Policy Details

### Sessions Table

```sql
-- SELECT: See own sessions + anonymous sessions
CREATE POLICY sessions_select_policy ON sessions FOR SELECT
USING (
    is_admin_user() OR
    user_id = get_current_user_id() OR
    user_id IS NULL
);

-- INSERT: Create sessions for self or anonymous
CREATE POLICY sessions_insert_policy ON sessions FOR INSERT
WITH CHECK (
    is_admin_user() OR
    user_id = get_current_user_id() OR
    user_id IS NULL
);

-- UPDATE/DELETE: Modify own sessions
CREATE POLICY sessions_update_policy ON sessions FOR UPDATE
USING (
    is_admin_user() OR
    user_id = get_current_user_id() OR
    user_id IS NULL
);
```

### Segments Table

```sql
-- SELECT: See segments from own sessions (via JOIN)
CREATE POLICY segments_select_policy ON segments FOR SELECT
USING (
    is_admin_user() OR
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = segments.session_id
        AND (sessions.user_id = get_current_user_id() OR sessions.user_id IS NULL)
    )
);
```

### Tasks Table

```sql
-- SELECT: See tasks you're involved with
CREATE POLICY tasks_select_policy ON tasks FOR SELECT
USING (
    is_admin_user() OR
    assigned_to_id = get_current_user_id() OR
    created_by_id = get_current_user_id() OR
    EXISTS (
        SELECT 1 FROM meetings
        WHERE meetings.id = tasks.meeting_id
        AND meetings.organizer_id = get_current_user_id()
    )
);
```

## Implementation Guide

### Step 1: Apply Migration

```bash
# Apply RLS migration
flask db upgrade

# Verify RLS is enabled
psql $DATABASE_URL -c "\d+ sessions" | grep "row security"
```

### Step 2: Add Middleware

Create `middleware/rls_context.py`:

```python
"""
Row-Level Security Context Middleware

Sets current user ID in Postgres session context before each request.
"""
from flask import g
from flask_login import current_user
from sqlalchemy import text
from models import db

def set_rls_context(app):
    """
    Enable RLS context setting for all requests.
    
    This middleware executes before every request and sets the
    app.current_user_id Postgres variable based on the authenticated user.
    """
    @app.before_request
    def set_postgres_rls_context():
        if current_user.is_authenticated:
            try:
                # Set current user ID for RLS policies
                db.session.execute(
                    text("SET LOCAL app.current_user_id = :user_id"),
                    {"user_id": current_user.id}
                )
            except Exception as e:
                app.logger.warning(f"Failed to set RLS context: {e}")
        else:
            # For unauthenticated requests, unset the variable
            try:
                db.session.execute(text("SET LOCAL app.current_user_id = NULL"))
            except Exception:
                pass
```

Register in `app.py`:

```python
from middleware.rls_context import set_rls_context

def create_app():
    # ... app initialization ...
    
    # Enable RLS context middleware
    set_rls_context(app)
    
    # ... rest of app setup ...
```

### Step 3: Test Multi-User Isolation

Create test script:

```bash
./scripts/test_rls_isolation.sh
```

## Testing RLS Policies

### Manual Testing via psql

```sql
-- Simulate user ID 1
SET app.current_user_id = 1;

-- Should only see user 1's sessions
SELECT id, title, user_id FROM sessions;

-- Switch to user ID 2
SET app.current_user_id = 2;

-- Should only see user 2's sessions
SELECT id, title, user_id FROM sessions;

-- Verify isolation (should return 0 rows)
SET app.current_user_id = 1;
SELECT * FROM sessions WHERE user_id = 2;  -- Returns nothing!
```

### Automated Testing

```python
# tests/test_rls_isolation.py
import pytest
from models import Session, Segment, Task, db
from sqlalchemy import text

def test_session_isolation(client, user1, user2):
    """Test that users can only see their own sessions."""
    
    # User 1 creates a session
    with client.session_transaction() as sess:
        sess['user_id'] = user1.id
    
    # Set RLS context
    db.session.execute(
        text("SET LOCAL app.current_user_id = :user_id"),
        {"user_id": user1.id}
    )
    
    # User 1 should see only their sessions
    sessions = Session.query.all()
    assert all(s.user_id == user1.id or s.user_id is None for s in sessions)
    
    # User 2 should not see user 1's sessions
    db.session.execute(
        text("SET LOCAL app.current_user_id = :user_id"),
        {"user_id": user2.id}
    )
    
    sessions = Session.query.all()
    assert all(s.user_id != user1.id for s in sessions if s.user_id is not None)
```

## Admin Bypass

Admins (role = 'admin') bypass all RLS policies:

```sql
-- Admin user (role='admin')
SET app.current_user_id = 999;  -- Admin user ID

-- Sees ALL sessions (bypass)
SELECT COUNT(*) FROM sessions;  -- Returns total count
```

## Performance Considerations

### Index Optimization

RLS policies use `user_id` extensively, ensure proper indexing:

```sql
-- Already indexed in schema
CREATE INDEX ix_sessions_user_id ON sessions(user_id);
CREATE INDEX ix_tasks_assigned_to ON tasks(assigned_to_id);
CREATE INDEX ix_tasks_created_by ON tasks(created_by_id);
```

### Query Performance

RLS adds `WHERE` clauses automatically:

```sql
-- Before RLS:
EXPLAIN ANALYZE SELECT * FROM sessions;
-- Seq Scan: 100ms

-- After RLS:
EXPLAIN ANALYZE SELECT * FROM sessions;
-- Index Scan using ix_sessions_user_id: 5ms
```

**Result**: RLS can actually *improve* performance by reducing result sets!

## Troubleshooting

### Problem: Users see no data

**Cause**: `app.current_user_id` not set in Postgres context

**Solution**:
```sql
-- Check current setting
SHOW app.current_user_id;

-- If empty, middleware not running
-- Verify middleware is registered in app.py
```

### Problem: Users see other users' data

**Cause**: RLS not enabled on table

**Solution**:
```sql
-- Check if RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Enable RLS if missing
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
```

### Problem: Migrations fail with permission errors

**Cause**: Migration user doesn't have BYPASSRLS privilege

**Solution**:
```sql
-- Grant BYPASSRLS to migration user
ALTER USER migration_user WITH BYPASSRLS;

-- Or disable RLS temporarily
SET ROLE postgres;  -- Superuser role
-- Run migration
```

## Disabling RLS (Emergency)

If RLS causes production issues, it can be temporarily disabled:

```sql
-- Disable RLS on specific table (as superuser)
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;

-- Or bypass for specific session
SET ROLE postgres;  -- Superuser bypasses RLS
-- Run query
RESET ROLE;
```

**Warning**: Only disable RLS in emergencies. It's a critical security layer.

## See Also

- [Postgres RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Migration Guide](./MIGRATIONS_GUIDE.md) - How to create RLS migrations
- [Security Best Practices](../SECURITY.md) - Overall security guidelines
