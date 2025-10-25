# Rate Limiting - Wave 0-14

## Overview

Mina implements comprehensive, multi-layer rate limiting to prevent abuse, ensure fair resource allocation, and protect infrastructure from DDoS attacks. The system uses **defense-in-depth** with two complementary rate limiters:

1. **Flask-Limiter** - Global baseline protection (always active)
2. **DistributedRateLimiter** - Advanced features (Redis-backed, sliding window)

## Architecture

```
┌─────────────────┐
│   Client        │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  Flask-Limiter          │  ← Layer 1: Fixed-window global limits
│  100/min, 1000/hour     │
└────────┬────────────────┘
         │ (if allowed)
         v
┌──────────────────────────┐
│ DistributedRateLimiter   │  ← Layer 2: Sliding window, per-endpoint
│ (Redis-backed)           │     - Burst protection
│                          │     - Progressive backoff
│                          │     - Whitelist/blacklist
│                          │     - Slack abuse alerts
└────────┬─────────────────┘
         │ (if allowed)
         v
    Application
```

## Layer 1: Flask-Limiter (Baseline Protection)

**Configuration** (app.py):
- **Global limits**: 100 requests/minute, 1000 requests/hour per IP
- **Strategy**: Fixed-window (simpler, more performant)
- **Backend**: Redis (if available) or in-memory fallback
- **Headers**: Includes `X-RateLimit-*` headers in responses
- **Error handling**: Swallows errors to prevent cascading failures

**Always Active**: Flask-Limiter provides baseline protection even when Redis is unavailable.

## Layer 2: DistributedRateLimiter (Advanced Protection)

**Active When**: `REDIS_URL` environment variable is set

**Features**:
1. **Sliding Window Algorithm** - More accurate than fixed-window
2. **Per-Endpoint Limits** - Different limits for different APIs
3. **Burst Protection** - Max 10 requests/second
4. **Progressive Backoff** - Exponential backoff after violations
5. **Whitelist/Blacklist** - Manual IP/user exemptions or blocks
6. **Slack Alerts** - Automatic alerts for abuse patterns (≥5 violations)

## Endpoint-Specific Limits

| Endpoint                      | Limit           | Window | Notes                          |
|-------------------------------|-----------------|--------|--------------------------------|
| `/auth/login`                 | 5 requests      | 1 min  | Prevent brute-force attacks    |
| `/auth/register`              | 5 requests      | 1 min  | Prevent account spam           |
| `/api/transcribe`             | 20 requests     | 1 min  | Protect OpenAI API quota       |
| `/api/upload`                 | 50 requests     | 1 hour | Prevent storage abuse          |
| `/socket.io/*` (WebSocket)    | 300 messages    | 1 min  | Prevent WebSocket flooding     |
| **Default** (all other routes)| 100 requests    | 1 min  | Global baseline                |
| **Burst limit** (all routes)  | 10 requests     | 1 sec  | Prevent rapid-fire requests    |

## Configuration

### Environment Variables

```bash
# Required for DistributedRateLimiter (Redis backend)
REDIS_URL=redis://localhost:6379/0

# Optional: Slack webhook for abuse alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Python Configuration (app.py)

```python
from services.distributed_rate_limiter import RateLimitConfig

config = RateLimitConfig(
    # Global limits
    requests_per_minute=100,
    requests_per_hour=1000,
    requests_per_day=10000,
    
    # Burst protection
    burst_limit=10,  # Max requests in 1 second
    burst_window=1,
    
    # Endpoint-specific limits
    auth_attempts_per_minute=5,
    upload_requests_per_hour=50,
    transcription_requests_per_minute=20,
    
    # Advanced features
    enable_whitelist=True,
    enable_blacklist=True,
    enable_progressive_backoff=True
)
```

## Enforcement Status (Wave 0-14)

**Applied to Production Routes**:
- ✅ `/auth/login` - 5 requests/min (routes/auth.py)
- ✅ `/auth/register` - 5 requests/min (routes/auth.py)
- ✅ `/api/transcribe-audio` - 20 requests/min (routes/unified_transcription_api.py)
- ✅ `/api/transcribe_chunk_streaming` - 20 requests/min (routes/live_transcription_working.py)

**Fallback Behavior**: When Redis is unavailable, `@rate_limit` decorators become no-ops and Flask-Limiter global limits (100/min, 1000/hour) apply.

## Usage Examples

### 1. Using Flask-Limiter (Baseline)

Flask-Limiter is **automatically applied** to all routes with global limits (100/min, 1000/hour).

```python
from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/data')
def get_data():
    # Automatically rate limited by Flask-Limiter
    return jsonify({'data': '...'})
