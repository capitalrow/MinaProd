#!/bin/bash
# Mina WAL Archiving Setup
# Configures PostgreSQL for continuous archiving and point-in-time recovery (PITR)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-$HOME/.mina_wal_archive}"
WAL_RETENTION_DAYS=${WAL_RETENTION_DAYS:-7}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "======================================"
echo "🔄 Mina WAL Archiving Setup"
echo "======================================"
echo ""

# Check if running on managed Postgres (Neon)
if [[ "$DATABASE_URL" == *"neon.tech"* ]] || [[ "$DATABASE_URL" == *"neondb"* ]]; then
    log_warning "Detected Neon PostgreSQL (managed service)"
    log_warning "Neon handles WAL archiving and PITR automatically"
    log_info "WAL archiving is managed by Neon with built-in:"
    echo "  - Automatic WAL archiving"
    echo "  - Point-in-time recovery (PITR)"
    echo "  - 7-day history retention"
    echo "  - Branch-based recovery"
    echo ""
    log_info "To perform PITR on Neon:"
    echo "  1. Go to Neon Console: https://console.neon.tech"
    echo "  2. Select your project"
    echo "  3. Use 'Branches' feature to create point-in-time branches"
    echo "  4. Or use Neon API for programmatic PITR"
    echo ""
    log_info "For additional backup redundancy, use pg_dump backups:"
    echo "  ./scripts/backup_database.sh"
    echo ""
    log_success "No manual WAL archiving configuration needed for Neon!"
    exit 0
fi

# For self-hosted PostgreSQL
log_info "Configuring WAL archiving for self-hosted PostgreSQL..."

# Create WAL archive directory
mkdir -p "$WAL_ARCHIVE_DIR"
chmod 700 "$WAL_ARCHIVE_DIR"
log_success "Created WAL archive directory: $WAL_ARCHIVE_DIR"

# Create WAL archiving script
cat > "$SCRIPT_DIR/archive_wal.sh" << 'EOF'
#!/bin/bash
# WAL Archive Command Script
# Called by PostgreSQL to archive WAL segments

set -e

# Arguments from PostgreSQL
WAL_PATH="$1"
WAL_FILE="$2"

# Configuration
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-$HOME/.mina_wal_archive}"
LOG_FILE="/tmp/wal_archive.log"

# Archive the WAL file
cp "$WAL_PATH" "$WAL_ARCHIVE_DIR/$WAL_FILE"

# Optional: Compress WAL file
gzip "$WAL_ARCHIVE_DIR/$WAL_FILE" || true

# Optional: Encrypt WAL file
if [ -n "${GPG_BACKUP_PASSPHRASE:-}" ]; then
    echo "$GPG_BACKUP_PASSPHRASE" | gpg \
        --batch --yes --passphrase-fd 0 \
        --symmetric --cipher-algo AES256 \
        --output "$WAL_ARCHIVE_DIR/${WAL_FILE}.gz.gpg" \
        "$WAL_ARCHIVE_DIR/${WAL_FILE}.gz" 2>/dev/null
    rm -f "$WAL_ARCHIVE_DIR/${WAL_FILE}.gz"
fi

# Log the archive operation
echo "[$(date)] Archived WAL segment: $WAL_FILE" >> "$LOG_FILE"

exit 0
EOF

chmod +x "$SCRIPT_DIR/archive_wal.sh"
log_success "Created WAL archiving script: $SCRIPT_DIR/archive_wal.sh"

# Create WAL cleanup script
cat > "$SCRIPT_DIR/cleanup_wal_archive.sh" << 'EOF'
#!/bin/bash
# Clean up old WAL archive files

WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-$HOME/.mina_wal_archive}"
WAL_RETENTION_DAYS=${WAL_RETENTION_DAYS:-7}

# Delete WAL files older than retention period
find "$WAL_ARCHIVE_DIR" -type f -name "0*" -mtime +${WAL_RETENTION_DAYS} -delete

# Log cleanup
echo "[$(date)] Cleaned up WAL archives older than ${WAL_RETENTION_DAYS} days" >> /tmp/wal_archive.log
EOF

chmod +x "$SCRIPT_DIR/cleanup_wal_archive.sh"
log_success "Created WAL cleanup script: $SCRIPT_DIR/cleanup_wal_archive.sh"

# Display PostgreSQL configuration instructions
echo ""
log_info "PostgreSQL Configuration Required:"
echo ""
echo "Add the following to postgresql.conf:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "wal_level = replica"
echo "archive_mode = on"
echo "archive_command = '${SCRIPT_DIR}/archive_wal.sh %p %f'"
echo "archive_timeout = 300  # Force WAL switch every 5 minutes"
echo "max_wal_senders = 3"
echo "wal_keep_size = 1GB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Then restart PostgreSQL:"
echo "  sudo systemctl restart postgresql"
echo ""

log_warning "Note: Direct PostgreSQL configuration requires superuser access"
log_info "On managed services (Neon, RDS, etc.), use their built-in PITR features"

echo ""
log_success "WAL archiving setup complete!"
log_info "WAL archives will be stored in: $WAL_ARCHIVE_DIR"
log_info "Retention period: ${WAL_RETENTION_DAYS} days"
echo ""
echo "======================================"
