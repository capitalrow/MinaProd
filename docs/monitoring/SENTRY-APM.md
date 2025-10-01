# Sentry Application Performance Monitoring (APM)

**Phase 0 - Task 0.25**: Performance Monitoring and Profiling

## Overview

Sentry APM provides real-time performance monitoring for Mina, capturing:
- **Transaction timing** (request duration, database queries, API calls)
- **Span tracking** (individual operation timing within transactions)
- **Performance profiling** (CPU, memory, function call traces)
- **Bottleneck identification** (slow queries, external API latency)

**Status**: ✅ **CONFIGURED** (automatically enabled with error tracking)  
**Last Updated**: 2025-10-01

---

## Quick Start

### 1. Enable Performance Monitoring

Sentry APM is **automatically enabled** when you configure Sentry (Task 0.24):

```bash
# Required - from Task 0.24
SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>

# Optional - APM configuration (already set with defaults)
SENTRY_TRACES_SAMPLE_RATE=0.1       # 10% of transactions (recommended)
SENTRY_PROFILES_SAMPLE_RATE=0.1     # 10% profiling sample rate
```

**No additional setup required** - APM is ready to use!

### 2. Test Performance Monitoring

```bash
# Test the performance monitoring endpoint
curl https://your-app.replit.dev/ops/test-sentry-performance

# Expected response:
{
  "status": "success",
  "message": "Performance test completed",
  "operations": [
    {"name": "Database Query", "duration_ms": 87.45},
    {"name": "OpenAI API Call", "duration_ms": 213.67},
    {"name": "Data Processing", "duration_ms": 54.32},
    {"name": "Cache Write", "duration_ms": 21.89}
  ],
  "total_duration_ms": 377.33,
  "check": "Visit Sentry Performance tab to view transaction details"
}
```

### 3. View Performance Data

1. Open Sentry dashboard
2. Navigate to **Performance** tab
3. View transactions, slow operations, and bottlenecks

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Percentage of transactions to capture (0.0 to 1.0) |
| `SENTRY_PROFILES_SAMPLE_RATE` | `0.1` | Percentage of transactions to profile (0.0 to 1.0) |

### Sample Rate Guidelines

**Production (High Traffic)**:
```bash
SENTRY_TRACES_SAMPLE_RATE=0.05      # 5% - balance cost vs visibility
SENTRY_PROFILES_SAMPLE_RATE=0.05
```

**Staging/QA**:
```bash
SENTRY_TRACES_SAMPLE_RATE=0.5       # 50% - more data for testing
SENTRY_PROFILES_SAMPLE_RATE=0.3
```

**Development**:
```bash
SENTRY_TRACES_SAMPLE_RATE=1.0       # 100% - capture everything
SENTRY_PROFILES_SAMPLE_RATE=1.0
```

**Notes:**
- Lower sample rates = lower costs, but may miss rare performance issues
- Higher sample rates = more visibility, but higher Sentry costs
- Profiling has higher overhead than traces alone

---

## Using Transactions

### Automatic Transaction Tracking

Flask routes are **automatically tracked** as transactions:

```python
@app.route('/api/meetings/<meeting_id>')
def get_meeting(meeting_id):
    # This entire request is tracked as a transaction
    meeting = db.session.get(Meeting, meeting_id)
    return jsonify(meeting.to_dict())
```

**Sentry captures:**
- Request URL and method
- Response status code
- Total duration
- Database queries (if using SQLAlchemy)

### Manual Transaction Tracking

Track custom operations as transactions:

```python
import sentry_sdk

# Start a custom transaction
with sentry_sdk.start_transaction(op="task", name="process_transcription"):
    # Your code here
    process_audio(file_path)
    generate_insights(transcript)
    
    # Transaction automatically ends when context exits
```

**Transaction Attributes:**
- `op` (required): Operation type (e.g., "task", "job", "websocket")
- `name` (required): Transaction name (e.g., "process_transcription")
- `description` (optional): Additional context

