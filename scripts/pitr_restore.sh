#!/bin/bash
# Mina Point-in-Time Recovery (PITR) Script
# Restores database to a specific point in time using base backup + WAL archives

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-$HOME/.mina_wal_archive}"
RESTORE_DIR="/tmp/mina_pitr_restore"
LOG_FILE="/tmp/pitr_restore_$(date +%Y%m%d_%H%M%S).log"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Perform point-in-time recovery (PITR) of PostgreSQL database

OPTIONS:
    -b, --base-backup FILE    Base backup file (required)
    -t, --target-time TIME    Target recovery time (YYYY-MM-DD HH:MM:SS)
    -l, --latest              Recover to latest available point
    -c, --confirm             Skip confirmation prompts
    -h, --help                Show this help message

EXAMPLES:
    # Recover to specific time
    $0 --base-backup /path/to/backup.sql.gz --target-time "2025-10-01 14:30:00"

    # Recover to latest point
    $0 --base-backup /path/to/backup.sql.gz --latest

REQUIREMENTS:
    - Base backup created with pg_basebackup or pg_dump
    - WAL archive files in $WAL_ARCHIVE_DIR
    - PostgreSQL client tools (pg_restore, psql)

NOTES:
    - On managed services (Neon, RDS), use their built-in PITR features
    - This script is for self-hosted PostgreSQL only
    - Database will be stopped during restore

EOF
    exit 1
}

# Check if running on managed Postgres
check_managed_service() {
    if [[ "$DATABASE_URL" == *"neon.tech"* ]] || [[ "$DATABASE_URL" == *"neondb"* ]]; then
        log_warning "Detected Neon PostgreSQL (managed service)"
        log_info "Use Neon's built-in PITR instead:"
        echo ""
        echo "Via Neon Console:"
        echo "  1. Go to https://console.neon.tech"
        echo "  2. Select your project"
        echo "  3. Create a branch at specific point in time"
        echo ""
        echo "Via Neon CLI:"
        echo "  neon branches create --name pitr-restore --from-time '2025-10-01T14:30:00Z'"
        echo ""
        echo "Via Neon API:"
        echo "  curl -X POST https://console.neon.tech/api/v2/projects/{project_id}/branches \\"
        echo "    -H 'Authorization: Bearer \$NEON_API_KEY' \\"
        echo "    -d '{\"endpoints\":[{\"type\":\"read_write\"}],\"parent_timestamp\":\"2025-10-01T14:30:00Z\"}'"
        echo ""
        log_info "For more details: https://neon.tech/docs/introduction/point-in-time-restore"
        exit 1
    fi
}

# Parse arguments
BASE_BACKUP=""
TARGET_TIME=""
RECOVER_LATEST=false
SKIP_CONFIRM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--base-backup)
            BASE_BACKUP="$2"
            shift 2
            ;;
        -t|--target-time)
            TARGET_TIME="$2"
            shift 2
            ;;
        -l|--latest)
            RECOVER_LATEST=true
            shift
            ;;
        -c|--confirm)
            SKIP_CONFIRM=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate arguments
if [ -z "$BASE_BACKUP" ]; then
    log_error "Base backup file not specified"
    usage
fi

if [ "$RECOVER_LATEST" = false ] && [ -z "$TARGET_TIME" ]; then
    log_error "Either --target-time or --latest must be specified"
    usage
fi

if [ ! -f "$BASE_BACKUP" ]; then
    log_error "Base backup file not found: $BASE_BACKUP"
    exit 1
fi

echo "======================================"
echo "🔄 Mina Point-in-Time Recovery"
echo "======================================"
echo ""

check_managed_service

log_info "Base backup: $BASE_BACKUP"
if [ "$RECOVER_LATEST" = true ]; then
    log_info "Recovery target: Latest available point"
else
    log_info "Recovery target: $TARGET_TIME"
fi
log_info "WAL archive directory: $WAL_ARCHIVE_DIR"
echo ""

# Confirmation
if [ "$SKIP_CONFIRM" = false ]; then
    log_warning "⚠️  WARNING: This will REPLACE the current database!"
    log_warning "⚠️  Ensure you have a recent backup before proceeding."
    echo ""
    read -p "Continue with PITR? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "PITR cancelled"
        exit 0
    fi
fi

# Create restore directory
mkdir -p "$RESTORE_DIR"
chmod 700 "$RESTORE_DIR"

# Extract base backup
log_info "Extracting base backup..."
if [[ "$BASE_BACKUP" == *.gz ]]; then
    gunzip -c "$BASE_BACKUP" > "$RESTORE_DIR/base_backup.sql"
else
    cp "$BASE_BACKUP" "$RESTORE_DIR/base_backup.sql"
fi
log_success "Base backup extracted"

# Create recovery.conf for PostgreSQL
log_info "Creating recovery configuration..."
cat > "$RESTORE_DIR/recovery.conf" << EOF
restore_command = 'gunzip -c $WAL_ARCHIVE_DIR/%f.gz > %p 2>/dev/null || gunzip -c $WAL_ARCHIVE_DIR/%f > %p 2>/dev/null || cp $WAL_ARCHIVE_DIR/%f %p'
EOF

if [ "$RECOVER_LATEST" = false ]; then
    echo "recovery_target_time = '$TARGET_TIME'" >> "$RESTORE_DIR/recovery.conf"
fi

echo "recovery_target_action = 'promote'" >> "$RESTORE_DIR/recovery.conf"
log_success "Recovery configuration created"

# Restore base backup
log_info "Restoring base backup to database..."
psql "$DATABASE_URL" < "$RESTORE_DIR/base_backup.sql" 2>&1 | tee -a "$LOG_FILE"
log_success "Base backup restored"

# Apply WAL files
log_info "Applying WAL archive files..."
log_warning "Note: PostgreSQL must be configured to use recovery.conf"
log_info "Copy $RESTORE_DIR/recovery.conf to PostgreSQL data directory"
log_info "Then restart PostgreSQL to begin recovery"

echo ""
log_success "PITR preparation complete!"
log_info "Next steps:"
echo "  1. Stop PostgreSQL"
echo "  2. Copy $RESTORE_DIR/recovery.conf to PostgreSQL data directory"
echo "  3. Start PostgreSQL (it will enter recovery mode)"
echo "  4. Wait for recovery to complete"
echo "  5. Verify database state"
echo ""
log_info "Recovery log: $LOG_FILE"
echo "======================================"
