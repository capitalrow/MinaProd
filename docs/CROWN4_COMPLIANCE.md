# CROWN⁴ Dashboard Event Sequencing - Compliance Documentation

## Table of Contents
1. [Overview](#overview)
2. [Event Catalog](#event-catalog)
3. [Payload Schemas](#payload-schemas)
4. [Cache Contracts](#cache-contracts)
5. [WebSocket Patterns](#websocket-patterns)
6. [Performance Guarantees](#performance-guarantees)
7. [Testing & Validation](#testing--validation)

---

## Overview

CROWN⁴ (Cached Real-time Orchestration with WebSocket Namespaces) is a comprehensive event-driven architecture that ensures sub-300ms event propagation with zero-desync guarantees.

### Core Principles
- **Event Sequencing**: All events are strictly ordered with sequence numbers
- **Cache-First Bootstrap**: Dashboard loads in <200ms using IndexedDB
- **Multi-Tab Sync**: BroadcastChannel API for cross-tab state synchronization
- **Graceful Degradation**: Fallback mechanisms for all failure modes
- **Zero Data Loss**: Event replay on reconnection with gap detection

### Architecture Components
1. **EventLedger**: PostgreSQL-based event log with sequence numbers
2. **EventSequencer**: Server-side event ordering and validation
3. **EventBroadcaster**: WebSocket event emission across 4 namespaces
4. **IndexedDBCache**: Client-side persistence with 5 stores
5. **CacheValidator**: SHA-256 checksum validation and reconciliation
6. **BroadcastSync**: Multi-tab synchronization via BroadcastChannel
7. **DashboardErrorHandler**: Comprehensive error recovery

---

## Event Catalog

### Event Types (15 Total)

#### 1. SESSION_CREATE
- **Description**: New meeting/session created
- **Namespace**: `/dashboard`, `/meetings`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 2. SESSION_UPDATE
- **Description**: Meeting metadata updated
- **Namespace**: `/dashboard`, `/meetings`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 3. TASK_CREATE
- **Description**: New task/action item created
- **Namespace**: `/dashboard`, `/tasks`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 4. TASK_UPDATE
- **Description**: Task status or metadata changed
- **Namespace**: `/dashboard`, `/tasks`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 5. TASK_DELETE
- **Description**: Task permanently deleted
- **Namespace**: `/dashboard`, `/tasks`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 6. ANALYTICS_REFRESH
- **Description**: Analytics data updated
- **Namespace**: `/dashboard`, `/analytics`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 7. DASHBOARD_REFRESH
- **Description**: Dashboard statistics refreshed
- **Namespace**: `/dashboard`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 8. SESSION_ARCHIVE
- **Description**: Meeting archived by user (CROWN⁴ Phase 4)
- **Namespace**: `/dashboard`, `/meetings`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 9. ARCHIVE_REVEAL
- **Description**: User viewed archive tab (analytics event)
- **Namespace**: `/dashboard`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 10. MEETING_UPDATE
- **Description**: Generic meeting update event
- **Namespace**: `/dashboard`, `/meetings`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 11. DASHBOARD_IDLE_SYNC
- **Description**: Background 30-second sync event
- **Namespace**: `/dashboard`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 12. FILTER_APPLY
- **Description**: User applied filter (search/time)
- **Namespace**: `/dashboard`
- **Sequence**: YES
- **Broadcast**: Local only

#### 13. INSIGHT_REMINDER
- **Description**: AI-powered predictive reminder (CROWN⁴ Phase 5)
- **Namespace**: `/dashboard`
- **Sequence**: YES
- **Broadcast**: User-scoped (24-hour throttling)

#### 14. SESSION_COMPLETE
- **Description**: Meeting finalization completed
- **Namespace**: `/dashboard`, `/meetings`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

#### 15. CACHE_INVALIDATE
- **Description**: Cache invalidation signal
- **Namespace**: `/dashboard`
- **Sequence**: YES
- **Broadcast**: Workspace-scoped

---

## Payload Schemas

### Standard Event Envelope
```json
{
  "event_id": 12345,
  "sequence": 98,
  "event_type": "SESSION_UPDATE",
  "event_name": "Meeting Updated",
  "workspace_id": 1,
  "user_id": 42,
  "timestamp": "2025-10-28T03:00:00Z",
  "data": {
    // Event-specific payload
  },
  "trace_id": "session_123_1730084400",
  "is_initial_sync": false
}
```

### SESSION_UPDATE Payload
```json
{
  "workspace_id": 1,
  "session_id": 123,
  "updates": {
    "title": "Updated Meeting Title",
    "status": "completed",
    "task_count": 5
  },
  "timestamp": "2025-10-28T03:00:00Z"
}
```

### TASK_UPDATE Payload
```json
{
  "workspace_id": 1,
  "task_id": 456,
  "session_id": 123,
  "updates": {
    "status": "completed",
    "completed_at": "2025-10-28T03:00:00Z"
  },
  "optimistic_ui": true,
  "timestamp": "2025-10-28T03:00:00Z"
}
```

### SESSION_ARCHIVE Payload
```json
{
  "workspace_id": 1,
  "meeting_id": 123,
  "archived_by": 42,
  "timestamp": "2025-10-28T03:00:00Z"
}
```

### INSIGHT_REMINDER Payload
```json
{
  "user_id": 42,
  "workspace_id": 1,
  "reminder": {
    "title": "Overdue Task Alert",
    "message": "You have 3 overdue tasks from this week's meetings",
    "action_text": "View Tasks",
    "action_url": "/tasks",
    "type": "overdue",
    "confidence": 0.85
  },
  "timestamp": "2025-10-28T03:00:00Z"
}
```

### DASHBOARD_REFRESH Payload
```json
{
  "workspace_id": 1,
  "stats": {
    "total_meetings": 156,
    "total_tasks": 423,
    "hours_saved": 78.5,
    "active_meetings": 142,
    "archived_meetings": 14
  },
  "timestamp": "2025-10-28T03:00:00Z"
}
```

---

## Cache Contracts

### IndexedDB Schema

#### Store: `meetings`
```typescript
interface Meeting {
  id: number;                    // Primary key
  title: string;
  status: 'active' | 'completed' | 'archived';
  created_at: string;            // ISO timestamp
  duration: number;              // seconds
  summary: string;
  task_count: number;
  participant_count: number;
  archived: boolean;             // Indexed
  _cached_at: string;            // ISO timestamp
  _checksum: string;             // SHA-256 hash
}
```

#### Store: `analytics`
```typescript
interface Analytics {
  session_id: number;            // Primary key
  speaking_time: object;
  sentiment: object;
  participation: object;
  updated_at: string;            // Indexed
  _cached_at: string;
  _checksum: string;
}
```

#### Store: `tasks`
```typescript
interface Task {
  id: number;                    // Primary key
  session_id: number;            // Indexed
  text: string;
  status: 'pending' | 'completed' | 'cancelled';  // Indexed
  priority: 'low' | 'medium' | 'high';  // Indexed
  due_date: string | null;
  assignee: string | null;
  _cached_at: string;
  _checksum: string;
}
```

#### Store: `sessions`
```typescript
interface SessionMetadata {
  external_session_id: string;  // Primary key
  session_id: number;            // Indexed
  last_accessed: string;         // Indexed
  _cached_at: string;
}
```

#### Store: `metadata`
```typescript
interface CacheMetadata {
  key: string;                   // Primary key
  value: any;
  updated_at: string;
}
```

### Cache Validation Contract
1. **Checksum Calculation**: SHA-256(JSON.stringify(sortedKeys(data)))
2. **Staleness Threshold**: 24 hours
3. **Purge Interval**: 60 minutes
4. **Max Cache Size**: 50 MB per workspace

### Cache Reconciliation Flow
```
1. Client requests data
2. Check IndexedDB cache
   ├─ Cache HIT
   │  ├─ Validate checksum
   │  │  ├─ MATCH → Return cached data
   │  │  └─ MISMATCH → Fetch from server + update cache
   │  └─ Check staleness (>24h)
   │     ├─ STALE → Fetch from server + update cache
   │     └─ FRESH → Return cached data
   └─ Cache MISS → Fetch from server + populate cache
```

---

## WebSocket Patterns

### Namespace Architecture

#### 1. `/dashboard` Namespace
- **Purpose**: Dashboard-wide events and statistics
- **Events**: SESSION_UPDATE, DASHBOARD_REFRESH, INSIGHT_REMINDER, ARCHIVE_REVEAL
- **Room**: `workspace_{workspace_id}`
- **Reconnection**: Exponential backoff with jitter

#### 2. `/tasks` Namespace
- **Purpose**: Task-specific events
- **Events**: TASK_CREATE, TASK_UPDATE, TASK_DELETE
- **Room**: `workspace_{workspace_id}`
- **Reconnection**: Exponential backoff with jitter

#### 3. `/analytics` Namespace
- **Purpose**: Analytics and insights
- **Events**: ANALYTICS_REFRESH
- **Room**: `workspace_{workspace_id}`
- **Reconnection**: Exponential backoff with jitter

#### 4. `/meetings` Namespace
- **Purpose**: Meeting-specific events
- **Events**: SESSION_CREATE, SESSION_UPDATE, SESSION_ARCHIVE
- **Room**: `workspace_{workspace_id}`
- **Reconnection**: Exponential backoff with jitter

### Connection Lifecycle

#### 1. Initial Connection
```javascript
socket.on('connect', () => {
  // Join workspace room
  socket.emit('join_workspace', { workspace_id });
  
  // Request initial sync
  socket.emit('request_event_replay', {
    last_sequence: 0,
    namespace: '/dashboard'
  });
});
```

#### 2. Disconnection Detection
```javascript
socket.on('disconnect', (reason) => {
  // Record last known sequence
  const lastSeq = getLastSequence(namespace);
  
  // Abort pending requests
  abortController.abort();
  
  // Start reconnection
  scheduleReconnection();
});
```

#### 3. Reconnection with Replay
```javascript
socket.on('connect', () => {
  // Register replay listener BEFORE requesting replay
  socket.once('event_replay', handleReplayEvents);
  
  // Request missing events
  socket.emit('request_event_replay', {
    last_sequence: lastKnownSequence,
    namespace: namespace
  });
});
```

#### 4. Event Replay Handler
```javascript
function handleReplayEvents(data) {
  const { events, is_initial_sync } = data;
  
  // Process events in sequence order
  events.sort((a, b) => a.sequence - b.sequence);
  
  for (const event of events) {
    processEvent(event, is_initial_sync);
  }
}
```

### Reconnection Strategy

#### Exponential Backoff Formula
```
delay = min(baseDelay * 2^attempts, maxDelay) + jitter
where:
  baseDelay = 1000ms
  maxDelay = 30000ms (30 seconds)
  jitter = random(-20%, +20%) of delay
```

#### Example Backoff Sequence
```
Attempt 1: 1000ms ± 200ms = 800-1200ms
Attempt 2: 2000ms ± 400ms = 1600-2400ms
Attempt 3: 4000ms ± 800ms = 3200-4800ms
Attempt 4: 8000ms ± 1600ms = 6400-9600ms
Attempt 5: 16000ms ± 3200ms = 12800-19200ms
Attempt 6+: 30000ms ± 6000ms = 24000-36000ms (capped)
```

---

## Performance Guarantees

### Latency Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Event Propagation | <300ms | Server emit → Client update |
| Cache-First Bootstrap | <200ms | Page load → Interactive dashboard |
| WebSocket Reconnection | <5s | Disconnect → Reconnected with replay |
| Cache Read | <10ms | IndexedDB query completion |
| Event Sequencing | <50ms | Receive → Process → Update UI |

### Throughput Targets

| Operation | Target | Load Test |
|-----------|--------|-----------|
| Event Processing | >1000 events/sec | 5000 events, all in-order |
| Cache Writes | >500 sessions/sec | 10000 sessions created |
| Concurrent Operations | >100 concurrent | 100 parallel requests |

### Memory Limits

| Resource | Limit | Enforcement |
|----------|-------|-------------|
| IndexedDB Cache | 50 MB/workspace | LRU eviction |
| Event Buffer | 100 events | FIFO with overflow |
| WebSocket Rooms | 1000 connections/room | Server-side limit |

---

## Testing & Validation

### Integration Tests
Run comprehensive test suite:
```javascript
const tests = new CROWN4IntegrationTests();
await tests.runAll({
  cache: window.cache,
  websocketManager: window.websocketManager,
  errorHandler: window.errorHandler,
  prefetchController: window.prefetchController
});
```

### Performance Monitoring
Start performance monitoring:
```javascript
const monitor = new CROWN4PerformanceMonitor();
monitor.startSession();

// Run audit
await monitor.runAudit();
```

### Load Testing
Run load test (10k+ sessions):
```javascript
const loadTest = new CROWN4LoadTest();
await loadTest.runFullSuite({
  sessionCount: 10000,
  eventCount: 5000,
  concurrency: 100
});
```

### Compliance Checklist

- [x] Event sequencing with no gaps or duplicates
- [x] Sub-300ms event propagation latency
- [x] Cache-first bootstrap <200ms
- [x] Multi-tab synchronization via BroadcastChannel
- [x] WebSocket reconnection with event replay
- [x] Stale cache purging every 60 minutes
- [x] Missing session recovery (404 handling)
- [x] Navigation abort cleanup
- [x] AI-powered insight reminders with 24h throttling
- [x] Zero data loss guarantee on reconnection

---

## Version History

### v1.0.0 (CROWN⁴ Phase 5 Complete) - 2025-10-28
- ✅ 15-event pipeline operational
- ✅ Multi-tab BroadcastChannel sync
- ✅ WebSocket reconnection with exponential backoff
- ✅ AI-powered insight reminders
- ✅ Comprehensive error handling
- ✅ Integration tests, performance monitoring, load testing
- ✅ Full compliance documentation

---

## Contact & Support

For questions or issues related to CROWN⁴ compliance:
- Review event logs in EventLedger table
- Check browser console for sequencing errors
- Run integration tests for validation
- Monitor performance metrics in real-time

**Last Updated**: October 28, 2025
**Status**: Production Ready ✅
