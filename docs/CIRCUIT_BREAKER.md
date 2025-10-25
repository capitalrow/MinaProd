# Circuit Breaker Pattern - Wave 0-10

## Overview

Mina implements the Circuit Breaker pattern to prevent cascading failures when upstream services (OpenAI, Anthropic, etc.) experience outages. The circuit breaker automatically:

1. **Tracks failures** - Monitors API call success/failure rates
2. **Opens circuit** - Blocks requests after threshold failures (default: 3 consecutive failures)
3. **Attempts recovery** - Tests service availability after timeout (default: 30s)
4. **Closes circuit** - Resumes normal operation after successful recovery
5. **Sends alerts** - Notifies team via Slack when circuit opens

## Architecture

```
┌─────────────────┐
│   Application   │
└────────┬────────┘
         │
         v
┌────────────────────────┐
│  Circuit Breaker       │
│  (Redis-backed state)  │
└────────┬───────────────┘
         │
         ├─ CLOSED ──> Allow requests (normal operation)
         │
         ├─ OPEN ────> Block requests (service down)
         │             └─> Send Slack alert
         │
         └─ HALF_OPEN -> Test recovery (limited requests)
```

## State Machine

- **CLOSED** → Normal operation, all requests allowed
- **OPEN** → Service unavailable, requests blocked immediately
- **HALF_OPEN** → Testing recovery, limited requests allowed

**Transitions:**
- CLOSED → OPEN: After N consecutive failures (default: 3)
- OPEN → HALF_OPEN: After timeout expires (default: 30s)
- HALF_OPEN → CLOSED: After successful request
- HALF_OPEN → OPEN: After failed request

## Protected Services

### OpenAI Transcription
- **Service Name**: `openai_transcription`
- **Failure Threshold**: 3 consecutive failures
- **Recovery Timeout**: 30 seconds
- **Success Threshold**: 2 consecutive successes
- **Protected Methods**:
  - `openai_client_manager.transcribe_audio()` (sync)
  - `openai_client_manager.transcribe_audio_async()` (async)
  - `openai_whisper_client.transcribe_bytes()` (WebSocket streaming)

## Redis State

Circuit breaker state is shared across all Gunicorn workers via Redis:

```
circuit_breaker:openai_transcription:state → "closed" | "open" | "half_open"
circuit_breaker:openai_transcription:failures → 0-N (failure count)
circuit_breaker:openai_transcription:last_failure_time → timestamp
circuit_breaker:openai_transcription:metrics → JSON (success/failure stats)
circuit_breaker:openai_transcription:history → List (last 100 events)
```

## Usage Examples

### 1. Automatic Protection (Existing Code)

All OpenAI transcription calls are automatically protected:

```python
# Already protected - no changes needed
from services.openai_client_manager import openai_manager

# This call is automatically protected by circuit breaker
text = openai_manager.transcribe_audio(audio_file, model="whisper-1")

# If circuit is OPEN, returns None instead of calling OpenAI
# Logs: "🚨 OpenAI circuit breaker is OPEN, blocking transcription request"
```

### 2. Manual Circuit Breaker Usage

For new services:

```python
from services.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

# Create circuit breaker
config = CircuitBreakerConfig(
    failure_threshold=5,    # Open after 5 failures
    recovery_timeout=60,    # Wait 60s before recovery
    success_threshold=3,    # Close after 3 successes
    request_timeout=30      # 30s timeout
)
cb = CircuitBreaker("my_service", config)

# Method 1: Context manager (recommended)
try:
    with cb:
        result = external_api_call()
except CircuitBreakerOpenError:
    # Circuit is OPEN, service unavailable
    return fallback_response()

# Method 2: Manual control
if cb.can_execute():
    try:
        result = external_api_call()
        cb.record_success()
    except Exception as e:
        cb.record_failure(e)
        raise
else:
    # Circuit is OPEN
    return fallback_response()
```

### 3. Decorator Pattern

```python
from services.circuit_breaker import CircuitBreaker

cb = CircuitBreaker("anthropic_api")

@cb
def call_anthropic_api(prompt: str) -> str:
    return anthropic.completion.create(prompt=prompt)

# Circuit breaker automatically wraps the function
result = call_anthropic_api("Hello")
```

## Monitoring

### Check Circuit Breaker Status

```python
from services.circuit_breaker import get_all_circuit_breakers

# Get all circuit breakers
breakers = get_all_circuit_breakers()

for cb in breakers:
    print(f"{cb['name']}: {cb['state']}")
    print(f"  Failures: {cb['current_failures']}/{cb['failure_threshold']}")
    print(f"  Success Rate: {cb['success_rate']:.1f}%")
    print(f"  Last Error: {cb['last_failure_error']}")
```

