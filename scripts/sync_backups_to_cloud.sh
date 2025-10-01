#!/bin/bash
# Mina Backup Cloud Storage Sync
# Syncs encrypted backups to S3/GCS for durable off-site storage

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKUP_DIR="${ENCRYPTED_BACKUP_DIR:-$HOME/.mina_backups_encrypted}"
CLOUD_PROVIDER="${CLOUD_BACKUP_PROVIDER:-auto}"  # s3, gcs, or auto
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
GCS_BUCKET="${GCS_BACKUP_BUCKET:-}"
RETENTION_30DAY=30
RETENTION_90DAY=90
LOG_FILE="/tmp/backup_sync_$(date +%Y%m%d).log"

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

Sync encrypted backups to cloud storage (S3 or GCS)

OPTIONS:
    --provider PROVIDER    Cloud provider: s3 or gcs (default: auto-detect)
    --bucket BUCKET        Bucket name (required)
    --retention DAYS       Retention period: 30 or 90 (default: 30)
    --dry-run              Show what would be synced without syncing
    -h, --help             Show this help message

ENVIRONMENT VARIABLES:
    AWS Configuration (for S3):
      AWS_ACCESS_KEY_ID       AWS access key
      AWS_SECRET_ACCESS_KEY   AWS secret key
      AWS_DEFAULT_REGION      AWS region (e.g., us-east-1)
      S3_BACKUP_BUCKET        S3 bucket name
    
    GCP Configuration (for GCS):
      GOOGLE_APPLICATION_CREDENTIALS    Path to service account JSON
      GCS_BACKUP_BUCKET                 GCS bucket name

EXAMPLES:
    # Sync to S3 (30-day retention)
    ./scripts/sync_backups_to_cloud.sh --provider s3 --bucket my-backups-30day

    # Sync to GCS (90-day retention)
    ./scripts/sync_backups_to_cloud.sh --provider gcs --bucket my-backups-90day --retention 90

    # Dry run (test without uploading)
    ./scripts/sync_backups_to_cloud.sh --provider s3 --bucket test-bucket --dry-run

SETUP INSTRUCTIONS:
    1. Create cloud storage bucket with server-side encryption
    2. Configure credentials (AWS CLI or GCP service account)
    3. Set environment variables
    4. Run this script manually or via cron

EOF
    exit 1
}

