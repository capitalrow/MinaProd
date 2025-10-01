#!/bin/bash
# Automated secret rotation script for Mina
# Usage: ./scripts/rotate_secrets.sh [secret_name] [--show]
# Example: ./scripts/rotate_secrets.sh SESSION_SECRET

set -euo pipefail

SECRET_NAME="${1:-}"
SHOW_SECRET="false"
ROTATION_LOG="docs/security/.rotation_log"
BACKUP_DIR="backups"

# Check for --show flag
if [[ "${2:-}" == "--show" ]]; then
    SHOW_SECRET="true"
fi

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Supported secrets and their generation commands
declare -A ROTATION_COMMANDS=(
    ["SESSION_SECRET"]="openssl rand -base64 32"
    ["API_SECRET_KEY"]="openssl rand -hex 32"
)

# Rotation frequencies (in days)
declare -A ROTATION_FREQUENCIES=(
    ["SESSION_SECRET"]="30"
    ["API_SECRET_KEY"]="30"
    ["OPENAI_API_KEY"]="90"
    ["DATABASE_URL"]="90"
    ["SENTRY_DSN"]="365"
)

usage() {
    echo "Usage: $0 [secret_name] [--show]"
    echo ""
    echo "Supported secrets:"
    for secret in "${!ROTATION_COMMANDS[@]}"; do
        echo "  - $secret (auto-generated)"
    done
    echo "  - OPENAI_API_KEY (manual - provide new key)"
    echo "  - DATABASE_URL (manual - update in provider dashboard)"
    echo "  - SENTRY_DSN (manual - generate in Sentry dashboard)"
    echo ""
    echo "Options:"
    echo "  --show    Display generated secret value (WARNING: prints to stdout)"
    exit 1
}

log_rotation() {
    local secret=$1
    local frequency=${ROTATION_FREQUENCIES[$secret]:-30}
    local next_date=$(date -d "+${frequency} days" +%Y-%m-%d 2>/dev/null || date -v+${frequency}d +%Y-%m-%d)
    
    echo "$(date +%Y-%m-%d) | $secret | $(whoami) | $next_date | Automated rotation" >> "$ROTATION_LOG"
}

backup_secret() {
    local secret_name=$1
    local secret_value=$2
    
    mkdir -p "$BACKUP_DIR"
    
    # Check if GPG is available
    if command -v gpg &> /dev/null; then
        # Get backup passphrase from environment
        local backup_passphrase="${GPG_BACKUP_PASSPHRASE:-}"
        
        if [[ -z "$backup_passphrase" ]]; then
            echo -e "${RED}❌ ERROR: GPG_BACKUP_PASSPHRASE not set${NC}"
            echo -e "${YELLOW}⚠️  Set GPG_BACKUP_PASSPHRASE in Replit Secrets for encrypted backups${NC}"
            echo -e "${YELLOW}⚠️  Generate one with: openssl rand -base64 32${NC}"
            echo ""
            echo "Skipping backup (unsafe to backup without encryption)"
            return 1
        fi
        
        # GPG-encrypted backup with secret passphrase
        BACKUP_FILE="${BACKUP_DIR}/${secret_name}_$(date +%Y%m%d_%H%M%S).gpg"
        echo "$secret_value" | gpg --symmetric --cipher-algo AES256 --batch --yes --passphrase "$backup_passphrase" > "$BACKUP_FILE"
        chmod 600 "$BACKUP_FILE"
        echo -e "${GREEN}✅ Old value backed up (encrypted) to $BACKUP_FILE${NC}"
    else
        echo -e "${YELLOW}⚠️  GPG not available. Install GPG for encrypted backups: apt install gnupg${NC}"
        echo "Skipping backup (unsafe to backup without encryption)"
        return 1
    fi
}

