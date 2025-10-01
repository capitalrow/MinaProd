#!/bin/bash
# Mina Database Restore Script
# Restores from encrypted or unencrypted backup files

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENCRYPTED_BACKUP_DIR="${ENCRYPTED_BACKUP_DIR:-$HOME/.mina_backups_encrypted}"
TEMP_RESTORE_DIR="/tmp/mina_restore"
LOG_FILE="/tmp/restore_$(date +%Y%m%d_%H%M%S).log"

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Restore Mina database from backup

OPTIONS:
    -f, --file FILE         Backup file to restore from (required)
    -l, --list             List available backups
    -c, --confirm          Skip confirmation prompt (use with caution!)
    -h, --help             Show this help message

EXAMPLES:
    # List available backups
    $0 --list

    # Restore from specific backup (with confirmation)
    $0 --file ~/.mina_backups_encrypted/mina_db_backup_20251001_120000.sql.gz.gpg

    # Restore without confirmation (automated restore)
    $0 --file /path/to/backup.sql.gz.gpg --confirm

EOF
    exit 1
}

# List available backups
list_backups() {
    log_info "📋 Available backups:"
    echo ""
    
    if [ -d "$ENCRYPTED_BACKUP_DIR" ]; then
        local backups=$(find "$ENCRYPTED_BACKUP_DIR" -name "mina_db_backup_*.sql.gz.gpg" -o -name "mina_db_backup_*.sql.gz" | sort -r)
        
        if [ -z "$backups" ]; then
            log_warning "No backups found in $ENCRYPTED_BACKUP_DIR"
        else
            local count=1
            while IFS= read -r backup; do
                local size=$(du -h "$backup" | cut -f1)
                local date=$(echo "$backup" | grep -oE '[0-9]{8}_[0-9]{6}')
                local encrypted=""
                [[ "$backup" == *.gpg ]] && encrypted=" (encrypted)"
                
                printf "%2d. %s - %s - %s%s\n" "$count" "$(basename $backup)" "$size" "$date" "$encrypted"
                count=$((count + 1))
            done <<< "$backups"
        fi
    else
        log_warning "Backup directory does not exist: $ENCRYPTED_BACKUP_DIR"
    fi
    echo ""
    exit 0
}

# Validate environment
validate_environment() {
    log "🔍 Validating environment..."
    
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL not set"
        exit 1
    fi
    
    # Check required commands
    for cmd in pg_restore psql gzip; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd command not found"
            exit 1
        fi
    done
    
    log_success "Environment validation passed"
}

# Decrypt backup if needed
decrypt_backup() {
    local backup_file=$1
    
    if [[ "$backup_file" != *.gpg ]]; then
        # Not encrypted, return as-is
        echo "$backup_file"
        return 0
    fi
    
    log "🔓 Decrypting backup..."
    
    if [ -z "${GPG_BACKUP_PASSPHRASE:-}" ]; then
        log_error "GPG_BACKUP_PASSPHRASE not set - cannot decrypt backup"
        log_error "Set GPG_BACKUP_PASSPHRASE in Replit Secrets"
        exit 1
    fi
    
    local decrypted_file="$TEMP_RESTORE_DIR/$(basename ${backup_file%.gpg})"
    
    # Decrypt using passphrase from environment
    if echo "$GPG_BACKUP_PASSPHRASE" | gpg \
        --batch \
        --yes \
        --passphrase-fd 0 \
        --decrypt \
        --output "$decrypted_file" \
        "$backup_file" 2>&1 | tee -a "$LOG_FILE"; then
        
        log_success "Decryption completed"
        echo "$decrypted_file"
    else
        log_error "Decryption failed"
        exit 1
    fi
}

# Decompress backup
decompress_backup() {
    local compressed_file=$1
    
    if [[ "$compressed_file" != *.gz ]]; then
        # Not compressed, return as-is
        echo "$compressed_file"
        return 0
    fi
    
    log "🗜️  Decompressing backup..."
    
    local decompressed_file="${compressed_file%.gz}"
    
    if gunzip -c "$compressed_file" > "$decompressed_file"; then
        log_success "Decompression completed"
        echo "$decompressed_file"
    else
        log_error "Decompression failed"
        exit 1
    fi
}

# Create database backup before restore
create_pre_restore_backup() {
    log_warning "⚠️  Creating safety backup before restore..."
    
    local safety_backup="$TEMP_RESTORE_DIR/pre_restore_safety_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if pg_dump "$DATABASE_URL" > "$safety_backup" 2>&1 | tee -a "$LOG_FILE"; then
        gzip "$safety_backup"
        log_success "Safety backup created: ${safety_backup}.gz"
        echo "${safety_backup}.gz"
    else
        log_error "Failed to create safety backup"
        return 1
    fi
}