```

### 2. Using DistributedRateLimiter (Per-Route)

Apply custom rate limits to specific endpoints:

```python
from flask import Blueprint, jsonify
from services.distributed_rate_limiter import rate_limit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@rate_limit()  # Uses endpoint-specific limits (5/min for /auth/login)
def login():
    # Auth logic
    return jsonify({'token': '...'})

@auth_bp.route('/api/expensive-operation', methods=['POST'])
@rate_limit(requests_per_minute=10)  # Custom limit: 10/min
def expensive_op():
    # Expensive operation
    return jsonify({'result': '...'})
```

### 3. Exempting Routes from Rate Limiting

Some routes may need to bypass rate limits (e.g., health checks):

```python
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
# No @rate_limit decorator = exempt from DistributedRateLimiter
# Still subject to Flask-Limiter global limits
def health_check():
    return jsonify({'status': 'healthy'})
```

## Whitelist/Blacklist Management

### Whitelist (Bypass All Limits)

```python
from services.distributed_rate_limiter import rate_limiter

# Whitelist an IP address
rate_limiter.add_to_whitelist("ip:203.0.113.42")

# Whitelist a user (authenticated)
rate_limiter.add_to_whitelist("user:admin_user_id:203.0.113.42")

# Temporary whitelist (expires after 3600 seconds)
rate_limiter.add_to_whitelist("ip:203.0.113.42", ttl=3600)
```

### Blacklist (Block Completely)

```python
# Blacklist an abusive IP
rate_limiter.add_to_blacklist("ip:203.0.113.99")

# Temporary blacklist (expires after 1 hour)
rate_limiter.add_to_blacklist("ip:203.0.113.99", ttl=3600)
```

### Check Status

```python
# Check if client is whitelisted
is_whitelisted = rate_limiter.is_whitelisted("ip:203.0.113.42")

# Check if client is blacklisted
is_blacklisted = rate_limiter.is_blacklisted("ip:203.0.113.99")

# Check if client is in backoff period
in_backoff, ttl = rate_limiter.is_in_backoff("ip:203.0.113.100")
if in_backoff:
    print(f"Client in backoff for {ttl} more seconds")
```

## Progressive Backoff

**How it Works**:
1. Client exceeds rate limit → violation count incremented
2. After **3 violations** within 1 hour → automatic backoff applied
3. Backoff duration: `2^violations` minutes (capped at 60 minutes)
4. Example: 3 violations = 8 min backoff, 4 violations = 16 min, 5 violations = 32 min

**Redis Keys**:
- `rate_limit:violations:{identifier}` - Violation count (expires after 1 hour)
- `rate_limit:backoff:{identifier}` - Backoff TTL

## Slack Abuse Alerts

**Trigger Condition**: ≥5 violations within 1 hour

**Alert Contents**:
- Client identifier (IP or user_id:IP)
- IP address
- User ID (if authenticated, otherwise "anonymous")
- Number of violations
- Endpoint being abused
- Timestamp (UTC)

**Example Alert**:

```
⚠️ Rate Limit Abuse Detected

Client:     ip:203.0.113.100
IP Address: 203.0.113.100
User ID:    anonymous
Violations: 5
Endpoint:   /api/transcribe

⏰ Alert Time: 2025-10-25 12:00:00 UTC
```

**Configuration**: Set `SLACK_WEBHOOK_URL` environment variable (see Circuit Breaker docs for webhook setup).

## Response Headers

### Successful Request (Under Limit)

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1698336000
```

### Rate Limit Exceeded

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1698336000
Retry-After: 42

{
  "error": "Rate limit exceeded",
  "limit": 100,
  "retry_after": 42,
  "code": "RATE_LIMIT_EXCEEDED"
}
```

### Burst Limit Exceeded

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 1

{
  "error": "Rate limit exceeded - too many requests",
  "retry_after": 1,
  "code": "BURST_LIMIT"
}
```

### Backoff Period Active

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 480

{
  "error": "Rate limit exceeded - backoff period active",
  "retry_after": 480,
  "code": "BACKOFF_ACTIVE"
}
```

### Blacklisted

```http
HTTP/1.1 403 Forbidden

{
  "error": "Access denied",
  "code": "BLACKLISTED"
}
```

## Monitoring & Statistics

### Get Rate Limiter Statistics

```python
from services.distributed_rate_limiter import rate_limiter

