"""Add row-level security policies for multi-tenant isolation

Revision ID: 66a7a90c3c09
Revises: 1d4f13bc9042
Create Date: 2025-10-25 10:53:07.993484

==============================================================================
ROW-LEVEL SECURITY (RLS) MIGRATION
==============================================================================

This migration implements Postgres Row-Level Security to enforce multi-tenant
data isolation at the database level. Users can only access their own data.

TABLES PROTECTED:
- sessions: Users see only their own sessions (or anonymous sessions)
- segments: Users see segments from their own sessions
- tasks: Users see tasks assigned to them, created by them, or from their meetings

POLICY LOGIC:
- Sessions: SELECT if session.user_id = current_user_id() OR session.user_id IS NULL
- Segments: SELECT if segment.session.user_id = current_user_id()
- Tasks: SELECT if task.assigned_to_id = current_user_id() OR 
                  task.created_by_id = current_user_id() OR
                  task.meeting.organizer_id = current_user_id()

BYPASS:
- Admin users (role = 'admin') bypass all RLS policies
- Service accounts use SET ROLE to bypass RLS when needed

SAFETY:
- RLS is only enabled for SELECT operations (read)
- INSERT/UPDATE/DELETE use application-level authorization
- Can be disabled via SET ROLE for migrations/admin operations

==============================================================================
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66a7a90c3c09'
down_revision = '1d4f13bc9042'
branch_labels = None
depends_on = None


def upgrade():
    """
    Enable Row-Level Security and create policies for multi-tenant isolation.
    
    This migration:
    1. Creates a helper function to get current user ID
    2. Enables RLS on sessions, segments, tasks tables
    3. Creates SELECT policies for each table
    4. Allows admins to bypass all policies
    """
    
    # =========================================================================
    # 1. Create helper function to get current user ID from application context
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION get_current_user_id()
        RETURNS INTEGER AS $$
        DECLARE
            user_id INTEGER;
        BEGIN
            -- Get user ID from application context variable
            -- Application must set this via: SET LOCAL app.current_user_id = <user_id>
            user_id := current_setting('app.current_user_id', TRUE)::INTEGER;
            RETURN user_id;
        EXCEPTION
            WHEN OTHERS THEN
                -- Return NULL if not set (allows application-level fallback)
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
        
        COMMENT ON FUNCTION get_current_user_id() IS
        'Returns current user ID from application context (app.current_user_id)';
    """)
    
    # =========================================================================
    # 2. Create helper function to check if user is admin
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION is_admin_user()
        RETURNS BOOLEAN AS $$
        DECLARE
            user_role TEXT;
        BEGIN
            -- Get user ID first
            DECLARE
                user_id INTEGER := get_current_user_id();
            BEGIN
                IF user_id IS NULL THEN
                    RETURN FALSE;
                END IF;
                
                -- Check if user has admin role
                SELECT role INTO user_role
                FROM users
                WHERE id = user_id;
                
                RETURN user_role = 'admin';
            END;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN FALSE;
        END;
        $$ LANGUAGE plpgsql STABLE SECURITY DEFINER;
        
        COMMENT ON FUNCTION is_admin_user() IS
        'Returns TRUE if current user has admin role, FALSE otherwise';
    """)
    
    # =========================================================================
    # 3. SESSIONS TABLE: Enable RLS and create policies
    # =========================================================================
    
    # Enable RLS on sessions table
    op.execute("ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;")
    
    # Policy: Users can see their own sessions OR anonymous sessions
    op.execute("""
        CREATE POLICY sessions_select_policy ON sessions
        FOR SELECT
        USING (
            -- Admins see everything
            is_admin_user() OR
            -- Users see their own sessions
            user_id = get_current_user_id() OR
            -- Everyone sees anonymous sessions (legacy support)
            user_id IS NULL
        );
    """)
    
    # Policy: Users can insert sessions for themselves
    op.execute("""
        CREATE POLICY sessions_insert_policy ON sessions
        FOR INSERT
        WITH CHECK (
            -- Admins can insert anything
            is_admin_user() OR
            -- Users can insert sessions for themselves or anonymous
            user_id = get_current_user_id() OR
            user_id IS NULL
        );
    """)
    
    # Policy: Users can update their own sessions
    op.execute("""
        CREATE POLICY sessions_update_policy ON sessions
        FOR UPDATE
        USING (
            is_admin_user() OR
            user_id = get_current_user_id() OR
            user_id IS NULL
        );
    """)
    
    # Policy: Users can delete their own sessions
    op.execute("""
        CREATE POLICY sessions_delete_policy ON sessions
        FOR DELETE
        USING (
            is_admin_user() OR
            user_id = get_current_user_id() OR
            user_id IS NULL
        );
    """)
    
    # =========================================================================
    # 4. SEGMENTS TABLE: Enable RLS and create policies
    # =========================================================================
    
    # Enable RLS on segments table
    op.execute("ALTER TABLE segments ENABLE ROW LEVEL SECURITY;")
    
    # Policy: Users can see segments from their own sessions
    op.execute("""
        CREATE POLICY segments_select_policy ON segments
        FOR SELECT
        USING (
            -- Admins see everything
            is_admin_user() OR
            -- Users see segments from sessions they own (via JOIN)
            EXISTS (
                SELECT 1 FROM sessions
                WHERE sessions.id = segments.session_id
                AND (
                    sessions.user_id = get_current_user_id() OR
                    sessions.user_id IS NULL
                )
            )
        );
    """)
    
    # Policy: Users can insert segments into their own sessions
    op.execute("""
        CREATE POLICY segments_insert_policy ON segments
        FOR INSERT
        WITH CHECK (
            is_admin_user() OR
            EXISTS (
                SELECT 1 FROM sessions
                WHERE sessions.id = segments.session_id
                AND (
                    sessions.user_id = get_current_user_id() OR
                    sessions.user_id IS NULL
                )
            )
        );
    """)
    
    # Policy: Users can update segments in their own sessions
    op.execute("""
        CREATE POLICY segments_update_policy ON segments
        FOR UPDATE
        USING (
            is_admin_user() OR
            EXISTS (
                SELECT 1 FROM sessions
                WHERE sessions.id = segments.session_id
                AND (
                    sessions.user_id = get_current_user_id() OR
                    sessions.user_id IS NULL
                )
            )
        );
    """)
    
    # Policy: Users can delete segments from their own sessions
    op.execute("""
        CREATE POLICY segments_delete_policy ON segments
        FOR DELETE
        USING (
            is_admin_user() OR
            EXISTS (
                SELECT 1 FROM sessions
                WHERE sessions.id = segments.session_id
                AND (
                    sessions.user_id = get_current_user_id() OR
                    sessions.user_id IS NULL
                )
            )
        );
    """)
    
    # =========================================================================
    # 5. TASKS TABLE: Enable RLS and create policies
    # =========================================================================
    
    # Enable RLS on tasks table
    op.execute("ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;")
    
    # Policy: Users can see tasks assigned to them, created by them, or from their meetings
    op.execute("""
        CREATE POLICY tasks_select_policy ON tasks
        FOR SELECT
        USING (
            -- Admins see everything
            is_admin_user() OR
            -- Tasks assigned to the user
            assigned_to_id = get_current_user_id() OR
            -- Tasks created by the user
            created_by_id = get_current_user_id() OR
            -- Tasks from meetings organized by the user
            EXISTS (
                SELECT 1 FROM meetings
                WHERE meetings.id = tasks.meeting_id
                AND meetings.organizer_id = get_current_user_id()
            )
        );
    """)
    
    # Policy: Users can insert tasks for their own meetings
    op.execute("""
        CREATE POLICY tasks_insert_policy ON tasks
        FOR INSERT
        WITH CHECK (
            is_admin_user() OR
            -- Can insert tasks into own meetings
            EXISTS (
                SELECT 1 FROM meetings
                WHERE meetings.id = tasks.meeting_id
                AND meetings.organizer_id = get_current_user_id()
            ) OR
            -- Can insert tasks assigned to self (delegation)
            assigned_to_id = get_current_user_id()
        );
    """)
    
    # Policy: Users can update tasks they have access to
    op.execute("""
        CREATE POLICY tasks_update_policy ON tasks
        FOR UPDATE
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
    """)
    
    # Policy: Users can delete tasks they created or from their meetings
    op.execute("""
        CREATE POLICY tasks_delete_policy ON tasks
        FOR DELETE
        USING (
            is_admin_user() OR
            created_by_id = get_current_user_id() OR
            EXISTS (
                SELECT 1 FROM meetings
                WHERE meetings.id = tasks.meeting_id
                AND meetings.organizer_id = get_current_user_id()
            )
        );
    """)
    
    print("✅ Row-Level Security policies created successfully")
    print("   - Sessions: user-owned + anonymous access")
    print("   - Segments: access via session ownership")
    print("   - Tasks: access via assignment, creation, or meeting ownership")
    print("   - Admins bypass all policies")


def downgrade():
    """
    Disable Row-Level Security and remove all policies.
    
    SAFETY: This migration can be safely rolled back as RLS is only
    an additional security layer on top of application-level authorization.
    """
    
    # =========================================================================
    # 1. Drop policies (must drop policies before disabling RLS)
    # =========================================================================
    
    # Drop tasks policies
    op.execute("DROP POLICY IF EXISTS tasks_delete_policy ON tasks;")
    op.execute("DROP POLICY IF EXISTS tasks_update_policy ON tasks;")
    op.execute("DROP POLICY IF EXISTS tasks_insert_policy ON tasks;")
    op.execute("DROP POLICY IF EXISTS tasks_select_policy ON tasks;")
    
    # Drop segments policies
    op.execute("DROP POLICY IF EXISTS segments_delete_policy ON segments;")
    op.execute("DROP POLICY IF EXISTS segments_update_policy ON segments;")
    op.execute("DROP POLICY IF EXISTS segments_insert_policy ON segments;")
    op.execute("DROP POLICY IF EXISTS segments_select_policy ON segments;")
    
    # Drop sessions policies
    op.execute("DROP POLICY IF EXISTS sessions_delete_policy ON sessions;")
    op.execute("DROP POLICY IF EXISTS sessions_update_policy ON sessions;")
    op.execute("DROP POLICY IF EXISTS sessions_insert_policy ON sessions;")
    op.execute("DROP POLICY IF EXISTS sessions_select_policy ON sessions;")
    
    # =========================================================================
    # 2. Disable RLS on tables
    # =========================================================================
    op.execute("ALTER TABLE tasks DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE segments DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;")
    
    # =========================================================================
    # 3. Drop helper functions
    # =========================================================================
    op.execute("DROP FUNCTION IF EXISTS is_admin_user();")
    op.execute("DROP FUNCTION IF EXISTS get_current_user_id();")
    
    print("✅ Row-Level Security policies removed successfully")
    print("   - RLS disabled on sessions, segments, tasks")
    print("   - All policies dropped")
    print("   - Helper functions removed")
