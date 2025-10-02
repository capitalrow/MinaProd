# Database Schema Documentation

## Overview

Mina uses PostgreSQL with SQLAlchemy ORM. The database is organized around workspaces, users, meetings, transcription sessions, and tasks.

## Core Tables

### User
Stores user account information and authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | User ID |
| username | String(64) | Unique, Not Null | Username |
| email | String(120) | Unique, Not Null | Email address |
| password_hash | String(256) | | Bcrypt password hash |
| workspace_id | Integer | FK(workspace.id) | User's workspace |
| role | String(20) | Default='member' | User role (admin/organizer/member) |
| is_active | Boolean | Default=True | Account status |
| created_at | DateTime | Default=now() | Account creation |

**Indexes**:
- `username` (unique)
- `email` (unique)
- `workspace_id` (for workspace queries)

### Workspace
Multi-tenancy container for organizations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Workspace ID |
| name | String(128) | Not Null | Workspace name |
| slug | String(64) | Unique, Not Null | URL-safe identifier |
| settings | JSON | Default={} | Workspace settings |
| created_at | DateTime | Default=now() | Created timestamp |

### Meeting
Meeting metadata and lifecycle.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Meeting ID |
| title | String(255) | Not Null | Meeting title |
| description | Text | | Meeting description |
| status | String(20) | Default='draft' | draft/scheduled/live/completed/cancelled |
| workspace_id | Integer | FK(workspace.id), Not Null | Owner workspace |
| organizer_id | Integer | FK(user.id), Not Null | Meeting organizer |
| session_id | String(36) | Unique | Linked transcription session |
| scheduled_start | DateTime | | Scheduled start time |
| scheduled_end | DateTime | | Scheduled end time |
| created_at | DateTime | Default=now() | Created timestamp |
| updated_at | DateTime | Default=now() | Last update |

