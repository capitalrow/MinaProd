#!/bin/bash
# Mina Database Backup Script

set -e

BACKUP_DIR="/backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="mina_backup_${TIMESTAMP}.sql"

echo "🗄️ Starting database backup..."

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Parse DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

echo "📊 Creating database backup: $BACKUP_NAME"

# Perform backup
pg_dump $DATABASE_URL > $BACKUP_DIR/$BACKUP_NAME

# Compress backup
gzip $BACKUP_DIR/$BACKUP_NAME

echo "✅ Backup completed: ${BACKUP_NAME}.gz"

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "mina_backup_*.sql.gz" -mtime +30 -delete

echo "🧹 Cleaned up old backups"
echo "🎉 Backup process completed successfully!"