# Perform database restore
perform_restore() {
    local backup_file=$1
    
    log "🔄 Starting database restore..."
    log_warning "⚠️  This will REPLACE all existing data!"
    
    # Extract database connection details
    local db_url="$DATABASE_URL"
    
    # Drop existing connections
    log "📡 Terminating existing database connections..."
    psql "$db_url" -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();" 2>&1 | tee -a "$LOG_FILE" || true
    
    # Check if backup is custom format or plain SQL
    local format_type=$(file "$backup_file" | grep -q "PostgreSQL custom" && echo "custom" || echo "plain")
    
    if [ "$format_type" = "custom" ]; then
        log "📊 Restoring from custom format backup..."
        
        # Drop and recreate schema for clean restore
        log "🗑️  Dropping existing schema..."
        psql "$db_url" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>&1 | tee -a "$LOG_FILE"
        
        # Restore using pg_restore
        if pg_restore \
            --dbname="$db_url" \
            --verbose \
            --clean \
            --if-exists \
            --no-owner \
            --no-acl \
            "$backup_file" 2>&1 | tee -a "$LOG_FILE"; then
            
            log_success "Database restore completed"
        else
            log_error "Database restore failed"
            exit 1
        fi
    else
        log "📊 Restoring from plain SQL backup..."
        
        # Restore using psql
        if psql "$db_url" < "$backup_file" 2>&1 | tee -a "$LOG_FILE"; then
            log_success "Database restore completed"
        else
            log_error "Database restore failed"
            exit 1
        fi
    fi
}

# Verify restore
verify_restore() {
    log "✅ Verifying restore..."
    
    # Check database connectivity
    if ! psql "$DATABASE_URL" -c "SELECT 1;" &>/dev/null; then
        log_error "Database connectivity check failed"
        return 1
    fi
    
    # Check table count
    local table_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    
    if [ "$table_count" -gt 0 ]; then
        log_success "Restore verified: $table_count tables found"
    else
        log_warning "Warning: No tables found in database"
    fi
    
    return 0
}

# Cleanup temporary files
cleanup() {
    log "🧹 Cleaning up temporary files..."
    
    if [ -d "$TEMP_RESTORE_DIR" ]; then
        # Securely delete sensitive temporary files
        find "$TEMP_RESTORE_DIR" -type f -exec shred -u {} \; 2>/dev/null || rm -rf "$TEMP_RESTORE_DIR"
        log_success "Cleanup completed"
    fi
}

# Main execution
main() {
    local backup_file=""
    local skip_confirmation=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--file)
                backup_file="$2"
                shift 2
                ;;
            -l|--list)
                list_backups
                ;;
            -c|--confirm)
                skip_confirmation=true
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
    if [ -z "$backup_file" ]; then
        log_error "Backup file not specified"
        usage
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file does not exist: $backup_file"
        exit 1
    fi
    
    echo "======================================"
    echo "🔄 Mina Database Restore System"
    echo "======================================"
    
    # Display restore information
    log_info "Backup file: $backup_file"
    log_info "Backup size: $(du -h "$backup_file" | cut -f1)"
    log_info "Database: ${DATABASE_URL%%@*}@***"
    echo ""
    
    # Confirmation prompt
    if [ "$skip_confirmation" = false ]; then
        log_warning "⚠️  WARNING: This will REPLACE all data in the database!"
        log_warning "⚠️  A safety backup will be created before restore."
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " confirm
        
        if [ "$confirm" != "yes" ]; then
            log "❌ Restore cancelled by user"
            exit 0
        fi
    fi
    
    local start_time=$(date +%s)
    
    # Create temporary directory
    mkdir -p "$TEMP_RESTORE_DIR"
    chmod 700 "$TEMP_RESTORE_DIR"
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    validate_environment
    
    # Create safety backup
    local safety_backup
    safety_backup=$(create_pre_restore_backup) || {
        log_error "Failed to create safety backup - aborting restore"
        exit 1
    }
    
    # Decrypt if needed
    local decrypted_file
    decrypted_file=$(decrypt_backup "$backup_file")
    
    # Decompress if needed
    local decompressed_file
    decompressed_file=$(decompress_backup "$decrypted_file")
    
    # Perform restore
    perform_restore "$decompressed_file"
    
    # Verify restore
    verify_restore
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "======================================"
    log_success "🎉 Restore completed successfully in ${duration}s"
    log_success "💾 Safety backup: $safety_backup"
    log_success "📋 Restore log: $LOG_FILE"
    echo "======================================"
}

# Run main function
main "$@"
