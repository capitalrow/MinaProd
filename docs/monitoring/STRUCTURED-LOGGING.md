# Structured Logging

**Phase 0 - Task 0.28**: Production-Ready Structured Logging

## Overview

Mina uses **structured logging** (JSON format) for production observability:
- **Parseable logs**: JSON format for easy parsing by log aggregators
- **Rich context**: Request IDs, user IDs, HTTP context, traces
- **Correlation**: Track requests across services with correlation IDs
- **Search & Filter**: Query logs by any field (user_id, request_id, level, etc.)
- **Alerting**: Trigger alerts based on structured fields

**Status**: ✅ **CONFIGURED** (enhanced JSON formatter with comprehensive fields)  
**Last Updated**: 2025-10-01

---

## Quick Start

### 1. Enable JSON Logging

Set environment variable:

```bash
JSON_LOGS=true
```

**Default**: `false` (text format for development)  
**Production**: `true` (JSON format for log aggregation)

### 2. Restart Application

```bash
# Restart to pick up new env var
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### 3. View Structured Logs

```bash
# View logs (JSON format)
tail -f /tmp/logs/Start_application_*.log

# Pretty-print JSON logs
tail -f /tmp/logs/Start_application_*.log | jq '.'
```

---

## Log Format

### Text Format (Development)

When `JSON_LOGS=false` (default):

```
2025-10-01 16:12:05,785 INFO app: Booting Mina…
2025-10-01 16:12:05,786 INFO app: ✅ Flask-Limiter configured (Memory backend): 100/min, 1000/hour per IP
```

**Use Case**: Local development (human-readable)

### JSON Format (Production)

When `JSON_LOGS=true`:

```json
{
  "timestamp": "2025-10-01T16:12:05.785000+00:00",
  "level": "INFO",
  "logger": "app",
  "message": "Booting Mina…",
  "module": "app",
  "function": "create_app",
  "line": 117,
  "process_id": 10177,
  "process_name": "MainProcess",
  "thread_id": 140245896464960,
  "thread_name": "MainThread",
  "hostname": "mina-prod-01",
  "request_id": "a8f5f167-0e5c-4890-a63f-e6e0cd9f7e0a",
  "http": {
    "method": "GET",
    "path": "/api/meetings",
    "ip": "172.31.115.34",
    "user_agent": "Mozilla/5.0..."
  },
  "user": {
    "id": "12345",
    "username": "john.doe"
  }
}
```

**Use Case**: Production (log aggregation, searching, alerting)

---

## Structured Fields

Every log entry includes these fields:

### Standard Fields (Always Present)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | ISO 8601 | UTC timestamp | `"2025-10-01T16:12:05.785000+00:00"` |
| `level` | String | Log level | `"INFO"`, `"ERROR"`, `"WARNING"` |
| `logger` | String | Logger name | `"app"`, `"services.transcription"` |
| `message` | String | Log message | `"Booting Mina…"` |
| `module` | String | Python module | `"app"`, `"routes.auth"` |
| `function` | String | Function name | `"create_app"`, `"login"` |
| `line` | Integer | Line number | `117`, `234` |
| `process_id` | Integer | Process ID | `10177` |
| `process_name` | String | Process name | `"MainProcess"`, `"Worker-1"` |
| `thread_id` | Integer | Thread ID | `140245896464960` |
| `thread_name` | String | Thread name | `"MainThread"`, `"eventlet.wsgi.server"` |
| `hostname` | String | Server hostname | `"mina-prod-01"` |

### Request Context (When Available)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `request_id` | UUID | Correlation ID for request tracing | `"a8f5f167-0e5c-4890-a63f-e6e0cd9f7e0a"` |
| `http.method` | String | HTTP method | `"GET"`, `"POST"` |
| `http.path` | String | URL path | `"/api/meetings"` |
| `http.ip` | String | Client IP address | `"172.31.115.34"` |
| `http.user_agent` | String | User agent (truncated to 200 chars) | `"Mozilla/5.0..."` |

### User Context (When Authenticated)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `user.id` | String | User ID | `"12345"` |
| `user.username` | String | Username | `"john.doe"` |

### Exception Context (When Error)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `exception.type` | String | Exception class name | `"ValueError"`, `"DatabaseError"` |
| `exception.message` | String | Exception message | `"Invalid meeting ID format"` |
| `exception.traceback` | String | Full traceback | `"Traceback (most recent call last)..."` |

### Custom Fields (Optional)

You can add custom fields using `extra={}`:

```python
logger.info("Meeting created", extra={
    "meeting_id": meeting.id,
    "duration_minutes": meeting.duration,
    "participant_count": len(meeting.participants)
})
```

**Output**:
```json
{
  "timestamp": "2025-10-01T16:15:30.123Z",
  "level": "INFO",
  "message": "Meeting created",
  "meeting_id": "abc123",
  "duration_minutes": 45,
  "participant_count": 5
}
```

---

## Usage Examples

### Basic Logging

```python
import logging