### Transaction Tags

Add metadata for filtering in Sentry:

```python
with sentry_sdk.start_transaction(op="transcription", name="whisper_api") as transaction:
    # Add tags for filtering
    transaction.set_tag("model", "whisper-1")
    transaction.set_tag("language", "en")
    transaction.set_tag("workspace_id", workspace.id)
    
    # Process transcription
    result = openai.audio.transcriptions.create(...)
```

---

## Using Spans

Spans track **individual operations** within a transaction, helping identify bottlenecks.

### Database Query Spans

```python
import sentry_sdk

with sentry_sdk.start_span(op="db.query", description="Fetch active meetings"):
    meetings = db.session.query(Meeting).filter_by(status="active").all()
```

**Span Attributes:**
- `op`: "db.query" (database operation)
- `description`: SQL query description
- `db.system`: "postgresql" (optional tag)

### HTTP API Call Spans

```python
with sentry_sdk.start_span(op="http.client", description="OpenAI Whisper API") as span:
    span.set_tag("http.method", "POST")
    span.set_tag("service", "openai")
    span.set_data("url", "https://api.openai.com/v1/audio/transcriptions")
    
    response = openai.audio.transcriptions.create(...)
    
    span.set_data("status_code", response.status_code)
```

### Custom Operation Spans

```python
with sentry_sdk.start_span(op="process", description="Generate meeting insights") as span:
    span.set_data("transcript_length", len(transcript))
    span.set_data("model", "gpt-4")
    
    insights = generate_insights(transcript)
    
    span.set_data("insights_generated", len(insights))
```

### Nested Spans

Create hierarchical spans to track sub-operations:

```python
with sentry_sdk.start_transaction(op="meeting", name="create_meeting_with_transcript"):
    
    # Span 1: Save meeting to database
    with sentry_sdk.start_span(op="db.insert", description="Save meeting"):
        db.session.add(meeting)
        db.session.commit()
    
    # Span 2: Upload audio to storage
    with sentry_sdk.start_span(op="storage", description="Upload audio"):
        storage.upload(audio_file)
    
    # Span 3: Process transcription (contains sub-spans)
    with sentry_sdk.start_span(op="ai", description="Process transcription"):
        
        # Sub-span 3a: Call OpenAI API
        with sentry_sdk.start_span(op="http.client", description="OpenAI API"):
            transcript = openai.audio.transcriptions.create(...)
        
        # Sub-span 3b: Post-process results
        with sentry_sdk.start_span(op="process", description="Format transcript"):
            formatted = format_transcript(transcript)
```

---

## Common Span Operations

Use consistent `op` values for better grouping in Sentry:

| Operation | Description | Example |
|-----------|-------------|---------|
| `db.query` | Database SELECT queries | Fetch users, meetings, tasks |
| `db.insert` | Database INSERT operations | Create new records |
| `db.update` | Database UPDATE operations | Modify existing records |
| `db.delete` | Database DELETE operations | Remove records |
| `http.client` | Outbound HTTP API calls | OpenAI, Stripe, Twilio |
| `cache.get` | Cache read operations | Redis GET, Memcached |
| `cache.set` | Cache write operations | Redis SET, Memcached |
| `process` | Data processing/computation | Parsing, formatting, calculations |
| `ai` | AI/ML model operations | Transcription, embeddings, insights |
| `storage` | File storage operations | Upload, download, delete |
| `websocket` | WebSocket operations | Send, receive, broadcast |
| `queue` | Queue operations | Enqueue, dequeue, process |

---

## Real-World Examples

### Example 1: Meeting Creation with Transcription

