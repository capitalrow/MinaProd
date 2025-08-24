# Architecture Decisions Record (ADR)

This document records the major architectural and implementation decisions made during the consolidation and development of the Mina transcription platform.

## ADR-001: Repository Consolidation Strategy

**Date:** 2025-01-24  
**Status:** Accepted  
**Context:** Multiple codebases existed with overlapping functionality that needed to be consolidated into a single production-ready repository.

### Decision
Consolidate the mina-transcription-hub-complete as the base repository structure and integrate improvements from the real-time transcription enhancements, maintaining the existing layered architecture.

**Rationale:**
- The hub-complete codebase provided a solid foundation with proper layered architecture
- Socket.IO integration was already established
- Database models and service layer were well-structured
- Frontend templates followed Bootstrap dark theme consistently

**Alternatives Considered:**
- Starting from scratch: Rejected due to time constraints and existing solid foundation
- Merging as separate modules: Rejected to avoid duplication and complexity

**Consequences:**
- Single source of truth for the application
- Consistent architecture patterns throughout
- Easier maintenance and deployment

---

## ADR-002: Flask + Socket.IO Architecture

**Date:** 2025-01-24  
**Status:** Accepted  
**Context:** Need for real-time communication between client and server for audio streaming and transcription updates.

### Decision
Maintain Flask + Flask-SocketIO + SQLAlchemy architecture with WebSocket streaming for real-time audio processing.

**Rationale:**
- Flask provides lightweight and flexible web framework
- Socket.IO enables reliable real-time communication with fallback to polling
- SQLAlchemy offers robust ORM with relationship management
- Architecture supports both HTTP REST API and WebSocket connections

**Technical Details:**
```python
# Socket.IO configuration
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    transport=['websocket', 'polling']
)
