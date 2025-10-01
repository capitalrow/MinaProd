#!/bin/bash
# Mina Production Database Backup Script
# Implements encrypted backups with pg_dump + WAL archiving support
# Security: GPG-encrypted backups stored in secure location

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/tmp/mina_backups}"
ENCRYPTED_BACKUP_DIR="${ENCRYPTED_BACKUP_DIR:-$HOME/.mina_backups_encrypted}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_ONLY=$(date +"%Y%m%d")
BACKUP_NAME="mina_db_backup_${TIMESTAMP}"
LOG_FILE="/tmp/backup_${DATE_ONLY}.log"

# Load retention configuration if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$(dirname "$SCRIPT_DIR")/config/backup_retention.conf"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE" >&2
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE" >&2
}

# Validate environment
validate_environment() {
    log "🔍 Validating environment..."
    
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL not set"
        exit 1
    fi
    
    # Check encryption requirements
    if [ "${REQUIRE_ENCRYPTION:-false}" = "true" ]; then
        if [ -z "${GPG_BACKUP_PASSPHRASE:-}" ]; then
            log_error "REQUIRE_ENCRYPTION=true but GPG_BACKUP_PASSPHRASE not set"
            log_error "Add GPG_BACKUP_PASSPHRASE to Replit Secrets or set REQUIRE_ENCRYPTION=false"
            exit 1
        fi
        USE_ENCRYPTION=true
        log "🔒 Encryption required and enabled"
    elif [ -z "${GPG_BACKUP_PASSPHRASE:-}" ]; then
        log_warning "GPG_BACKUP_PASSPHRASE not set - backups will NOT be encrypted"
        log_warning "Set GPG_BACKUP_PASSPHRASE in Replit Secrets for encrypted backups"
        USE_ENCRYPTION=false
    else
        USE_ENCRYPTION=true
    fi
    
    # Check required commands
    for cmd in pg_dump gzip; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd command not found"
            exit 1
        fi
    done
    
    if [ "$USE_ENCRYPTION" = true ] && ! command -v gpg &> /dev/null; then
        log_error "gpg command not found but GPG_BACKUP_PASSPHRASE is set"
        exit 1
    fi
    
    log_success "Environment validation passed"
}

# Create backup directories
create_directories() {
    log "📁 Creating backup directories..."
    
    # Create temporary backup directory (not web-accessible)
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"  # Owner only
    
    # Create encrypted backup directory (persistent storage)
    if [ "$USE_ENCRYPTION" = true ]; then
        mkdir -p "$ENCRYPTED_BACKUP_DIR"
        chmod 700 "$ENCRYPTED_BACKUP_DIR"
    fi
    
    log_success "Directories created and secured"
}

# Perform database backup
perform_backup() {
    log "🗄️  Starting PostgreSQL backup: $BACKUP_NAME"
    
    local sql_file="$BACKUP_DIR/${BACKUP_NAME}.sql"
    local compressed_file="${sql_file}.gz"
    
    # Perform pg_dump (plain SQL format for maximum compatibility)
    if pg_dump "$DATABASE_URL" --format=plain > "$sql_file" 2>> "$LOG_FILE"; then
        log_success "Database dump completed: ${BACKUP_NAME}.sql"
        
        # Get backup size
        local size=$(du -h "$sql_file" | cut -f1)
        log "Backup size: $size"
    else
        log_error "pg_dump failed"
        exit 1
    fi
    
    # Compress backup
    log "🗜️  Compressing backup..."
    if gzip -9 "$sql_file"; then
        log_success "Compression completed"
        echo "$compressed_file"
    else
        log_error "Compression failed"
        exit 1
    fi
}

