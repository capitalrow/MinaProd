# Memory Leak Monitoring Plan

## Current Status (Sept 30, 2025)
- **Worker RSS**: 219 MB (stable)
- **System Baseline**: 26.8 GB
- **Previous Issue**: 630 MB/min growth detected, resolved after app restart
- **Current State**: No leak warnings in latest logs

## Monitoring Strategy
1. **Immediate**: Health monitor running (30s intervals)
2. **Short-term**: Monitor next 6 hours for growth patterns
3. **Long-term**: Implement soak test (45-60 min simulated workload)

## Soak Test Requirements (Phase 0)
- Simulated WebSocket connections (10-20 concurrent)
- Audio streaming workload
- Monitor RSS growth, Socket.IO queue depth
- Track memory per session/connection
- Alert if growth > 25 MB/minute

## Action Items
- [ ] Implement automated soak test script
- [ ] Set up memory growth alerts in health_monitor.py
- [ ] Add RSS tracking to metrics dashboard
- [ ] Document baseline memory per connection type

## Resolution Evidence Required
- Sustained 60-minute test with <5MB/min growth
- No memory leak warnings from health monitor
- Stable memory after 100+ completed sessions