rotate_auto() {
    local secret=$1
    local gen_command="${ROTATION_COMMANDS[$secret]}"
    
    echo -e "${YELLOW}🔄 Rotating $secret...${NC}"
    
    # Generate new value
    echo "Generating new value..."
    NEW_VALUE=$(eval "$gen_command")
    
    # Backup old value (if available)
    if OLD_VALUE=$(printenv "$secret" 2>/dev/null) && [[ -n "$OLD_VALUE" ]]; then
        backup_secret "$secret" "$OLD_VALUE"
    else
        echo -e "${YELLOW}⚠️  No existing value found (first rotation)${NC}"
    fi
    
    # Save new value to secure temp file
    TEMP_FILE=$(mktemp)
    chmod 600 "$TEMP_FILE"
    echo "$NEW_VALUE" > "$TEMP_FILE"
    
    # Display instructions (don't show secret by default)
    echo ""
    if [[ "$SHOW_SECRET" == "true" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: Displaying secret value (use --show flag carefully)${NC}"
        echo -e "${GREEN}New $secret value:${NC}"
        echo "=================================================="
        echo "$NEW_VALUE"
        echo "=================================================="
    else
        echo -e "${GREEN}New $secret value generated${NC}"
        echo "To view: cat $TEMP_FILE"
    fi
    
    echo ""
    echo "To apply this rotation:"
    echo "1. In Replit: Tools → Secrets → $secret → Paste from: cat $TEMP_FILE"
    echo "2. Or via Replit CLI (if available):"
    echo "   replit secrets set $secret=\"\$(cat $TEMP_FILE)\""
    echo "3. Application will auto-restart after secret update"
    echo ""
    echo "After applying, run:"
    echo "  $0 $secret --verify"
    echo ""
    
    # Don't log until verification
    echo -e "${YELLOW}⚠️  Rotation prepared but NOT logged yet${NC}"
    echo -e "${YELLOW}⚠️  After applying secret in Replit, run: $0 $secret --verify${NC}"
    
    # Keep temp file for reference
    echo ""
    echo -e "${GREEN}✅ $secret rotation prepared${NC}"
    echo "Secure temp file: $TEMP_FILE (will be cleaned up on reboot)"
}

verify_rotation() {
    local secret=$1
    
    echo -e "${YELLOW}🔍 Verifying $secret rotation...${NC}"
    
    # Check if secret is set
    if CURRENT_VALUE=$(printenv "$secret" 2>/dev/null) && [[ -n "$CURRENT_VALUE" ]]; then
        echo -e "${GREEN}✅ $secret is set in environment${NC}"
        
        # Log successful rotation
        log_rotation "$secret"
        echo -e "${GREEN}✅ Rotation logged successfully${NC}"
        
        # Calculate next rotation date
        local frequency=${ROTATION_FREQUENCIES[$secret]:-30}
        local next_date=$(date -d "+${frequency} days" +%Y-%m-%d 2>/dev/null || date -v+${frequency}d +%Y-%m-%d)
        echo ""
        echo -e "${GREEN}🎉 Rotation complete!${NC}"
        echo "Next rotation due: $next_date"
    else
        echo -e "${RED}❌ $secret is NOT set in environment${NC}"
        echo "Please update the secret in Replit Secrets first."
        exit 1
    fi
}

rotate_manual() {
    local secret=$1
    
    echo -e "${YELLOW}🔄 Manual rotation required for $secret${NC}"
    echo ""
    
    case $secret in
        OPENAI_API_KEY)
            echo "Steps to rotate OpenAI API key:"
            echo "1. Go to https://platform.openai.com/api-keys"
            echo "2. Click 'Create new secret key'"
            echo "3. Name: 'Mina Production - $(date +%Y-%m)'"
            echo "4. Copy the key (NEVER print it here)"
            echo "5. Update in Replit: Tools → Secrets → OPENAI_API_KEY"
            echo "6. Verify transcription works in app"
            echo "7. Revoke old key in OpenAI dashboard"
            echo "8. Run: $0 OPENAI_API_KEY --verify"
            ;;
        DATABASE_URL)
            echo "Steps to rotate database credentials:"
            echo "1. Go to your database provider (Neon/Replit Database pane)"
            echo "2. Reset password / Generate new credentials"
            echo "3. Copy new DATABASE_URL (NEVER print it here)"
            echo "4. Update in Replit: Tools → Secrets → DATABASE_URL"
            echo "5. Verify app restarts successfully"
            echo "6. Test database connectivity: curl /ops/health"
            echo "7. Run: $0 DATABASE_URL --verify"
            ;;
        SENTRY_DSN)
            echo "Steps to rotate Sentry DSN:"
            echo "1. Go to Sentry → Settings → Client Keys (DSN)"
            echo "2. Create new key"
            echo "3. Copy DSN (NEVER print it here)"
            echo "4. Update in Replit: Tools → Secrets → SENTRY_DSN"
            echo "5. Verify errors still reported: trigger test error"
            echo "6. Delete old key in Sentry"
            echo "7. Run: $0 SENTRY_DSN --verify"
            ;;
        *)
            echo "No specific instructions for $secret"
            ;;
    esac
    
    echo ""
    echo -e "${YELLOW}⚠️  Do NOT confirm until rotation is complete and verified${NC}"
}