**Indexes**:
- `workspace_id, status, created_at DESC` (meeting list queries)
- `workspace_id, scheduled_start` (calendar queries)
- `organizer_id` (user's organized meetings)
- `session_id` (unique, lookup)

**Relationships**:
- `workspace`: Many-to-One with Workspace
- `organizer`: Many-to-One with User
- `tasks`: One-to-Many with Task
- `participants`: One-to-Many with Participant
- `analytics`: One-to-One with Analytics

### Session
Real-time transcription session.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Session ID |
| external_id | String(36) | Unique, Not Null | UUID for client |
| status | String(20) | Default='pending' | pending/recording/processing/completed/error |
| user_id | Integer | FK(user.id) | Session owner |
| language | String(10) | Default='en' | Language code |
| vad_enabled | Boolean | Default=True | Voice activity detection |
| started_at | DateTime | | Session start |
| ended_at | DateTime | | Session end |
| created_at | DateTime | Default=now() | Created timestamp |

**Indexes**:
- `external_id` (unique, client lookup)
- `user_id` (user's sessions)
- `status, started_at DESC` (active sessions)

**Relationships**:
- `user`: Many-to-One with User
- `segments`: One-to-Many with Segment

### Segment
Individual transcription segment.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Segment ID |
| session_id | Integer | FK(session.id), Not Null | Parent session |
| text | Text | Not Null | Transcribed text |
| confidence | Float | | Confidence score 0-1 |
| start_ms | Integer | | Start time milliseconds |
| end_ms | Integer | | End time milliseconds |
| speaker | String(50) | | Speaker identifier |
| language | String(10) | | Detected language |
| kind | String(20) | Default='final' | interim/final/corrected |
| created_at | DateTime | Default=now() | Created timestamp |

**Indexes**:
- `session_id, start_ms` (ordered retrieval)
- `kind` (filtering by type)

**Relationships**:
- `session`: Many-to-One with Session

### Task
Action items extracted from meetings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Task ID |
| title | String(255) | Not Null | Task title |
| description | Text | | Task details |
| status | String(20) | Default='todo' | todo/in_progress/completed/cancelled |
| priority | String(20) | Default='medium' | low/medium/high/critical |
| meeting_id | Integer | FK(meeting.id), Not Null | Source meeting |
| assigned_to_id | Integer | FK(user.id) | Assignee |
| created_by_id | Integer | FK(user.id), Not Null | Creator |
| due_date | Date | | Due date |
| completed_at | DateTime | | Completion time |
| depends_on_task_id | Integer | FK(task.id) | Parent task |
| created_at | DateTime | Default=now() | Created timestamp |
| updated_at | DateTime | Default=now() | Last update |

**Indexes**:
- `assigned_to_id, status, due_date` (user task list)
- `meeting_id, status` (meeting tasks)
- `created_by_id` (created tasks)
- `depends_on_task_id` (task dependencies)

**Relationships**:
- `meeting`: Many-to-One with Meeting
- `assigned_to`: Many-to-One with User
- `created_by`: Many-to-One with User
- `depends_on`: Many-to-One with Task (self-reference)

### Participant
Meeting participation tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Participant ID |
| meeting_id | Integer | FK(meeting.id), Not Null | Meeting |
| user_id | Integer | FK(user.id), Not Null | Participant |
| role | String(20) | Default='participant' | organizer/presenter/participant |
| status | String(20) | Default='invited' | invited/accepted/declined/attended |
| joined_at | DateTime | | Join timestamp |
| left_at | DateTime | | Leave timestamp |
| created_at | DateTime | Default=now() | Invitation timestamp |

**Indexes**:
- `meeting_id, user_id` (unique constraint, participant lookup)
- `user_id` (user's participation history)

**Relationships**:
- `meeting`: Many-to-One with Meeting
- `user`: Many-to-One with User

### Analytics
AI-generated meeting insights.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Analytics ID |
| meeting_id | Integer | FK(meeting.id), Unique | Analyzed meeting |
| analysis_status | String(20) | Default='pending' | pending/processing/completed/error |
| meeting_effectiveness_score | Float | | 0-1 effectiveness |
| overall_engagement_score | Float | | 0-1 engagement |
| overall_sentiment_score | Float | | 0-1 sentiment |
| key_topics | JSON | | Extracted topics |
| action_items_summary | JSON | | Action items |
| decisions_made | JSON | | Decisions |
| created_at | DateTime | Default=now() | Analysis start |
| updated_at | DateTime | Default=now() | Last update |

**Indexes**:
- `meeting_id` (unique, one-to-one)
- `analysis_status, created_at DESC` (pending analytics)

**Relationships**:
- `meeting`: One-to-One with Meeting

### Marker
User-marked important moments in transcripts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Auto | Marker ID |
| session_id | String(36) | Not Null | Session external ID |
| user_id | Integer | FK(user.id), Not Null | User who marked |
| type | String(20) | Not Null | decision/todo/risk/question |
| content | Text | Not Null | Marker content |
| timestamp | Integer | | Position in recording (ms) |
| speaker | String(50) | | Associated speaker |
| created_at | DateTime | Default=now() | Marked timestamp |

**Indexes**:
- `session_id, timestamp` (chronological retrieval)
- `user_id` (user's markers)

**Relationships**:
- `user`: Many-to-One with User

## Migrations

Migrations are managed via Flask-Migrate (Alembic):

```bash
# Create new migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Revert migration
flask db downgrade
```

## Performance Considerations

1. **Composite Indexes**: Critical for multi-column filtering and sorting
2. **N+1 Prevention**: Use `joinedload()` for relationships
3. **Connection Pooling**: Configured for 20 max connections
4. **Query Optimization**: Monitor slow queries (>500ms)

## Backup Strategy

- **Frequency**: Automated daily backups via Neon
- **Retention**: 7 days point-in-time recovery
- **Encryption**: AES-256 at rest