### View History

```python
from services.circuit_breaker import CircuitBreaker

cb = CircuitBreaker("openai_transcription")
history = cb.get_history(limit=10)

for event in history:
    print(f"{event['timestamp']}: {event['event']}")
```

### Manual Reset

```python
cb = CircuitBreaker("openai_transcription")
cb.reset()  # Force circuit to CLOSED state
```

## Slack Alerts

When a circuit breaker opens (service goes down), an automatic Slack alert is sent:

```
🚨 Circuit Breaker Alert: openai_transcription

Service:     openai_transcription
State:       OPEN
Failures:    3
Recovery In: 30s

Last Error:
```
OpenAI API error: Connection timeout
```

⏰ Alert Time: 2025-10-25 11:30:00 UTC
```

**Configuration:**
- Set `SLACK_WEBHOOK_URL` environment variable
- Alerts sent automatically when circuit opens
- No additional configuration needed

## Fallback Strategies

When circuit is OPEN, implement graceful degradation:

### 1. Return Empty Results
```python
text = openai_manager.transcribe_audio(audio)
if not text:
    # Circuit may be OPEN, return empty transcript
    return ""
```

### 2. Queue for Later
```python
if not cb.can_execute():
    # Queue audio for later transcription
    transcription_queue.add(audio_file, user_id)
    return {"status": "queued", "message": "Service temporarily unavailable"}
```

### 3. Use Alternative Service
```python
if not cb.can_execute():
    # Fallback to alternative transcription service
    return backup_transcription_service.transcribe(audio)
```

## Performance Impact

- **Redis overhead**: ~1-2ms per request (state check + metrics update)
- **Memory overhead**: ~10KB per circuit breaker in Redis
- **Network overhead**: Minimal (Redis local or same datacenter)
- **CPU overhead**: Negligible (simple state machine logic)

**Result**: Circuit breaker adds <2ms latency, prevents minutes/hours of cascading failures.

## Configuration

### Environment Variables

- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379/0`)
- `SLACK_WEBHOOK_URL`: Slack webhook for alerts (optional)

### Circuit Breaker Parameters

```python
CircuitBreakerConfig(
    failure_threshold=3,     # Failures before opening circuit
    recovery_timeout=30,     # Seconds before retry
    success_threshold=2,     # Successes before closing circuit
    request_timeout=45       # Request timeout (seconds)
)
```

## Troubleshooting

### Problem: Circuit keeps opening

**Cause**: Upstream service genuinely down or experiencing issues

**Solution**:
1. Check OpenAI status: https://status.openai.com
2. Verify API key is valid: `OPENAI_API_KEY`
3. Check network connectivity to OpenAI servers
4. Review Slack alerts for error details

### Problem: Circuit doesn't open despite failures

**Cause**: Failures not reaching threshold or circuit breaker not initialized

**Solution**:
1. Check logs for circuit breaker initialization: "🔒 Circuit Breaker service initialized"
2. Verify failure threshold is reasonable (default: 3)
3. Check Redis connectivity
4. Ensure failures are being recorded (check logs for "❌ Circuit breaker recorded failure")

### Problem: Circuit stuck OPEN

**Cause**: Recovery timeout too long or service still failing

**Solution**:
1. Manually reset circuit: `cb.reset()`
2. Check service is actually recovered
3. Reduce `recovery_timeout` if needed
4. Check recovery logs: "🔄 Circuit breaker timeout expired, entering HALF_OPEN"

## Production Deployment

### Health Checks

Add circuit breaker health to monitoring:

```python
@app.route('/health')
def health_check():
    breakers = get_all_circuit_breakers()
    open_breakers = [b for b in breakers if b['state'] == 'open']
    
    if open_breakers:
        return jsonify({
            'status': 'degraded',
            'open_circuits': [b['name'] for b in open_breakers]
        }), 503
    
    return jsonify({'status': 'healthy'}), 200
```

### Prometheus Metrics (Future)

Metrics already tracked in Redis, can be exposed via `/metrics` endpoint:

- `circuit_breaker_state{service="openai_transcription"}` → 0 (closed), 1 (open), 2 (half_open)
- `circuit_breaker_failures{service="openai_transcription"}` → current failure count
- `circuit_breaker_total_requests{service="openai_transcription"}` → total requests
- `circuit_breaker_success_rate{service="openai_transcription"}` → success percentage

## See Also

- [Deployment Playbook](./DEPLOYMENT_PLAYBOOK.md) - Production deployment procedures
- [Staging Environment](./STAGING_ENVIRONMENT.md) - Testing circuit breaker in staging
- [Row-Level Security](./ROW_LEVEL_SECURITY.md) - Database security layer