logger = logging.getLogger(__name__)

# Info level
logger.info("User logged in successfully")

# Warning level
logger.warning("Rate limit approaching threshold")

# Error level
logger.error("Failed to connect to database")

# Debug level (not shown in production)
logger.debug("Processing chunk 5 of 10")
```

### Logging with Custom Fields

```python
logger.info("Transcription completed", extra={
    "meeting_id": meeting.id,
    "duration_seconds": audio_duration,
    "model": "whisper-1",
    "language": "en",
    "word_count": len(transcript.split()),
    "processing_time_ms": processing_time * 1000
})
```

**Output (JSON)**:
```json
{
  "timestamp": "2025-10-01T16:20:15.456Z",
  "level": "INFO",
  "logger": "services.transcription",
  "message": "Transcription completed",
  "meeting_id": "abc123",
  "duration_seconds": 120,
  "model": "whisper-1",
  "language": "en",
  "word_count": 1543,
  "processing_time_ms": 2345.67
}
```

### Logging Exceptions

```python
try:
    result = process_transcription(audio_file)
except Exception as e:
    logger.error("Transcription failed", exc_info=True, extra={
        "meeting_id": meeting.id,
        "file_size_mb": audio_file.size / 1024 / 1024
    })
    raise
```

**Output (JSON)**:
```json
{
  "timestamp": "2025-10-01T16:25:00.789Z",
  "level": "ERROR",
  "logger": "services.transcription",
  "message": "Transcription failed",
  "meeting_id": "abc123",
  "file_size_mb": 12.5,
  "exception": {
    "type": "OpenAIAPIError",
    "message": "Rate limit exceeded",
    "traceback": "Traceback (most recent call last):\n  File..."
  }
}
```

### Request Context Logging

```python
from flask import request, g

@app.before_request
def before_request():
    # Request ID already set by middleware
    logger.info("Request started")  # Includes request_id, http context automatically
    
@app.route('/api/meetings/<meeting_id>')
def get_meeting(meeting_id):
    logger.info("Fetching meeting", extra={"meeting_id": meeting_id})
    # ...
    return jsonify(meeting.to_dict())
```

**Output (JSON)**:
```json
{
  "timestamp": "2025-10-01T16:30:00.123Z",
  "level": "INFO",
  "logger": "routes.meetings",
  "message": "Fetching meeting",
  "request_id": "a8f5f167-0e5c-4890-a63f-e6e0cd9f7e0a",
  "http": {
    "method": "GET",
    "path": "/api/meetings/abc123",
    "ip": "172.31.115.34",
    "user_agent": "Mozilla/5.0..."
  },
  "user": {
    "id": "12345",
    "username": "john.doe"
  },
  "meeting_id": "abc123"
}
```

### Background Task Logging

```python
def process_daily_analytics():
    """Background job without request context."""
    logger = logging.getLogger("tasks.analytics")
    
    logger.info("Starting daily analytics job", extra={
        "job_type": "analytics",
        "schedule": "daily"
    })
    
    # Process data...
    
    logger.info("Daily analytics completed", extra={
        "meetings_processed": 1543,
        "duration_seconds": 45.2
    })