```python
import sentry_sdk
from flask import request, jsonify

@app.route('/api/meetings', methods=['POST'])
def create_meeting():
    # Automatic transaction: POST /api/meetings
    
    # Span 1: Validate request
    with sentry_sdk.start_span(op="process", description="Validate meeting data"):
        data = request.get_json()
        # Validation logic...
    
    # Span 2: Create meeting in database
    with sentry_sdk.start_span(op="db.insert", description="Create meeting record") as span:
        meeting = Meeting(
            title=data['title'],
            scheduled_at=data['scheduled_at']
        )
        db.session.add(meeting)
        db.session.commit()
        span.set_data("meeting_id", meeting.id)
    
    # Span 3: Upload audio file
    with sentry_sdk.start_span(op="storage", description="Upload audio to S3") as span:
        audio_url = upload_to_s3(data['audio_file'])
        span.set_data("file_size_mb", data['audio_file'].size / 1024 / 1024)
    
    # Span 4: Transcribe audio
    with sentry_sdk.start_span(op="ai", description="Transcribe with Whisper") as span:
        span.set_tag("model", "whisper-1")
        
        with sentry_sdk.start_span(op="http.client", description="OpenAI API call"):
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=data['audio_file']
            )
        
        span.set_data("transcript_length", len(transcript.text))
    
    # Span 5: Generate insights
    with sentry_sdk.start_span(op="ai", description="Generate meeting insights"):
        insights = generate_insights(transcript.text)
    
    # Span 6: Cache results
    with sentry_sdk.start_span(op="cache.set", description="Cache transcript"):
        redis_client.setex(
            f"meeting:{meeting.id}:transcript",
            3600,  # 1 hour TTL
            transcript.text
        )
    
    return jsonify({
        "meeting_id": meeting.id,
        "transcript": transcript.text,
        "insights": insights
    })
```

**Sentry Dashboard View:**
```
Transaction: POST /api/meetings (total: 3.4s)
├─ process: Validate meeting data (12ms)
├─ db.insert: Create meeting record (34ms)
├─ storage: Upload audio to S3 (456ms)
├─ ai: Transcribe with Whisper (2.1s)
│  └─ http.client: OpenAI API call (2.0s)
├─ ai: Generate meeting insights (721ms)
└─ cache.set: Cache transcript (8ms)
```

### Example 2: Background Job Monitoring

```python
import sentry_sdk

def process_daily_analytics():
    """Background job to generate daily analytics."""
    
    # Create transaction for background job
    with sentry_sdk.start_transaction(op="task", name="daily_analytics_job") as transaction:
        transaction.set_tag("job_type", "analytics")
        transaction.set_tag("frequency", "daily")
        
        # Span 1: Fetch data
        with sentry_sdk.start_span(op="db.query", description="Fetch meeting data"):
            meetings = db.session.query(Meeting).filter(
                Meeting.created_at >= datetime.now() - timedelta(days=1)
            ).all()
        
        # Span 2: Calculate metrics
        with sentry_sdk.start_span(op="process", description="Calculate metrics") as span:
            metrics = {
                "total_meetings": len(meetings),
                "total_duration": sum(m.duration for m in meetings),
                "avg_participants": sum(m.participant_count for m in meetings) / len(meetings)
            }
            span.set_data("meetings_processed", len(meetings))
        
        # Span 3: Store results
        with sentry_sdk.start_span(op="db.insert", description="Save analytics"):
            analytics = DailyAnalytics(**metrics)
            db.session.add(analytics)
            db.session.commit()
        
        # Span 4: Send notification
        with sentry_sdk.start_span(op="http.client", description="Send email report"):
            send_email_report(metrics)
        
        transaction.set_data("status", "success")
```

### Example 3: WebSocket Performance Monitoring

