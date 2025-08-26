#!/bin/bash
# Mina Production Deployment Script

set -e  # Exit on any error

echo "🚀 Starting Mina Production Deployment..."

# Check environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is required"
    exit 1
fi

if [ -z "$SESSION_SECRET" ]; then
    echo "❌ ERROR: SESSION_SECRET environment variable is required"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY environment variable is required"
    exit 1
fi

echo "✅ Environment variables validated"

# Database migration
echo "📊 Running database migrations..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created/updated')
"

# Health check
echo "🏥 Running health checks..."
python -c "
import requests
import time
import subprocess
import sys

# Start server in background
proc = subprocess.Popen(['gunicorn', '--bind', '0.0.0.0:5000', '--workers', '1', '--timeout', '30', 'main:app'])
time.sleep(5)

try:
    # Test health endpoint
    response = requests.get('http://localhost:5000/api/health', timeout=10)
    if response.status_code == 200:
        print('✅ Health check passed')
    else:
        print(f'❌ Health check failed: {response.status_code}')
        sys.exit(1)
finally:
    proc.terminate()
    proc.wait()
"

echo "🎉 Deployment validation completed successfully!"
echo "🚀 Ready for production deployment"