```

**Output** (no request/user context):
```json
{
  "timestamp": "2025-10-01T02:00:00.000Z",
  "level": "INFO",
  "logger": "tasks.analytics",
  "message": "Starting daily analytics job",
  "job_type": "analytics",
  "schedule": "daily"
}
```

---

## Log Levels

Use appropriate log levels for different scenarios:

### DEBUG
**When**: Detailed diagnostic information  
**Example**: "Processing audio chunk 5/10", "Cache hit for key: meeting:abc123"  
**Production**: Usually disabled (too verbose)

```python
logger.debug("Processing audio chunk", extra={"chunk_id": 5, "total_chunks": 10})
```

### INFO
**When**: General informational messages  
**Example**: "User logged in", "Transcription completed", "Meeting created"  
**Production**: Enabled (default level)

```python
logger.info("Meeting created successfully", extra={"meeting_id": meeting.id})
```

### WARNING
**When**: Something unexpected but not critical  
**Example**: "Rate limit approaching", "Slow query detected", "Retrying failed API call"  
**Production**: Enabled (investigate but not urgent)

```python
logger.warning("OpenAI API slow response", extra={
    "endpoint": "/v1/audio/transcriptions",
    "latency_ms": 5432
})
```

### ERROR
**When**: Errors that need attention  
**Example**: "Database connection failed", "API call failed", "Transcription failed"  
**Production**: Enabled (requires investigation)

```python
logger.error("Failed to save meeting to database", exc_info=True, extra={
    "meeting_id": meeting.id
})
```

### CRITICAL
**When**: Severe errors causing system failure  
**Example**: "Database unreachable", "Out of memory", "Security breach detected"  
**Production**: Enabled (immediate action required)

```python
logger.critical("Database cluster unreachable", exc_info=True, extra={
    "cluster": "production",
    "down_since": start_time
})
```

---

## Log Aggregation

### Why Log Aggregation?

**Without Aggregation**:
- Logs scattered across multiple servers
- Hard to search across servers
- No centralized analysis
- Manual SSH to view logs

**With Aggregation**:
- Centralized log storage
- Fast search across all servers
- Real-time dashboards
- Alerts on log patterns

### Recommended Services

| Service | Free Tier | Price | Best For |
|---------|-----------|-------|----------|
| **Datadog** | 14-day trial | $15/host/month | Enterprise, APM integration |
| **New Relic** | 100GB/month | $0.30/GB | Application monitoring |
| **Logtail** | 1GB/month | $7/month | Simple setup, good UX |
| **Papertrail** | 50MB/day | $7/month | Quick setup, search |
| **Logz.io** | 1GB/day | $89/month | ELK stack (Elasticsearch) |
| **CloudWatch** | 5GB/month | $0.50/GB | AWS integration |
| **Grafana Loki** | Self-hosted | Free | Prometheus/Grafana stack |

**Recommendation**: **Logtail** (easy setup, generous free tier)

### Setup with Logtail

1. Sign up at [logtail.com](https://logtail.com)

2. Create source:
   - **Source Type**: HTTP
   - **Name**: Mina Production
   - Copy source token: `<YOUR_SOURCE_TOKEN>`

3. Install Logtail agent (optional) OR ship logs via HTTP:

   **Option A: Logtail Agent (Recommended)**
   ```bash
   # Install Logtail Vector agent
   curl -sSL https://logtail.com/install | bash
   
   # Configure source
   logtail sources add \
     --token <YOUR_SOURCE_TOKEN> \
     --path /tmp/logs/Start_application_*.log
   ```

   **Option B: Ship logs via HTTP**
   ```python
   # In app.py, add HTTPHandler
   import logging.handlers
   
   if JSON_LOGS:
       http_handler = logging.handlers.HTTPHandler(
           host="logs.logtail.com",
           url="/sources/<YOUR_SOURCE_TOKEN>",
           method="POST"
       )
       root.addHandler(http_handler)
   ```

4. View logs in Logtail dashboard:
   - Search: `level:ERROR`
   - Filter: `user.id:12345`
   - Alert: Create alert on `level:CRITICAL`

### Setup with Datadog

1. Sign up at [datadoghq.com](https://www.datadoghq.com)

2. Install Datadog Agent:
   ```bash
   DD_API_KEY=<YOUR_API_KEY> bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"
   ```

3. Configure log collection:
   ```yaml
   # /etc/datadog-agent/conf.d/mina.d/conf.yaml
   logs:
     - type: file
       path: /tmp/logs/Start_application_*.log
       service: mina
       source: python
       tags:
         - env:production
   ```

4. Restart agent:
   ```bash
   sudo systemctl restart datadog-agent
   ```

---

## Searching & Filtering Logs

### By Log Level

```bash
# All errors
jq 'select(.level == "ERROR")' logs.json