```python
import sentry_sdk
from flask_socketio import emit

@socketio.on('audio_chunk', namespace='/transcription')
def handle_audio_chunk(data):
    """Handle incoming audio chunk via WebSocket."""
    
    # Create transaction for WebSocket event
    with sentry_sdk.start_transaction(op="websocket", name="audio_chunk_handler"):
        
        # Span 1: Validate chunk
        with sentry_sdk.start_span(op="process", description="Validate audio chunk"):
            validate_audio_format(data['chunk'])
        
        # Span 2: Buffer audio
        with sentry_sdk.start_span(op="cache.set", description="Buffer audio chunk"):
            session_buffer.add_chunk(data['session_id'], data['chunk'])
        
        # Span 3: Process if buffer full
        if session_buffer.is_ready(data['session_id']):
            with sentry_sdk.start_span(op="ai", description="Process audio buffer"):
                transcript = process_audio_buffer(data['session_id'])
                
                # Emit result to client
                emit('transcription_result', {'text': transcript})
```

---

## Performance Dashboard

### Key Metrics to Monitor

1. **P50 (Median)**: 50% of requests complete in this time
2. **P75**: 75% of requests complete in this time
3. **P95**: 95% of requests complete in this time (SLA target)
4. **P99**: 99% of requests complete in this time (tail latency)

**Example SLA:**
- P95 < 1 second for API endpoints
- P95 < 3 seconds for transcription endpoints

### Alerting on Performance Issues

Configure alerts in Sentry:

**Alert 1: Slow Transactions**
- **Condition**: P95 > 2 seconds
- **Duration**: 5 minutes
- **Action**: Email, Slack

**Alert 2: High Error Rate**
- **Condition**: Error rate > 5%
- **Duration**: 3 minutes
- **Action**: PagerDuty, Email

**Alert 3: Throughput Drop**
- **Condition**: Throughput < 50% of baseline
- **Duration**: 10 minutes
- **Action**: Email, Slack

---

## Profiling

### What is Profiling?

Profiling captures **detailed function-level performance data**:
- Function call stacks
- CPU time per function
- Memory allocation
- Blocking operations

**Difference from Traces:**
- **Traces**: Request-level timing (what happened?)
- **Profiling**: Function-level timing (why was it slow?)

### Enable Profiling

Already enabled via `profiles_sample_rate`:

```python
# In app.py (already configured)
sentry_sdk.init(
    dsn=SENTRY_DSN,
    profiles_sample_rate=0.1,  # 10% of transactions profiled
)
```

### View Profiling Data

1. Open Sentry dashboard
2. Navigate to **Performance** → **Profiles**
3. Select a transaction to view flame graph
4. Identify hot spots (functions consuming most CPU)

**Example Flame Graph:**
```
process_transcription (100%)
├─ openai.audio.transcriptions.create (60%) ← API call is slowest
├─ generate_insights (25%)
│  └─ openai.chat.completions.create (20%)
├─ db.session.commit (10%)
└─ format_response (5%)
```

**Insight**: 60% of time spent waiting for OpenAI API → consider caching or parallel processing.

---

## Best Practices

### 1. Use Descriptive Names

**❌ Bad**:
```python
with sentry_sdk.start_span(op="process"):
    do_stuff()
```

**✅ Good**:
```python
with sentry_sdk.start_span(op="process", description="Parse and validate transcript"):
    parse_transcript(raw_text)
```

### 2. Add Contextual Data

```python
with sentry_sdk.start_span(op="db.query", description="Fetch user meetings") as span:
    span.set_tag("user_id", user.id)
    span.set_data("filter", "last_30_days")
    span.set_data("limit", 100)
    
    meetings = fetch_meetings(user.id, days=30, limit=100)
    
    span.set_data("results_count", len(meetings))
```

### 3. Don't Over-Instrument

**Avoid tracking very fast operations** (< 1ms):

**❌ Overkill**:
```python
with sentry_sdk.start_span(op="process", description="Increment counter"):
    counter += 1  # Too fast to be useful
```

**✅ Better**:
```python
# Just do it - no span needed
counter += 1
```

### 4. Group Similar Operations

Use consistent naming for similar operations:

```python
# Good: All API calls use "http.client" op
with sentry_sdk.start_span(op="http.client", description="OpenAI API"):
    openai_response = call_openai()

with sentry_sdk.start_span(op="http.client", description="Stripe API"):
    stripe_response = call_stripe()
```

