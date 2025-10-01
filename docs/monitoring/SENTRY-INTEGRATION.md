# Sentry Integration - Error Tracking & Monitoring

**Phase 0 - Task 0.24**: Production Error Tracking with Sentry

## Overview

Mina uses **Sentry** (sentry-sdk v2.39.0) for real-time error tracking, performance monitoring, and production debugging. Sentry automatically captures exceptions, logs, and performance data to help identify and fix issues quickly.

**Status**: ✅ **INTEGRATED** (awaiting DSN configuration)  
**Last Updated**: 2025-10-01

---

## Quick Start

### 1. Create Sentry Project

Sign up at [sentry.io](https://sentry.io) and create a new project:
- **Platform**: Flask / Python
- **Project Name**: mina-transcription-prod (or similar)
- Copy the DSN (Data Source Name) URL

### 2. Configure Environment Variables

Add to Replit Secrets (or `.env` for local):

```bash
# Required
SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>

# Optional (recommended)
SENTRY_ENVIRONMENT=production        # development, staging, production
SENTRY_RELEASE=mina@1.0.0           # Version/build ID
SENTRY_TRACES_SAMPLE_RATE=0.1       # 10% of transactions (performance monitoring)
SENTRY_PROFILES_SAMPLE_RATE=0.1     # 10% profiling sample rate
```

### 3. Restart Application

```bash
# Restart to pick up new env vars
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### 4. Test Error Tracking

```bash
# Trigger a test error
curl https://your-app.replit.dev/api/test-sentry-error

# Check Sentry dashboard for the error
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | **Yes** | None | Sentry project DSN URL (from project settings) |
| `SENTRY_ENVIRONMENT` | No | `development` | Environment name (`development`, `staging`, `production`) |
| `SENTRY_RELEASE` | No | `mina@unknown` | Release version (e.g., `mina@1.2.3`, git SHA) |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `0.1` | Performance monitoring sample rate (0.0 to 1.0) |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | `0.1` | Profiling sample rate (0.0 to 1.0) |

**Notes:**
- `SENTRY_DSN` must be set for Sentry to activate
- Sample rates control cost vs visibility tradeoff
- Higher sample rates = more data but higher costs

---

## Features

### 1. Automatic Exception Capture

All unhandled exceptions are automatically captured and sent to Sentry:

```python
# This error will be captured automatically
raise ValueError("Something went wrong!")
```

**Includes:**
- Full stack trace
- Request context (URL, headers, user agent)
- User information (if authenticated)
- Environment details (Python version, OS, etc.)

### 2. Manual Error Reporting

Capture custom errors or warnings:

```python
import sentry_sdk

# Capture an exception
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)

# Capture a message
sentry_sdk.capture_message("User exceeded rate limit", level="warning")
```

### 3. User Context

Associate errors with specific users:

```python
from flask_login import current_user
import sentry_sdk

# Set user context for all subsequent errors
sentry_sdk.set_user({
    "id": current_user.id,
    "username": current_user.username,
    "email": current_user.email
})
```

### 4. Custom Tags & Context

Add structured metadata to errors:

```python
import sentry_sdk

# Add tags for filtering in Sentry
sentry_sdk.set_tag("meeting_id", meeting.id)
sentry_sdk.set_tag("transcription_model", "whisper-1")

# Add extra context
sentry_sdk.set_context("meeting", {
    "duration": meeting.duration,
    "participants": meeting.participant_count,
    "quality": meeting.audio_quality
})
```

### 5. Breadcrumbs

Sentry automatically captures breadcrumbs (log messages, HTTP requests, etc.):

```python
import logging

# These become breadcrumbs in Sentry
logging.info("User started transcription")
logging.debug(f"Processing audio chunk: {chunk_id}")
```

### 6. Performance Monitoring

Track transaction performance:

```python
import sentry_sdk

# Start a transaction
with sentry_sdk.start_transaction(op="transcription", name="process_audio"):
    # Your code here
    transcribe_audio(file)
    
    # Add a span for a specific operation
    with sentry_sdk.start_span(op="ai", description="OpenAI Whisper API call"):
        result = openai_client.audio.transcriptions.create(...)
```

---

## Security & Privacy

### 1. PII Protection

Sentry is configured with `send_default_pii=False`:
- Does NOT send user passwords
- Does NOT send auth tokens
- Does NOT send request bodies by default

### 2. Data Sanitization

Custom `before_send` filter redacts sensitive data:

```python
def _sentry_before_send(event, hint):
    # Redact sensitive keys from request data
    sensitive_keys = ['password', 'token', 'api_key', 'secret', 'authorization']
    
    if 'request' in event and 'data' in event['request']:
        for key in sensitive_keys:
            if key in event['request']['data']:
                event['request']['data'][key] = '[REDACTED]'
    
    return event
```

### 3. Filtered Exceptions

Common non-critical exceptions are filtered out:
- `NotFound` (HTTP 404) - Too noisy
- `Unauthorized` (HTTP 401) - Expected behavior
- `Forbidden` (HTTP 403) - Access control working correctly

---

## Integration Details

### Flask Integration

Sentry integrates with Flask to capture:
- **Uncaught exceptions** in route handlers
- **Request context** (URL, method, headers)
- **User information** (via Flask-Login)
- **Performance data** (response times, database queries)

```python
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FlaskIntegration()],
    # ... other config
)
```

### Logging Integration

Captures log messages as breadcrumbs and events:
- **INFO and above** → Breadcrumbs (context)
- **ERROR and above** → Events (alerts)

```python
from sentry_sdk.integrations.logging import LoggingIntegration

LoggingIntegration(
    level=logging.INFO,         # Breadcrumb level
    event_level=logging.ERROR   # Event level
)
```

---

## Sentry Dashboard

### Issues Tab

View all captured errors:
- **Stack traces** with code context
- **Frequency graphs** (errors over time)
- **User impact** (how many users affected)
- **First/last seen** timestamps

**Actions:**
- Mark as resolved
- Assign to team member
- Ignore future occurrences
- Create GitHub/Jira issue

### Performance Tab

Monitor application performance:
- **Transaction duration** (P50, P75, P95, P99)
- **Throughput** (requests per second)
- **Apdex score** (application performance index)
- **Slow transactions** (identify bottlenecks)

### Releases Tab

Track errors by release version:
- **Error rate** per release
- **New issues** introduced
- **Regression detection**
- **Deployment tracking**

---

## Alerting

Configure alerts in Sentry dashboard:

### 1. Error Rate Alert

Trigger when error rate exceeds threshold:
- **Condition**: Error count > 100 in 1 hour
- **Actions**: Email, Slack, PagerDuty

### 2. New Issue Alert

Notify on new error types:
- **Condition**: First time seen
- **Actions**: Email, Slack

### 3. Regression Alert

Alert when resolved issue reappears:
- **Condition**: Issue reopened
- **Actions**: Email, Slack, assign to owner

### 4. Performance Alert

Monitor transaction performance:
- **Condition**: P95 response time > 2 seconds
- **Actions**: Email, Slack

---

## Best Practices

### 1. Use Descriptive Error Messages

**❌ Bad**:
```python
raise ValueError("Error")
```

**✅ Good**:
```python
raise ValueError(f"Invalid meeting ID: {meeting_id}. Expected format: UUID v4.")
```

### 2. Add Context to Errors

```python
try:
    process_transcription(meeting_id)
except Exception as e:
    sentry_sdk.set_context("transcription", {
        "meeting_id": meeting_id,
        "audio_format": audio.format,
        "duration_seconds": audio.duration
    })
    sentry_sdk.capture_exception(e)
    raise
```

### 3. Use Transactions for Performance

```python
with sentry_sdk.start_transaction(op="meeting", name="create_meeting"):
    meeting = create_meeting(data)
    
    with sentry_sdk.start_span(op="db", description="save to database"):
        db.session.add(meeting)
        db.session.commit()
    
    with sentry_sdk.start_span(op="ai", description="generate insights"):
        insights = generate_insights(meeting)
```

### 4. Set User Context Early

```python
@app.before_request
def set_sentry_user():
    if current_user.is_authenticated:
        sentry_sdk.set_user({
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        })
```

### 5. Tag Errors for Filtering

```python
# Tag by feature
sentry_sdk.set_tag("feature", "transcription")

# Tag by severity
sentry_sdk.set_tag("severity", "critical")

# Tag by customer
sentry_sdk.set_tag("workspace_id", workspace.id)
```

---

## Cost Optimization

### 1. Adjust Sample Rates

Lower sample rates reduce events sent to Sentry:

```bash
# Send 10% of transactions (recommended for production)
SENTRY_TRACES_SAMPLE_RATE=0.1

# Send 5% for high-traffic apps
SENTRY_TRACES_SAMPLE_RATE=0.05

# Send 100% for staging (full visibility)
SENTRY_TRACES_SAMPLE_RATE=1.0
```

### 2. Filter Noisy Errors

Update `_sentry_before_send()` to ignore common errors:

```python
def _sentry_before_send(event, hint):
    # Ignore specific error types
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, (NotFound, RateLimitExceeded)):
            return None  # Don't send to Sentry
    
    return event
```

### 3. Use Environments Wisely

Only monitor production and staging:

```bash
# Production
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Staging
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.5

# Development (disable)
# Don't set SENTRY_DSN in development
```

---

## Troubleshooting

### Sentry Not Capturing Errors

**Check:**
1. Is `SENTRY_DSN` set?
   ```bash
   echo $SENTRY_DSN
   ```

2. Check logs for initialization message:
   ```
   ✅ Sentry initialized: env=production, release=mina@1.0.0
   ```

3. Test with a manual error:
   ```python
   import sentry_sdk
   sentry_sdk.capture_message("Test message", level="info")
   ```

### High Event Volume

**Solutions:**
1. Lower sample rates:
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.05  # 5% instead of 10%
   ```

2. Filter noisy errors in `_sentry_before_send()`

3. Use Sentry's "Ignore" feature for specific errors

### Missing Context

**Solutions:**
1. Add more breadcrumbs:
   ```python
   logging.info(f"Processing meeting: {meeting_id}")
   ```

2. Set custom context:
   ```python
   sentry_sdk.set_context("operation", {
       "type": "transcription",
       "duration": duration
   })
   ```

---

## OWASP Compliance

This Sentry integration addresses:

- **A09:2021 - Security Logging and Monitoring Failures**: ✅ Real-time error tracking
- **A06:2021 - Vulnerable and Outdated Components**: Helps identify library issues
- **A04:2021 - Insecure Design**: Performance monitoring reveals design flaws

**Security Control**: ✅ **ACTIVE** (when DSN configured)  
**Coverage**: All Flask routes, background tasks, scheduled jobs  
**Retention**: 90 days (Sentry default)

---

## Testing

### Manual Test

Create a test route to trigger errors:

```python
@app.route('/api/test-sentry-error')
def test_sentry():
    sentry_sdk.capture_message("Test message from Mina", level="info")
    
    try:
        1 / 0  # Intentional error
    except Exception as e:
        sentry_sdk.capture_exception(e)
    
    return jsonify({"status": "error sent to Sentry"})
```

### Verify in Dashboard

1. Visit Sentry dashboard
2. Check "Issues" tab
3. Should see new ZeroDivisionError
4. Verify breadcrumbs and context

---

## References

- [Sentry Python SDK Documentation](https://docs.sentry.io/platforms/python/)
- [Flask Integration Guide](https://docs.sentry.io/platforms/python/guides/flask/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Best Practices](https://docs.sentry.io/product/best-practices/)

---

**Last Updated**: 2025-10-01  
**Version**: 1.0  
**Status**: ✅ Integrated (awaiting DSN configuration)