# Errors and warnings
jq 'select(.level == "ERROR" or .level == "WARNING")' logs.json
```

### By User

```bash
# All logs for specific user
jq 'select(.user.id == "12345")' logs.json

# All actions by user
jq 'select(.user.username == "john.doe") | {timestamp, message, http}' logs.json
```

### By Request

```bash
# All logs for specific request
jq 'select(.request_id == "a8f5f167-0e5c-4890-a63f-e6e0cd9f7e0a")' logs.json

# Request timeline
jq 'select(.request_id == "a8f5f167-0e5c-4890-a63f-e6e0cd9f7e0a") | {timestamp, logger, message}' logs.json
```

### By Custom Field

```bash
# All logs for specific meeting
jq 'select(.meeting_id == "abc123")' logs.json

# Transcriptions longer than 2 minutes
jq 'select(.duration_seconds > 120) | {timestamp, meeting_id, duration_seconds}' logs.json
```

### Time Range

```bash
# Logs in last hour
jq 'select(.timestamp > "2025-10-01T15:00:00Z")' logs.json

# Logs between timestamps
jq 'select(.timestamp >= "2025-10-01T15:00:00Z" and .timestamp <= "2025-10-01T16:00:00Z")' logs.json
```

---

## Alerting on Logs

### Alert Conditions

**Example Alerts:**

1. **High Error Rate**
   - Condition: > 10 ERROR logs in 5 minutes
   - Action: Email engineering team

2. **Critical Errors**
   - Condition: Any CRITICAL log
   - Action: Page on-call engineer

3. **Slow API Calls**
   - Condition: `processing_time_ms > 5000` in 3 consecutive logs
   - Action: Slack #alerts channel

4. **Authentication Failures**
   - Condition: > 5 "Login failed" logs from same IP in 1 minute
   - Action: Block IP, alert security team

### Setup in Logtail

```yaml
# Alert: High error rate
name: High Error Rate
query: level:ERROR
condition: count > 10
window: 5 minutes
actions:
  - type: email
    recipients: [engineering@company.com]
```

### Setup in Datadog

```yaml
# Alert: Critical errors
name: Critical Errors Detected
query: logs("level:CRITICAL")
condition: count > 0
window: 1 minute
actions:
  - type: pagerduty
    service: mina-production
```

---

## Best Practices

### 1. Use Structured Fields

**❌ Bad** (unstructured):
```python
logger.info(f"Meeting {meeting.id} created by user {user.id} with {len(participants)} participants")
```

**✅ Good** (structured):
```python
logger.info("Meeting created", extra={
    "meeting_id": meeting.id,
    "user_id": user.id,
    "participant_count": len(participants)
})
```

**Why**: Structured fields are searchable and filterable.

### 2. Include Context

Always include relevant IDs and context:

```python
logger.info("Transcription started", extra={
    "meeting_id": meeting.id,
    "user_id": current_user.id,
    "model": "whisper-1",
    "language": "en",
    "duration_seconds": audio.duration
})
```

### 3. Log at Boundaries

Log at system boundaries (API calls, database queries, external services):

```python
# Before external API call
logger.info("Calling OpenAI API", extra={
    "endpoint": "/v1/audio/transcriptions",
    "model": "whisper-1"
})