### 5. Set Sample Rates Based on Traffic

**Low Traffic (< 1000 req/day)**:
```bash
SENTRY_TRACES_SAMPLE_RATE=1.0  # Capture everything
```

**Medium Traffic (1K-10K req/day)**:
```bash
SENTRY_TRACES_SAMPLE_RATE=0.5  # 50% of requests
```

**High Traffic (> 10K req/day)**:
```bash
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of requests
```

---

## Troubleshooting

### No Performance Data in Sentry

**Check:**
1. Is `SENTRY_DSN` set?
   ```bash
   echo $SENTRY_DSN
   ```

2. Is `SENTRY_TRACES_SAMPLE_RATE` > 0?
   ```bash
   echo $SENTRY_TRACES_SAMPLE_RATE
   ```

3. Check logs for initialization:
   ```
   ✅ Sentry initialized: env=production, release=mina@1.0.0
   ```

4. Test with sample rate = 1.0 (100%):
   ```bash
   export SENTRY_TRACES_SAMPLE_RATE=1.0
   ```

### High Sentry Costs

**Solutions:**
1. Lower sample rates:
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.05  # 5% instead of 10%
   ```

2. Filter noisy endpoints:
   ```python
   # Don't track health checks
   if request.path == '/healthz':
       return  # Skip tracking
   ```

3. Use dynamic sampling:
   ```python
   def traces_sampler(sampling_context):
       # Sample all errors at 100%
       if sampling_context.get("error"):
           return 1.0
       
       # Sample slow requests at higher rate
       if sampling_context.get("duration", 0) > 2.0:
           return 0.5
       
       # Sample fast requests at lower rate
       return 0.05
   
   sentry_sdk.init(
       dsn=SENTRY_DSN,
       traces_sampler=traces_sampler  # Instead of traces_sample_rate
   )
   ```

### Missing Span Data

**Solutions:**
1. Ensure spans are created **within** a transaction:
   ```python
   with sentry_sdk.start_transaction(...):  # Transaction required
       with sentry_sdk.start_span(...):      # Spans go inside
           do_work()
   ```

2. Check that transaction is sampled (not filtered out by sample rate)

---

## Testing

### Test Endpoint

Use the built-in test endpoint:

```bash
# Test performance monitoring
curl https://your-app.replit.dev/ops/test-sentry-performance

# Response includes:
{
  "status": "success",
  "operations": [
    {"name": "Database Query", "duration_ms": 87.45},
    {"name": "OpenAI API Call", "duration_ms": 213.67},
    ...
  ],
  "total_duration_ms": 377.33
}
```

### Verify in Sentry

1. Make a request to the test endpoint
2. Wait 30-60 seconds (Sentry batches data)
3. Open Sentry dashboard → Performance tab
4. Search for transaction: `/ops/test-sentry-performance`
5. Verify spans appear: db.query, http.client, process, cache.set

---

## Integration with OWASP

Sentry APM addresses:

- **A09:2021 - Security Logging and Monitoring Failures**: ✅ Real-time performance monitoring
- **A06:2021 - Vulnerable and Outdated Components**: Identify slow third-party API calls
- **A05:2021 - Security Misconfiguration**: Detect performance degradation after config changes

**Security Control**: ✅ **ACTIVE** (when DSN configured)  
**Coverage**: All Flask routes, background jobs, WebSocket handlers  
**Sample Rate**: 10% (configurable via `SENTRY_TRACES_SAMPLE_RATE`)

---

## References

- [Sentry Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Python APM Guide](https://docs.sentry.io/platforms/python/performance/)
- [Flask Performance Integration](https://docs.sentry.io/platforms/python/guides/flask/performance/)
- [Profiling Documentation](https://docs.sentry.io/product/profiling/)

---

**Last Updated**: 2025-10-01  
**Version**: 1.0  
**Status**: ✅ Configured (ready for use with SENTRY_DSN)
