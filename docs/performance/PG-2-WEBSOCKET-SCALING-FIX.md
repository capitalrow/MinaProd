# PG-2: WebSocket Concurrent Connection Failure - Production Blocker

**Date**: October 2, 2025  
**Severity**: 🔴 CRITICAL - Production Blocker  
**Status**: ❌ BLOCKED - Requires Fix Before Production Deployment

---

## Issue Summary

Performance benchmarking (PG-2) revealed a critical failure in WebSocket concurrent connection handling:

- **Sequential Connections**: ✅ 90% success rate (45/50 connections)
- **Concurrent Connections**: ❌ 0% success rate (0/10 connections)  
- **Impact**: System collapses under minimal parallel WebSocket load
- **Production Risk**: **CRITICAL** - Denial of service with multiple simultaneous users

---

## Root Cause Analysis

### Observed Behavior
When 10 WebSocket clients attempt to connect simultaneously:
```
Connection error: Connection refused by the server (10/10 failures)
OSError: [Errno 9] Bad file descriptor (repeating errors in logs)
```

### Root Cause
**Single Gunicorn Worker Limitation**:
- Current configuration: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`
- `--reload` flag restricts to single worker (development mode)
- Single eventlet worker overwhelmed by rapid concurrent connections
- Socket file descriptors closed prematurely under load
- Worker crashes and restarts repeatedly

### Technical Details
1. Gunicorn eventlet worker has limited connection pool
2. Rapid concurrent connections exhaust available sockets
3. File descriptors become invalid ("Bad file descriptor")
4. Worker crashes, causing connection refusal
5. System enters crash-loop under sustained load

---

## Required Fix

### Production Configuration Changes

**Current (Development)**:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

**Required (Production)**:
```bash
gunicorn \
  --bind 0.0.0.0:5000 \
  --workers 4 \
  --worker-class eventlet \
  --worker-connections 1000 \
  --reuse-port \
  --max-requests 10000 \
  --max-requests-jitter 1000 \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  main:app
```

**Key Changes**:
- `--workers 4`: Multiple workers for parallel request handling (2 × CPU cores)
- `--worker-class eventlet`: Explicit eventlet worker for Socket.IO
- `--worker-connections 1000`: Increased concurrent connections per worker
- Removed `--reload`: Production mode (no auto-reload)
- Added `--max-requests`: Worker recycling for memory management
- Added timeout and keep-alive settings

###Socket.IO Configuration Tuning

**Current**: Already configured properly in `app.py`
```python
socketio = SocketIO(
    async_mode="eventlet",
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=10*1024*1024,  # 10MB
    allow_upgrades=True,
    transports=['websocket', 'polling']
)
```

**Additional Recommendations**:
- Add connection rate limiting (prevent DoS)
- Implement Redis for multi-worker Socket.IO coordination
- Add health checks for worker monitoring

---

## Testing Requirements

Before marking PG-2 as complete, must verify:

### 1. Sequential Connection Test
- Run 50 sequential WebSocket connections
- **Target**: ≥95% success rate
- **Current**: ✅ 90% (acceptable)

### 2. Concurrent Connection Test
- Run 10 simultaneous WebSocket connections
- **Target**: ≥95% success rate  
- **Current**: ❌ 0% (CRITICAL FAILURE)

### 3. Load Test
- Gradually ramp from 10 → 50 → 100 concurrent connections
- Monitor worker stability and memory usage
- **Target**: No worker crashes, <5% error rate

### 4. Stress Test
- 150 concurrent connections (3x normal capacity)
- **Target**: Graceful degradation, no crashes

---

## Implementation Plan

### Phase 1: Update Gunicorn Configuration (30min)
1. Create `gunicorn_config.py` with production settings
2. Update workflow command to use config file
3. Test basic application startup

### Phase 2: Re-run WebSocket Benchmarks (1h)
1. Restart application with new configuration
2. Run sequential connection test (verify still passing)
3. Run concurrent connection test (verify fix)
4. Run load test with 10 → 50 → 100 connections

### Phase 3: Documentation & Verification (30min)
1. Update PG-2-PERFORMANCE-BASELINE.md with passing results
2. Document production deployment configuration
3. Get architect approval for PG-2 completion

**Total Estimated Time**: 2 hours

---

## Environment Limitation Note

**`.replit` file cannot be modified directly** - Requires workflow restart with new command or `gunicorn_config.py` file approach.

---

## Success Criteria

PG-2 can be marked complete when:
- ✅ Sequential connections: ≥95% success (currently 90% ✅)
- ❌ Concurrent connections: ≥95% success (currently 0% ❌)
- ⏳ Load test: 100 concurrent connections with <5% errors
- ⏳ No worker crashes under normal load
- ⏳ Architect approval of updated benchmarks

---

## Next Steps

1. **Inform user** of production blocker and estimated 2h fix time
2. **Create production gunicorn config** file
3. **Re-run benchmarks** after configuration change
4. **Complete PG-2** once all tests pass

This issue was correctly identified by performance benchmarking (PG-2) and must be resolved before production deployment.