# After external API call
logger.info("OpenAI API response received", extra={
    "latency_ms": latency,
    "status_code": response.status_code
})
```

### 4. Don't Log Sensitive Data

**Never log**:
- Passwords
- API keys / tokens
- Credit card numbers
- Social security numbers
- Personal health information

**❌ Bad**:
```python
logger.info(f"User logged in with password: {password}")
```

**✅ Good**:
```python
logger.info("User logged in successfully", extra={"user_id": user.id})
```

### 5. Use Consistent Field Names

Standardize field names across the application:

```python
# Good: Consistent naming
logger.info("Event", extra={"meeting_id": "abc123", "user_id": "12345"})

# Bad: Inconsistent naming
logger.info("Event", extra={"meetingId": "abc123", "userId": "12345"})  # camelCase
logger.info("Event", extra={"meeting_id": "abc123", "user_id": "12345"})  # snake_case
```

### 6. Log Performance Metrics

Track performance at key operations:

```python
import time

start = time.time()
transcript = openai.audio.transcriptions.create(...)
latency = (time.time() - start) * 1000

logger.info("Transcription completed", extra={
    "meeting_id": meeting.id,
    "duration_seconds": audio.duration,
    "processing_time_ms": latency,
    "words_per_second": word_count / audio.duration
})
```

---

## Integration with Sentry

Sentry automatically captures logs as breadcrumbs:

**INFO+ logs** → Breadcrumbs (context for errors)  
**ERROR+ logs** → Events (alerts)

```python
# This log becomes a breadcrumb in Sentry
logger.info("Starting transcription", extra={"meeting_id": meeting.id})

# If error occurs, Sentry captures breadcrumbs + error
logger.error("Transcription failed", exc_info=True, extra={"meeting_id": meeting.id})
```

**View in Sentry**:
1. Open error in Sentry dashboard
2. Scroll to "Breadcrumbs" section
3. See timeline of events leading to error

---

## Troubleshooting

### Logs Not in JSON Format

**Problem**: Logs still in text format despite `JSON_LOGS=true`.

**Solution**:
1. Verify env var is set:
   ```bash
   echo $JSON_LOGS
   ```

2. Restart application to pick up env var change

3. Check `Config.JSON_LOGS` in code

### Missing Request Context

**Problem**: `request_id`, `http`, `user` fields missing from logs.

**Solution**:
- Request context only available within Flask request context
- Background tasks/jobs won't have request context (expected)
- Ensure middleware is setting `g.request_id`

### Logs Too Verbose

**Problem**: Too many DEBUG logs in production.

**Solution**:
Change log level to INFO:

```python
# In app.py
root.setLevel(logging.INFO)  # Only INFO and above
```

---

## OWASP Compliance

Structured logging addresses:

- **A09:2021 - Security Logging and Monitoring Failures**: ✅ Comprehensive logging with correlation IDs
- **A01:2021 - Broken Access Control**: Track access attempts with user/resource IDs
- **A07:2021 - Identification and Authentication Failures**: Log authentication events

**Security Control**: ✅ **ACTIVE** (JSON logging with full context)  
**Coverage**: All Flask routes, services, background tasks  
**Retention**: Configurable by log aggregation service (30-90 days typical)

---

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structured Logging Best Practices](https://www.loggly.com/ultimate-guide/python-logging-basics/)
- [Datadog Log Collection](https://docs.datadoghq.com/logs/)
- [Logtail Documentation](https://logtail.com/docs/)

---

**Last Updated**: 2025-10-01  
**Version**: 1.0  
**Status**: ✅ JSON formatter implemented, log aggregation setup recommended
