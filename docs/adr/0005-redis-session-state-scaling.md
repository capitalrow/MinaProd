# 5. Redis for Session State and Horizontal Scaling

**Date**: 2025-10-02

**Status**: Accepted

**Context**: To enable horizontal scaling with multiple Gunicorn workers and Socket.IO instances, we need distributed session management and pub/sub messaging.

**Decision**: Use Redis for Socket.IO adapter, session state management, and distributed caching with automatic failover to in-memory fallback.

**Alternatives Considered**:
- In-memory only: Doesn't support horizontal scaling
- RabbitMQ: More complex, overkill for our use case
- Memcached: No pub/sub support needed for Socket.IO

**Consequences**:
- **Positive**:
  - Enables multi-worker Socket.IO deployments
  - Sub-millisecond session lookups
  - Distributed pub/sub for room broadcasts
  - Automatic failover manager for resilience
  - Can use for rate limiting and caching
  
- **Negative**:
  - Additional infrastructure dependency
  - Requires monitoring and maintenance
  - Data loss risk if Redis crashes (mitigated by failover)
