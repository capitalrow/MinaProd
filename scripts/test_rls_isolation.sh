#!/bin/bash

# ==============================================================================
# ROW-LEVEL SECURITY ISOLATION TESTING SCRIPT
# ==============================================================================
# This script tests that RLS policies correctly enforce multi-tenant isolation.
# It creates two test users and verifies they can only see their own data.
#
# Usage:
#   ./scripts/test_rls_isolation.sh
#
# Requirements:
#   - Postgres running with RLS migration applied
#   - DATABASE_URL environment variable set
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database connection
DB_URL="${DATABASE_URL}"

if [ -z "$DB_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL not set${NC}"
    exit 1
fi

echo -e "${BLUE}==============================================================================

${NC}"
echo -e "${BLUE}ROW-LEVEL SECURITY ISOLATION TESTING${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# ----------------------------------------------------------------------------
# 1. Create test users
# ----------------------------------------------------------------------------
echo -e "${BLUE}📝 Step 1: Creating test users...${NC}"
psql "$DB_URL" <<'EOF'
-- Create test users if they don't exist
INSERT INTO users (username, email, password_hash, role, created_at)
VALUES 
    ('rls_test_user1', 'rls_test1@example.com', 'hash123', 'user', NOW()),
    ('rls_test_user2', 'rls_test2@example.com', 'hash456', 'user', NOW()),
    ('rls_test_admin', 'rls_admin@example.com', 'hash789', 'admin', NOW())
ON CONFLICT (email) DO NOTHING;

-- Get user IDs
SELECT id, username, role FROM users WHERE username LIKE 'rls_test_%';
EOF
echo -e "${GREEN}✅ Test users created${NC}"
echo ""

# Get user IDs
USER1_ID=$(psql "$DB_URL" -t -c "SELECT id FROM users WHERE username = 'rls_test_user1';" | xargs)
USER2_ID=$(psql "$DB_URL" -t -c "SELECT id FROM users WHERE username = 'rls_test_user2';" | xargs)
ADMIN_ID=$(psql "$DB_URL" -t -c "SELECT id FROM users WHERE username = 'rls_test_admin';" | xargs)

echo -e "User 1 ID: ${YELLOW}$USER1_ID${NC}"
echo -e "User 2 ID: ${YELLOW}$USER2_ID${NC}"
echo -e "Admin  ID: ${YELLOW}$ADMIN_ID${NC}"
echo ""

# ----------------------------------------------------------------------------
# 2. Create test sessions for each user
# ----------------------------------------------------------------------------
echo -e "${BLUE}📝 Step 2: Creating test sessions...${NC}"
psql "$DB_URL" <<EOF
-- User 1's session
INSERT INTO sessions (external_id, title, user_id, status, started_at)
VALUES ('rls_test_session_1', 'User 1 Session', $USER1_ID, 'active', NOW())
ON CONFLICT DO NOTHING;

-- User 2's session
INSERT INTO sessions (external_id, title, user_id, status, started_at)
VALUES ('rls_test_session_2', 'User 2 Session', $USER2_ID, 'active', NOW())
ON CONFLICT DO NOTHING;

-- Anonymous session (should be visible to all)
INSERT INTO sessions (external_id, title, user_id, status, started_at)
VALUES ('rls_test_session_anon', 'Anonymous Session', NULL, 'active', NOW())
ON CONFLICT DO NOTHING;

SELECT external_id, title, user_id FROM sessions WHERE external_id LIKE 'rls_test_%';
EOF
echo -e "${GREEN}✅ Test sessions created${NC}"
echo ""

# ----------------------------------------------------------------------------
# 3. Test User 1 isolation
# ----------------------------------------------------------------------------
echo -e "${BLUE}🔒 Step 3: Testing User 1 isolation...${NC}"
echo -e "User 1 should see:"
echo -e "  ✓ Their own session (rls_test_session_1)"
echo -e "  ✓ Anonymous session (rls_test_session_anon)"
echo -e "  ✗ User 2's session (rls_test_session_2) ${RED}[BLOCKED]${NC}"
echo ""

RESULT=$(psql "$DB_URL" -t <<EOF
BEGIN;
-- Set RLS context to User 1
SET LOCAL app.current_user_id = $USER1_ID;

-- Query sessions (RLS policies applied automatically)
SELECT external_id FROM sessions WHERE external_id LIKE 'rls_test_%' ORDER BY external_id;
COMMIT;
EOF
)

echo "User 1 sees:"
echo "$RESULT"
echo ""

# Verify isolation
if echo "$RESULT" | grep -q "rls_test_session_2"; then
    echo -e "${RED}❌ FAIL: User 1 can see User 2's session (RLS violation!)${NC}"
    exit 1
else
    echo -e "${GREEN}✅ PASS: User 1 cannot see User 2's session${NC}"
fi

if echo "$RESULT" | grep -q "rls_test_session_1"; then
    echo -e "${GREEN}✅ PASS: User 1 can see their own session${NC}"
else
    echo -e "${RED}❌ FAIL: User 1 cannot see their own session${NC}"
    exit 1
fi

if echo "$RESULT" | grep -q "rls_test_session_anon"; then
    echo -e "${GREEN}✅ PASS: User 1 can see anonymous session${NC}"
else
    echo -e "${RED}❌ FAIL: User 1 cannot see anonymous session${NC}"
    exit 1
fi
echo ""

# ----------------------------------------------------------------------------
# 4. Test User 2 isolation
# ----------------------------------------------------------------------------
echo -e "${BLUE}🔒 Step 4: Testing User 2 isolation...${NC}"
echo -e "User 2 should see:"
echo -e "  ✓ Their own session (rls_test_session_2)"
echo -e "  ✓ Anonymous session (rls_test_session_anon)"
echo -e "  ✗ User 1's session (rls_test_session_1) ${RED}[BLOCKED]${NC}"
echo ""

RESULT=$(psql "$DB_URL" -t <<EOF
BEGIN;
-- Set RLS context to User 2
SET LOCAL app.current_user_id = $USER2_ID;

-- Query sessions
SELECT external_id FROM sessions WHERE external_id LIKE 'rls_test_%' ORDER BY external_id;
COMMIT;
EOF
)

echo "User 2 sees:"
echo "$RESULT"
echo ""

# Verify isolation
if echo "$RESULT" | grep -q "rls_test_session_1"; then
    echo -e "${RED}❌ FAIL: User 2 can see User 1's session (RLS violation!)${NC}"
    exit 1
else
    echo -e "${GREEN}✅ PASS: User 2 cannot see User 1's session${NC}"
fi

if echo "$RESULT" | grep -q "rls_test_session_2"; then
    echo -e "${GREEN}✅ PASS: User 2 can see their own session${NC}"
else
    echo -e "${RED}❌ FAIL: User 2 cannot see their own session${NC}"
    exit 1
fi
echo ""

# ----------------------------------------------------------------------------
# 5. Test Admin bypass
# ----------------------------------------------------------------------------
echo -e "${BLUE}🔓 Step 5: Testing Admin bypass...${NC}"
echo -e "Admin should see ALL sessions (bypass RLS)"
echo ""

RESULT=$(psql "$DB_URL" -t <<EOF
BEGIN;
-- Set RLS context to Admin
SET LOCAL app.current_user_id = $ADMIN_ID;

-- Query sessions (admin bypasses RLS)
SELECT external_id FROM sessions WHERE external_id LIKE 'rls_test_%' ORDER BY external_id;
COMMIT;
EOF
)

echo "Admin sees:"
echo "$RESULT"
echo ""

# Count sessions
SESSION_COUNT=$(echo "$RESULT" | grep -c "rls_test_session" || echo "0")

if [ "$SESSION_COUNT" -eq 3 ]; then
    echo -e "${GREEN}✅ PASS: Admin can see all 3 test sessions (RLS bypass working)${NC}"
else
    echo -e "${RED}❌ FAIL: Admin sees only $SESSION_COUNT/3 sessions (RLS bypass broken)${NC}"
    exit 1
fi
echo ""

# ----------------------------------------------------------------------------
# 6. Cleanup test data
# ----------------------------------------------------------------------------
echo -e "${BLUE}🧹 Step 6: Cleaning up test data...${NC}"
psql "$DB_URL" <<EOF
-- Delete test sessions
DELETE FROM sessions WHERE external_id LIKE 'rls_test_%';

-- Delete test users
DELETE FROM users WHERE username LIKE 'rls_test_%';
EOF
echo -e "${GREEN}✅ Test data cleaned up${NC}"
echo ""

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo -e "${GREEN}==============================================================================

${NC}"
echo -e "${GREEN}✅ ALL RLS ISOLATION TESTS PASSED!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo -e "Verified:"
echo -e "  ${GREEN}✅${NC} User 1 sees only their own data + anonymous sessions"
echo -e "  ${GREEN}✅${NC} User 2 sees only their own data + anonymous sessions"
echo -e "  ${GREEN}✅${NC} Users cannot see each other's data"
echo -e "  ${GREEN}✅${NC} Admin users bypass RLS and see all data"
echo -e "  ${GREEN}✅${NC} Anonymous sessions visible to all users"
echo ""
echo -e "${GREEN}Row-Level Security is working correctly!${NC}"
echo ""

exit 0
