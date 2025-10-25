#!/bin/bash

# ==============================================================================
# LOCAL MIGRATION TESTING SCRIPT
# ==============================================================================
# This script mimics the CI pipeline for testing migrations locally.
# Run this before pushing to ensure migrations will pass CI.
#
# Usage:
#   ./scripts/test_migrations.sh
#
# Requirements:
#   - Postgres installed and running
#   - Flask app environment configured
#   - Python virtual environment activated
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test database configuration
TEST_DB_NAME="test_mina_migrations_$(date +%s)"
TEST_DB_USER="${POSTGRES_USER:-postgres}"
TEST_DB_HOST="${POSTGRES_HOST:-localhost}"
TEST_DB_PORT="${POSTGRES_PORT:-5432}"
TEST_DB_URL="postgresql://${TEST_DB_USER}@${TEST_DB_HOST}:${TEST_DB_PORT}/${TEST_DB_NAME}"

# Store original DATABASE_URL
ORIGINAL_DATABASE_URL="${DATABASE_URL}"

echo -e "${BLUE}==============================================================================

${NC}"
echo -e "${BLUE}MIGRATION TESTING SCRIPT${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""
echo -e "Test database: ${YELLOW}${TEST_DB_NAME}${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up test database...${NC}"
    dropdb --if-exists "$TEST_DB_NAME" 2>/dev/null || true
    export DATABASE_URL="$ORIGINAL_DATABASE_URL"
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

trap cleanup EXIT

# ----------------------------------------------------------------------------
# 1. Create test database
# ----------------------------------------------------------------------------
echo -e "${BLUE}📦 Step 1: Creating test database...${NC}"
createdb "$TEST_DB_NAME"
export DATABASE_URL="$TEST_DB_URL"
echo -e "${GREEN}✅ Test database created${NC}"
echo ""

# ----------------------------------------------------------------------------
# 2. Apply all migrations (matches test-migration-up)
# ----------------------------------------------------------------------------
echo -e "${BLUE}🔄 Step 2: Applying all migrations...${NC}"
export FLASK_APP=main.py
export SECRET_KEY=test_secret_key_for_local_testing
flask db upgrade
echo -e "${GREEN}✅ All migrations applied${NC}"
echo ""

# ----------------------------------------------------------------------------
# 3. Rollback one migration (matches test-migration-rollback)
# ----------------------------------------------------------------------------
echo -e "${BLUE}⏪ Step 3: Rolling back latest migration...${NC}"
flask db downgrade -1
echo -e "${GREEN}✅ Rollback successful${NC}"
echo ""

# ----------------------------------------------------------------------------
# 4. Re-apply latest migration (matches test-migration-rollback)
# ----------------------------------------------------------------------------
echo -e "${BLUE}🔄 Step 4: Re-applying latest migration...${NC}"
flask db upgrade
echo -e "${GREEN}✅ Re-application successful${NC}"
echo ""

# ----------------------------------------------------------------------------
# 5. Full rollback test (matches test-migration-rollback)
# ----------------------------------------------------------------------------
echo -e "${BLUE}⏪ Step 5: Rolling back ALL migrations...${NC}"
flask db downgrade base
echo -e "${GREEN}✅ Full rollback successful${NC}"
echo ""

# ----------------------------------------------------------------------------
# 6. Full upgrade test (matches test-migration-rollback)
# ----------------------------------------------------------------------------
echo -e "${BLUE}🔄 Step 6: Re-applying all migrations from base...${NC}"
flask db upgrade
echo -e "${GREEN}✅ Full upgrade from base successful${NC}"
echo ""

# ----------------------------------------------------------------------------
# 7. Test idempotency (matches test-migration-idempotency)
# ----------------------------------------------------------------------------
echo -e "${BLUE}🔄 Step 7: Testing idempotency (re-application should be no-op)...${NC}"
flask db upgrade
echo -e "${GREEN}✅ Idempotent - no errors on re-application${NC}"
echo ""

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo -e "${GREEN}==============================================================================

${NC}"
echo -e "${GREEN}✅ ALL MIGRATION TESTS PASSED!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo -e "Tested (matching CI pipeline):"
echo -e "  ${GREEN}✅${NC} Migration application (up)"
echo -e "  ${GREEN}✅${NC} Migration rollback (down)"
echo -e "  ${GREEN}✅${NC} Latest migration re-apply"
echo -e "  ${GREEN}✅${NC} Full rollback to base"
echo -e "  ${GREEN}✅${NC} Full upgrade from base"
echo -e "  ${GREEN}✅${NC} Idempotency (re-application)"
echo ""
echo -e "${GREEN}Your migrations are ready to push!${NC}"
echo -e "${BLUE}The CI pipeline will run the same tests automatically.${NC}"
echo ""

exit 0
