# 1. Flask + Socket.IO for Real-Time Architecture

**Date**: 2025-10-02

**Status**: Accepted

**Context**: Mina requires real-time bidirectional communication for live transcription streaming. We needed to choose a technology stack that supports WebSocket connections, is production-ready, and integrates well with our Python backend.

**Decision**: Use Flask with Flask-SocketIO for real-time communication, backed by Eventlet for async I/O and Redis for horizontal scaling.

**Alternatives Considered**:
- FastAPI with WebSockets: More modern but less mature Socket.IO integration
- Django Channels: Required full Django migration
- Node.js with Socket.IO: Would require separate language stack

**Consequences**:
- **Positive**:
  - Mature, battle-tested Socket.IO protocol with automatic fallbacks
  - Seamless integration with existing Flask application
  - Redis adapter enables horizontal scaling across multiple workers
  - Eventlet provides efficient async I/O without full async rewrite
  - Wide browser compatibility with polling fallback
  
- **Negative**:
  - Eventlet monkey-patching can cause issues with some libraries
  - Single-threaded nature requires careful consideration of blocking operations
  - Need to manage worker count and concurrency limits