check_overdue() {
    echo "Checking for overdue rotations..."
    echo ""
    
    if [[ ! -f "$ROTATION_LOG" ]]; then
        echo "No rotation log found. Initialize with first rotations."
        return
    fi
    
    local has_issues=false
    
    while IFS='|' read -r date secret user next_date notes; do
        # Skip empty lines and comments
        [[ -z "$date" || "$date" =~ ^# ]] && continue
        
        # Trim whitespace
        date=$(echo "$date" | xargs)
        secret=$(echo "$secret" | xargs)
        next_date=$(echo "$next_date" | xargs)
        
        # Calculate days until next rotation
        if [[ -n "$next_date" ]]; then
            TODAY=$(date +%s)
            NEXT=$(date -d "$next_date" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$next_date" +%s)
            DAYS_REMAINING=$(( (NEXT - TODAY) / 86400 ))
            
            if [[ $DAYS_REMAINING -lt 0 ]]; then
                echo -e "${RED}🚨 OVERDUE: $secret (${DAYS_REMAINING#-} days overdue)${NC}"
                echo "   Rotate now: $0 $secret"
                has_issues=true
            elif [[ $DAYS_REMAINING -lt 7 ]]; then
                echo -e "${YELLOW}⚠️  DUE SOON: $secret ($DAYS_REMAINING days remaining)${NC}"
                echo "   Schedule rotation: $0 $secret"
            else
                echo -e "${GREEN}✅ OK: $secret ($DAYS_REMAINING days remaining)${NC}"
            fi
        fi
    done < "$ROTATION_LOG"
    
    echo ""
    if [[ "$has_issues" == "true" ]]; then
        exit 1  # Non-zero exit for monitoring/CI
    fi
}

# Main logic
case "${SECRET_NAME}" in
    "")
        # No argument: Show status
        check_overdue
        echo "To rotate a specific secret: $0 [secret_name]"
        exit 0
        ;;
    --verify)
        echo "Error: Specify secret name before --verify"
        echo "Usage: $0 [secret_name] --verify"
        exit 1
        ;;
    *)
        # Handle --verify mode
        if [[ "${2:-}" == "--verify" ]]; then
            verify_rotation "$SECRET_NAME"
            exit 0
        fi
        
        # Validate secret name
        if [[ ! ${ROTATION_FREQUENCIES[$SECRET_NAME]+_} ]]; then
            echo -e "${RED}Error: Unknown secret '$SECRET_NAME'${NC}"
            usage
        fi
        
        # Perform rotation
        if [[ ${ROTATION_COMMANDS[$SECRET_NAME]+_} ]]; then
            # Auto-generated secret
            rotate_auto "$SECRET_NAME"
        else
            # Manual rotation required
            rotate_manual "$SECRET_NAME"
        fi
        ;;
esac