stats = rate_limiter.get_stats()
# {
#   'total_requests': 15420,
#   'blocked_requests': 234,
#   'burst_blocks': 45,
#   'rate_limit_blocks': 189,
#   'whitelist_count': 5,
#   'blacklist_count': 12,
#   'block_rate': 0.015  # 1.5% of requests blocked
# }
```

### Metrics to Monitor

1. **Block Rate** - `blocked_requests / total_requests` (should be <5%)
2. **Burst Blocks** - Frequent burst blocks indicate bot activity
3. **Blacklist Growth** - Rapid growth indicates attack
4. **Whitelist Count** - Ensure only trusted IPs whitelisted

### Prometheus Metrics (Future)

```
# Planned metrics for Wave 0 follow-up
rate_limit_requests_total{endpoint="/api/transcribe"} 1234
rate_limit_blocked_total{endpoint="/api/transcribe",reason="rate_limit"} 45
rate_limit_backoff_active{identifier="ip:203.0.113.100"} 1
```

## Troubleshooting

### Problem: All requests getting 429 errors

**Cause**: Rate limits too aggressive or client IP incorrectly identified

**Solution**:
1. Check client IP extraction logic (`X-Forwarded-For` header)
2. Verify rate limit configuration (not too low)
3. Check if client is blacklisted: `rate_limiter.is_blacklisted("ip:...")`
4. Check Redis connectivity
5. Temporarily whitelist client for testing

### Problem: Rate limiting not working

**Cause**: Redis not configured or DistributedRateLimiter not initialized

**Solution**:
1. Check logs for "DistributedRateLimiter configured" message
2. Verify `REDIS_URL` environment variable is set
3. Test Redis connectivity: `redis-cli ping`
4. Fall back to Flask-Limiter (always active) if needed

### Problem: Slack alerts not sending

**Cause**: Slack webhook not configured or rate limiter can't reach Slack API

**Solution**:
1. Verify `SLACK_WEBHOOK_URL` is set
2. Test webhook: `curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"test"}'`
3. Check application logs for Slack errors
4. Verify firewall allows outbound HTTPS to Slack

### Problem: False positives (legitimate users blocked)

**Cause**: Shared IPs (NAT, VPN, corporate proxy) or overly aggressive limits

**Solution**:
1. Increase endpoint-specific limits
2. Whitelist corporate IP ranges
3. Implement user-based rate limiting (not just IP-based)
4. Add authentication-based exemptions

## Production Deployment

### Pre-Deployment Checklist

- [ ] Redis configured with `REDIS_URL` environment variable
- [ ] Slack webhook configured for abuse alerts (`SLACK_WEBHOOK_URL`)
- [ ] Rate limit thresholds tuned for production traffic
- [ ] Monitoring dashboards configured (Prometheus, Grafana)
- [ ] Whitelist configured for trusted IPs (office, CI/CD)
- [ ] Backoff configuration tested
- [ ] Alert escalation procedures documented

### Performance Impact

- **Redis overhead**: ~1-2ms per request (Redis local or same datacenter)
- **Memory overhead**: ~1KB per unique client per hour
- **CPU overhead**: Negligible (simple Redis operations)

**Result**: <2ms latency increase, prevents hours of downtime from DDoS attacks.

### Scaling Considerations

**Redis Cluster** (>10,000 RPS):
- Use Redis Cluster for horizontal scaling
- Configure connection pooling: `max_connections=50`
- Monitor Redis CPU, memory, network

**Multiple Instances** (Load Balanced):
- Rate limits shared across all instances via Redis
- No configuration changes needed
- Ensure all instances use same `REDIS_URL`

## Best Practices

1. **Tiered Limits** - Free users: 100/hour, Pro users: 1000/hour, Enterprise: whitelisted
2. **Gradual Rollout** - Start with high limits, gradually decrease based on abuse patterns
3. **Client-Friendly Errors** - Always include `Retry-After` header
4. **Monitor Block Rate** - Alert if >5% requests blocked (indicates too aggressive limits)
5. **Whitelist CI/CD** - Prevent blocking automated tests
6. **Document Public APIs** - Publish rate limits in API documentation
7. **Rate Limit Keys** - Consider user-based limits for authenticated users (more accurate than IP)

## Security Considerations

1. **DDoS Protection** - Rate limiting is **first line of defense**, not sole protection
2. **Layer 7 Attacks** - Combine with WAF (Cloudflare, AWS WAF) for sophisticated attacks
3. **Credential Stuffing** - Auth endpoints have stricter limits (5/min)
4. **API Key Leaks** - Monitor for unusual patterns (one key hitting limit repeatedly)
5. **Bot Detection** - Burst protection catches most bots (10 req/sec impossible for humans)

## See Also

- [Circuit Breaker Documentation](./CIRCUIT_BREAKER.md) - Upstream service protection
- [Deployment Playbook](./DEPLOYMENT_PLAYBOOK.md) - Production deployment procedures
- [Staging Environment](./STAGING_ENVIRONMENT.md) - Testing rate limiting in staging
- [Row-Level Security](./ROW_LEVEL_SECURITY.md) - Database security layer