detect_provider() {
    if [ "$CLOUD_PROVIDER" != "auto" ]; then
        echo "$CLOUD_PROVIDER"
        return
    fi
    
    # Auto-detect based on available tools and config
    if command -v aws &> /dev/null && [ -n "${AWS_ACCESS_KEY_ID:-}" ]; then
        echo "s3"
    elif command -v gsutil &> /dev/null && [ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
        echo "gcs"
    else
        echo "none"
    fi
}

sync_to_s3() {
    local bucket=$1
    local retention=$2
    local dry_run=$3
    
    log_info "Syncing to S3 bucket: s3://$bucket"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install with: pip install awscli"
        exit 1
    fi
    
    # Verify credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "AWS credentials not configured or invalid"
        log_info "Configure with: aws configure"
        exit 1
    fi
    
    # Determine S3 path based on retention
    local s3_path
    if [ "$retention" -eq 90 ]; then
        s3_path="s3://${bucket}/backups/90day/"
    else
        s3_path="s3://${bucket}/backups/30day/"
    fi
    
    # Sync files
    local sync_cmd="aws s3 sync \"$BACKUP_DIR\" \"$s3_path\" \
        --exclude \"*\" \
        --include \"*.gpg\" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256"
    
    if [ "$dry_run" = true ]; then
        sync_cmd="$sync_cmd --dryrun"
        log_warning "DRY RUN - No files will be uploaded"
    fi
    
    if eval "$sync_cmd" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "S3 sync completed"
        
        # Set lifecycle policy
        if [ "$dry_run" = false ]; then
            set_s3_lifecycle "$bucket" "$retention"
        fi
    else
        log_error "S3 sync failed"
        exit 1
    fi
}

set_s3_lifecycle() {
    local bucket=$1
    local retention=$2
    
    log_warning "⚠️  Lifecycle policy management requires dedicated bucket ownership"
    log_info "For production, ensure this script has exclusive control of lifecycle policies"
    log_info "Or manually configure lifecycle policies in AWS Console"
    
    # Ask for confirmation before overwriting lifecycle
    if [ "${AUTO_LIFECYCLE:-false}" != "true" ]; then
        log_warning "Skipping automatic lifecycle policy (set AUTO_LIFECYCLE=true to enable)"
        log_info "Manual lifecycle policy recommended:"
        echo "  - Rule: Delete backups/${retention}day/* after ${retention} days"
        echo "  - Rule: Transition to GLACIER after $((retention / 2)) days"
        return 0
    fi
    
    log_info "Setting S3 lifecycle policy (${retention}-day retention)..."
    
    # Create lifecycle policy JSON
    cat > /tmp/s3_lifecycle.json << EOF
{
    "Rules": [
        {
            "Id": "DeleteOldBackups${retention}Day",
            "Status": "Enabled",
            "Prefix": "backups/${retention}day/",
            "Expiration": {
                "Days": ${retention}
            }
        },
        {
            "Id": "TransitionToGlacier${retention}Day",
            "Status": "Enabled",
            "Prefix": "backups/${retention}day/",
            "Transitions": [
                {
                    "Days": $((retention / 2)),
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
EOF
    
    if aws s3api put-bucket-lifecycle-configuration \
        --bucket "$bucket" \
        --lifecycle-configuration file:///tmp/s3_lifecycle.json 2>&1 | tee -a "$LOG_FILE"; then
        log_success "S3 lifecycle policy configured"
        rm /tmp/s3_lifecycle.json
    else
        log_warning "Failed to set S3 lifecycle policy"
        rm /tmp/s3_lifecycle.json
    fi
}

sync_to_gcs() {
    local bucket=$1
    local retention=$2
    local dry_run=$3
    
    log_info "Syncing to GCS bucket: gs://$bucket"
    
    # Check gsutil
    if ! command -v gsutil &> /dev/null; then
        log_error "gsutil not found. Install Google Cloud SDK"
        exit 1
    fi
    
    # Verify credentials
    if ! gsutil ls gs://$bucket &>/dev/null; then
        log_error "GCS credentials not configured or bucket not accessible"
        log_info "Authenticate with: gcloud auth application-default login"
        exit 1
    fi
    
    # Determine GCS path based on retention
    local gcs_path
    if [ "$retention" -eq 90 ]; then
        gcs_path="gs://${bucket}/backups/90day/"
    else
        gcs_path="gs://${bucket}/backups/30day/"
    fi
    
    # Sync files
    local sync_cmd="gsutil -m rsync -r -x '.*[^.gpg]$' \"$BACKUP_DIR\" \"$gcs_path\""
    
    if [ "$dry_run" = true ]; then
        sync_cmd="$sync_cmd -n"
        log_warning "DRY RUN - No files will be uploaded"
    fi
    
    if eval "$sync_cmd" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "GCS sync completed"
        
        # Set lifecycle policy
        if [ "$dry_run" = false ]; then
            set_gcs_lifecycle "$bucket" "$retention"
        fi
    else
        log_error "GCS sync failed"
        exit 1
    fi
}

set_gcs_lifecycle() {
    local bucket=$1
    local retention=$2
    
    log_info "Setting GCS lifecycle policy (${retention}-day retention)..."
    
    # Create lifecycle policy JSON
    cat > /tmp/gcs_lifecycle.json << EOF
{
    "lifecycle": {
        "rule": [
            {
                "action": {"type": "Delete"},
                "condition": {
                    "age": ${retention},
                    "matchesPrefix": ["backups/${retention}day/"]
                }
            },
            {
                "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
                "condition": {
                    "age": $((retention / 2)),
                    "matchesPrefix": ["backups/${retention}day/"]
                }
            }
        ]
    }
}
EOF
    
    if gsutil lifecycle set /tmp/gcs_lifecycle.json gs://$bucket 2>&1 | tee -a "$LOG_FILE"; then
        log_success "GCS lifecycle policy configured"
        rm /tmp/gcs_lifecycle.json
    else
        log_warning "Failed to set GCS lifecycle policy (may already exist)"
        rm /tmp/gcs_lifecycle.json
    fi
}

# Parse arguments
BUCKET=""
RETENTION=30
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            CLOUD_PROVIDER="$2"
            shift 2
            ;;
        --bucket)
            BUCKET="$2"
            shift 2
            ;;
        --retention)
            RETENTION="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
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

# Main execution
echo "======================================"
echo "☁️  Mina Backup Cloud Storage Sync"
echo "======================================"
echo ""

# Detect provider
DETECTED_PROVIDER=$(detect_provider)
if [ "$CLOUD_PROVIDER" = "auto" ]; then
    CLOUD_PROVIDER="$DETECTED_PROVIDER"
fi

if [ "$CLOUD_PROVIDER" = "none" ]; then
    log_error "No cloud provider detected or configured"
    log_info "Install AWS CLI or GCS SDK and configure credentials"
    log_info "AWS: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    log_info "GCS: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Validate bucket
if [ -z "$BUCKET" ]; then
    if [ "$CLOUD_PROVIDER" = "s3" ] && [ -n "$S3_BACKUP_BUCKET" ]; then
        BUCKET="$S3_BACKUP_BUCKET"
    elif [ "$CLOUD_PROVIDER" = "gcs" ] && [ -n "$GCS_BACKUP_BUCKET" ]; then
        BUCKET="$GCS_BACKUP_BUCKET"
    else
        log_error "Bucket name not specified"
        usage
    fi
fi

# Validate retention
if [ "$RETENTION" -ne 30 ] && [ "$RETENTION" -ne 90 ]; then
    log_error "Retention must be 30 or 90 days"
    exit 1
fi

# Check if backups exist
if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
    log_warning "No backups found in $BACKUP_DIR"
    log_info "Run ./scripts/backup_database.sh first"
    exit 0
fi

# Display configuration
log_info "Configuration:"
echo "  Provider: $CLOUD_PROVIDER"
echo "  Bucket: $BUCKET"
echo "  Retention: ${RETENTION} days"
echo "  Backup directory: $BACKUP_DIR"
echo "  Dry run: $DRY_RUN"
echo ""

# Count backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.gpg" 2>/dev/null | wc -l)
log_info "Found $BACKUP_COUNT encrypted backup(s) to sync"
echo ""

# Perform sync
case "$CLOUD_PROVIDER" in
    s3)
        sync_to_s3 "$BUCKET" "$RETENTION" "$DRY_RUN"
        ;;
    gcs)
        sync_to_gcs "$BUCKET" "$RETENTION" "$DRY_RUN"
        ;;
    *)
        log_error "Invalid provider: $CLOUD_PROVIDER"
        exit 1
        ;;
esac

echo ""
log_success "✅ Cloud sync complete!"
log_info "Sync log: $LOG_FILE"
echo "======================================"