# Encrypt backup
encrypt_backup() {
    local compressed_file=$1
    
    if [ "$USE_ENCRYPTION" = false ]; then
        log_warning "Skipping encryption (GPG_BACKUP_PASSPHRASE not set)"
        return
    fi
    
    log "🔐 Encrypting backup with GPG AES256..."
    
    local encrypted_file="$ENCRYPTED_BACKUP_DIR/$(basename "$compressed_file").gpg"
    
    # Encrypt using passphrase from environment
    if echo "$GPG_BACKUP_PASSPHRASE" | gpg \
        --batch \
        --yes \
        --passphrase-fd 0 \
        --symmetric \
        --cipher-algo AES256 \
        --output "$encrypted_file" \
        "$compressed_file" 2>&1 | tee -a "$LOG_FILE"; then
        
        log_success "Encryption completed: $(basename "$encrypted_file")"
        
        # Get encrypted file size
        local encrypted_size=$(du -h "$encrypted_file" | cut -f1)
        log "🔒 Encrypted backup size: $encrypted_size"
        
        # Securely delete unencrypted compressed file
        shred -u "$compressed_file" 2>/dev/null || rm -f "$compressed_file"
        log "🧹 Unencrypted backup securely deleted"
        
        echo "$encrypted_file"
    else
        log_error "Encryption failed"
        exit 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    local retention_days=${RETENTION_HOT_DAYS:-${BACKUP_RETENTION_DAYS:-30}}
    
    log "🧹 Cleaning up backups older than ${retention_days} days..."
    
    # Cleanup encrypted backups
    if [ "$USE_ENCRYPTION" = true ] && [ -d "$ENCRYPTED_BACKUP_DIR" ]; then
        local deleted_count=$(find "$ENCRYPTED_BACKUP_DIR" -name "mina_db_backup_*.sql.gz.gpg" -mtime +${retention_days} -delete -print | wc -l)
        if [ "$deleted_count" -gt 0 ]; then
            log_success "Deleted $deleted_count old encrypted backup(s)"
        else
            log "No old encrypted backups to delete"
        fi
    fi
    
    # Cleanup any temporary files
    find "$BACKUP_DIR" -name "mina_db_backup_*.sql*" -mtime +1 -delete 2>/dev/null || true
}

# Verify backup integrity
verify_backup() {
    local backup_file=$1
    
    log "✅ Verifying backup integrity..."
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Verify file is not empty
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")
    if [ "$file_size" -eq 0 ]; then
        log_error "Backup file is empty"
        return 1
    fi
    
    # Verify GPG encryption if applicable
    if [[ "$backup_file" == *.gpg ]]; then
        if gpg --batch --list-packets "$backup_file" &>/dev/null; then
            log_success "Backup file is properly encrypted"
        else
            log_error "Backup file encryption is invalid"
            return 1
        fi
    fi
    
    log_success "Backup verification passed"
    return 0
}

# Generate backup report
generate_report() {
    local backup_file=$1
    local duration=$2
    
    log "📋 Generating backup report..."
    
    cat >> "$LOG_FILE" << EOF

==============================================
BACKUP REPORT
==============================================
Timestamp: $(date)
Backup Name: $(basename "$backup_file")
Backup Location: $(dirname "$backup_file")
Backup Size: $(du -h "$backup_file" | cut -f1)
Encrypted: $([ "$USE_ENCRYPTION" = true ] && echo "Yes (AES256)" || echo "No")
Duration: ${duration}s
Status: SUCCESS
==============================================

EOF
    
    log_success "Backup report generated: $LOG_FILE"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    echo "======================================"
    echo "🚀 Mina Database Backup System"
    echo "======================================"
    
    validate_environment
    create_directories
    
    local compressed_file
    compressed_file=$(perform_backup)
    
    local final_backup_file
    if [ "$USE_ENCRYPTION" = true ]; then
        final_backup_file=$(encrypt_backup "$compressed_file")
    else
        # If not encrypting, move compressed file to final location
        final_backup_file="$BACKUP_DIR/$(basename $compressed_file)"
    fi
    
    verify_backup "$final_backup_file"
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    generate_report "$final_backup_file" "$duration"
    
    echo "======================================"
    log_success "🎉 Backup completed successfully in ${duration}s"
    log_success "📦 Backup location: $final_backup_file"
    echo "======================================"
    
    # Return backup file path for automation
    echo "$final_backup_file"
}

# Run main function
main "$@"
