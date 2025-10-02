# Troubleshooting Guide

## Common Issues and Solutions

### Application Won't Start

#### Symptom: `ModuleNotFoundError`
```
ModuleNotFoundError: No module named 'flask_socketio'
```

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

#### Symptom: `DATABASE_URL not set`
```
KeyError: 'DATABASE_URL'
```

**Solution**:
1. Check environment variables are set
2. For Replit: Ensure PostgreSQL database is created
3. For local: Set in `.env` file

#### Symptom: Port 5000 already in use
```
OSError: [Errno 98] Address already in use
```

**Solution**:
```bash
# Find and kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
gunicorn --bind 0.0.0.0:5001 main:app
```

### Database Issues

#### Migration Conflict
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution**:
```bash
# Check current revision
flask db current

# Stamp to specific revision if needed
flask db stamp head

# Then upgrade
flask db upgrade
```

#### Connection Pool Exhausted
```
sqlalchemy.exc.TimeoutError: QueuePool limit exceeded
```

**Solution**:
```python
# In app.py, increase pool size
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 20,  # Increase from 10
    "max_overflow": 10,
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
```

#### Foreign Key Constraint Violation
```
IntegrityError: FOREIGN KEY constraint failed
```

**Solution**:
```python
# Always check related objects exist first
workspace = Workspace.query.get(workspace_id)
if not workspace:
    raise ValueError("Workspace not found")

meeting = Meeting(title=title, workspace_id=workspace_id)
```

### Socket.IO Issues

#### Clients Can't Connect
```
Socket.IO connection failed
```

**Solution**:
1. Check CORS settings in `app.py`:
```python
socketio = SocketIO(
    app,
    cors_allowed_origins=['http://localhost:5000', '*.replit.app'],
    async_mode='eventlet'
)
```

2. Verify client connection URL:
```javascript
const socket = io(window.location.origin, {
    transports: ['websocket', 'polling']
});
```

#### Room Broadcasting Not Working
**Solution**:
```python
# Use Redis adapter for multi-worker
socketio = SocketIO(
    app,
    message_queue=os.environ.get('REDIS_URL')
)
```

#### Concurrent Connection Failures (PG-2 Blocker)
```
0/10 concurrent connections succeed
```

**Known Issue**: Single Gunicorn worker limitation

**Workaround**:
```bash
# Use multiple workers with Redis
gunicorn --workers 2 \
         --worker-class eventlet \
         --bind 0.0.0.0:5000 \
         main:app
```

Requires: `REDIS_URL` environment variable set

### Authentication Issues

#### JWT Token Invalid
```
401 Unauthorized: Token has expired
```

**Solution**:
```javascript
// Implement token refresh
if (response.status === 401) {
    const newToken = await refreshToken();
    // Retry request with new token
}
```

#### Session Not Persisting
**Solution**:
```python
# Ensure SESSION_SECRET is set
app.secret_key = os.environ.get("SESSION_SECRET")

# For production, use permanent sessions
session.permanent = True
app.permanent_session_lifetime = timedelta(days=7)
```

### Performance Issues

#### Slow Database Queries
**Diagnosis**:
```python
# Enable query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**Solution**:
```python
# Add missing index
from models import db

# In migration
op.create_index(
    'ix_meeting_workspace_status',
    'meetings',
    ['workspace_id', 'status', 'created_at']
)
```

#### N+1 Query Problem
**Diagnosis**: Multiple queries for related objects

**Solution**:
```python
# Use eager loading
meetings = db.session.query(Meeting).options(
    joinedload(Meeting.organizer),
    joinedload(Meeting.tasks)
).all()
```

#### High Memory Usage
**Solution**:
```python
# Use pagination
from flask_sqlalchemy import Pagination

meetings = db.paginate(
    db.select(Meeting).order_by(Meeting.created_at.desc()),
    page=page,
    per_page=20
)
```

### Transcription Issues

#### OpenAI API Timeout
```
openai.error.Timeout: Request timed out
```

**Solution**:
```python
# In services/whisper_streaming_service.py
client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY'),
    timeout=30.0,  # Increase timeout
    max_retries=3
)
```

#### Audio Quality Poor
**Diagnosis**: Low VAD threshold

**Solution**:
```python
# Adjust VAD sensitivity
vad = webrtcvad.Vad(2)  # 0-3, higher = more aggressive
```

#### Missing Segments
**Solution**:
```python
# Check buffer size
BUFFER_SIZE = 2048  # Increase if segments missing
SAMPLE_RATE = 16000
```

### Redis Issues

#### Redis Connection Failed
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution**:
```python
# Failover manager handles this automatically
# Check logs for fallback status
logger.info("Redis unavailable, using in-memory fallback")
```

#### Redis Memory Limit
```
OOM command not allowed when used memory > 'maxmemory'
```

**Solution**:
```bash
# Configure eviction policy
redis-cli config set maxmemory-policy allkeys-lru
```

### Frontend Issues

#### JavaScript Not Loading
**Solution**:
1. Check browser console for errors
2. Verify static file path:
```html
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
```

3. Clear browser cache

#### AJAX Requests Failing
**Diagnosis**: CSRF token missing

**Solution**:
```javascript
// Add CSRF token to requests
fetch('/api/meetings', {
    method: 'POST',
    headers: {
        'X-CSRFToken': document.querySelector('[name=csrf_token]').value
    },
    body: JSON.stringify(data)
});
```

### Testing Issues

#### Tests Fail in CI but Pass Locally
**Common Cause**: Database state pollution

**Solution**:
```python
@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    db.create_all()
    yield
    # Teardown
    db.session.remove()
    db.drop_all()
```

#### Playwright Browser Not Found
```
Browser executable not found
```

**Solution**:
```bash
# Install Playwright browsers
playwright install chromium

# Or run tests in CI only
pytest -m "not playwright" # Skip Playwright tests locally
```

### Deployment Issues

#### Health Check Failing
**Diagnosis**:
```bash
curl http://localhost:5000/health/detailed
```

**Solution**: Check component status and fix failing service

#### Blue-Green Deployment Smoke Test Fails
**Solution**:
```bash
# Check staging environment
./scripts/blue-green-deploy.sh

# Review smoke test logs
cat /tmp/logs/deployment_smoke_test.log
```

## Debugging Tools

### Logging
```python
# Increase log verbosity
logging.basicConfig(level=logging.DEBUG)

# Log SQL queries
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Database Inspection
```bash
# Connect to database
psql $DATABASE_URL

# List tables
\dt

# Describe table
\d meetings

# Show indexes
\di
```

### Performance Profiling
```python
# Profile endpoint
from werkzeug.middleware.profiler import ProfilerMiddleware

app.wsgi_app = ProfilerMiddleware(app.wsgi_app)
```

### Network Debugging
```bash
# Check server is listening
netstat -tlnp | grep 5000

# Test WebSocket connection
wscat -c ws://localhost:5000/socket.io/?transport=websocket
```

## Getting Help

1. **Check logs**: `/tmp/logs/` or workflow logs
2. **Search docs**: `docs/` directory
3. **Review ADRs**: `docs/adr/` for architectural context
4. **Check issues**: GitHub issues or project tracker
5. **Ask team**: Team chat or forums

## Reporting Bugs

Include in bug reports:
1. **Symptom**: What's happening
2. **Expected**: What should happen
3. **Steps**: How to reproduce
4. **Environment**: OS, Python version, etc.
5. **Logs**: Relevant error messages
6. **Impact**: Severity and affected users
