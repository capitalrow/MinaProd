#!/bin/bash
# Mina Backup Scheduler
# Configures automated database backups

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_database.sh"
CRON_LOG="/tmp/mina_backup_cron.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================"
echo "⏰ Mina Backup Scheduler"
echo "======================================"

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}ERROR: Backup script not found: $BACKUP_SCRIPT${NC}"
    exit 1
fi

# Check if running on Replit (no cron available)
if [ -n "${REPL_ID:-}" ]; then
    echo -e "${YELLOW}⚠️  Running on Replit - cron not available${NC}"
    echo ""
    echo "Replit doesn't support traditional cron jobs."
    echo "Backup strategies for Replit:"
    echo ""
    echo "1. Manual backups:"
    echo "   ./scripts/backup_database.sh"
    echo ""
    echo "2. Scheduled via Replit Cron (if available):"
    echo "   - Add to .replit file:"
    echo "   run = \"./scripts/backup_database.sh\""
    echo ""
    echo "3. External scheduler (recommended for production):"
    echo "   - Use GitHub Actions with cron schedule"
    echo "   - Use external monitoring service (UptimeRobot, Cronitor)"
    echo "   - Use cloud scheduler (AWS EventBridge, GCP Cloud Scheduler)"
    echo ""
    echo "4. Application-level scheduler:"
    echo "   - Add APScheduler to Flask app"
    echo "   - Configure daily backup job in app initialization"
    echo ""
    
    # Create sample GitHub Actions workflow
    cat > /tmp/backup-schedule.yml << 'EOF'
name: Database Backup

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Install PostgreSQL client
        run: |
          sudo apt-get update
          sudo apt-get install -y postgresql-client
      
      - name: Run backup
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GPG_BACKUP_PASSPHRASE: ${{ secrets.GPG_BACKUP_PASSPHRASE }}
        run: |
          chmod +x scripts/backup_database.sh
          ./scripts/backup_database.sh
      
      - name: Upload backup to artifacts
        uses: actions/upload-artifact@v3
        with:
          name: database-backup-${{ github.run_number }}
          path: ~/.mina_backups_encrypted/
          retention-days: 30
EOF
    
    echo -e "${BLUE}📄 Sample GitHub Actions workflow created: /tmp/backup-schedule.yml${NC}"
    echo "   Copy this to .github/workflows/ to enable automated backups"
    echo ""
    
    exit 0
fi

# Standard Linux/Unix cron setup
echo "Setting up cron job for automated backups..."
echo ""

# Ask for schedule
echo "Select backup schedule:"
echo "1. Daily at 2 AM"
echo "2. Daily at midnight"
echo "3. Every 6 hours"
echo "4. Custom cron expression"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 2 * * *"
        DESCRIPTION="Daily at 2 AM"
        ;;
    2)
        CRON_SCHEDULE="0 0 * * *"
        DESCRIPTION="Daily at midnight"
        ;;
    3)
        CRON_SCHEDULE="0 */6 * * *"
        DESCRIPTION="Every 6 hours"
        ;;
    4)
        read -p "Enter cron expression: " CRON_SCHEDULE
        DESCRIPTION="Custom schedule"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Create cron job
CRON_CMD="$CRON_SCHEDULE $BACKUP_SCRIPT >> $CRON_LOG 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo -e "${YELLOW}⚠️  Backup cron job already exists${NC}"
    read -p "Replace existing job? (yes/no): " replace
    
    if [ "$replace" != "yes" ]; then
        echo "Cancelled"
        exit 0
    fi
    
    # Remove existing job
    (crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT") | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo -e "${GREEN}✅ Backup cron job installed successfully${NC}"
echo "Schedule: $DESCRIPTION ($CRON_SCHEDULE)"
echo "Script: $BACKUP_SCRIPT"
echo "Log file: $CRON_LOG"
echo ""
echo "To view scheduled jobs:"
echo "  crontab -l"
echo ""
echo "To remove backup job:"
echo "  crontab -e"
echo ""
echo "======================================"
