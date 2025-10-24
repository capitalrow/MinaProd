# Mina - Meeting Insights & Action Platform

## Overview

Mina is an enterprise-grade SaaS platform designed to transform meetings into actionable moments. It provides real-time transcription with speaker identification, voice activity detection, and AI-powered insights to generate comprehensive meeting summaries and extract actionable tasks. Its core purpose is to enhance productivity and streamline post-meeting workflows. The business vision is to deliver a cutting-edge platform that significantly improves post-meeting productivity, tapping into the growing market for AI-powered business tools.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application utilizes a layered architecture with Flask as the web framework and Socket.IO for real-time communication, following an application factory pattern. The frontend employs a "Crown+" design system with a dark theme, vanilla JavaScript, and Socket.IO client for a modern and accessible UI/UX.

**Recent Fixes (October 2025):**
- **Comment Model Registry Conflict (Resolved)**: Fixed SQLAlchemy duplicate model registration by separating SessionComment (session-level comments in "session_comments" table) from Comment/SegmentComment (segment-level threaded comments in "comments" table). Auto-created tables via db.create_all(). No data loss.

**UI/UX Decisions:**
- **Crown+ Design System**: Glassmorphism effects, smooth animations, consistent design tokens.
- **Theming**: Dark theme, light mode support, system preference detection.
- **Responsiveness**: Mobile-first approach.
- **Accessibility**: WCAG 2.1 AA compliance, screen reader support, keyboard navigation, high contrast/large text modes.
- **UI States**: Comprehensive loading, empty, and error states.
- **Component Standardization**: Standardized modals, tooltips, forms, buttons, navigation, cards, tables, and badges.

**Technical Implementations & Feature Specifications:**
- **AI Intelligence**: Auto-summarization (3-paragraph), key points (5-10 actionable insights), action items (with assignee, priority, due dates), questions tracking, decisions extraction, sentiment analysis, topic detection, language detection, custom AI prompts.
- **AI Copilot**: Chat interface with streaming responses (GPT-4o-mini), context awareness (recent meetings, tasks, AI insights, conversation history, user preferences), prompt template library (8 system templates + CRUD API), suggested actions, and citations.
- **Analytics Dashboard**: Speaking time distribution, participation balance metrics (6-dimensional scoring), sentiment analysis tracking, topic trend analysis, question/answer tracking, action items completion rate, export functionality (JSON), custom analytics widgets.
- **Sharing & Integrations**: Public sharing (link generation, privacy settings, expiration), embed functionality, email sharing, Slack integration (webhooks), team sharing (role-based permissions), share analytics tracking.
- **Transcript Display**: Enhanced layout (glassmorphism, speaker labels, timestamps, confidence indicators), search functionality, export options (TXT, DOCX, PDF, JSON), copy functionality, inline editing with auto-save and history, speaker identification (color-coding, editable names, filtering), highlighting (yellow/green/blue, filtering), commenting with threading, playback sync, comprehensive keyboard shortcuts.
- **Real-time Audio Processing Pipeline**: Client-side VAD, WebSocket streaming, server-side processing, OpenAI Whisper API integration, real-time broadcasting, multi-speaker diarization, multi-language detection, adaptive VAD, real-time audio quality monitoring, confidence scoring.
- **Security & Authentication**: JWT-based authentication with RBAC, bcrypt, AES-256 encryption, rate limiting, CSP headers, CSRF protection, input validation.
- **Performance**: Low Word Error Rate (WER), sub-400ms end-to-end transcription latency, optimized database indexing.

**System Design Choices:**
- **Backend**: Flask with Flask-SocketIO.
- **Database**: SQLAlchemy ORM (SQLite for dev, PostgreSQL for prod).
- **Real-time Communication**: Socket.IO for WebSockets with polling fallback.
- **Frontend**: Bootstrap dark theme, vanilla JavaScript, Socket.IO client.
- **Data Model**: Session and Segment models.
- **Service Layer**: Encapsulated business logic (e.g., `TranscriptionService`, `AI Insights Service`).
- **Production Readiness**: Scalability, security, reliability, fault tolerance using Redis for horizontal scaling, distributed room management, session state checkpointing, robust error handling, background task retry systems, and Redis failover.
- **Background Processing**: Non-blocking transcription using thread pools.
- **Continuous Audio Processing**: Overlapping context windows and sliding buffer management.
- **Advanced Deduplication**: Text stability analysis.
- **WebSocket Reliability**: Auto-reconnection, heartbeat monitoring, session recovery.
- **Monitoring & Observability**: Sentry for error tracking, BetterStack for uptime, structured JSON logging, SLO/SLI metrics.
- **Backup & Disaster Recovery**: Automated, encrypted PostgreSQL backups with multi-tier retention.
- **Deployment**: CI/CD pipeline (GitHub Actions), Alembic migrations, blue-green deployment.

## External Dependencies

**AI/ML Services:**
- OpenAI Whisper API
- OpenAI GPT-4o-mini
- OpenAI GPT-4 Turbo
- WebRTC MediaRecorder

**Database Systems:**
- PostgreSQL
- SQLAlchemy
- Redis

**Real-time Communication:**
- Socket.IO with Redis Adapter

**Security & Authentication:**
- Flask-Login
- Cryptography
- bcrypt
- PyJWT

**Audio Processing Libraries:**
- NumPy/SciPy
- WebRTCVAD
- PyDub

**Web Framework Dependencies:**
- Flask
- Bootstrap
- WhiteNoise
- ProxyFix
- Chart.js

**Production Infrastructure:**
- Gunicorn
- Eventlet

**Other Integrations:**
- SendGrid (for email sharing)
- Slack (for webhook integration)
- Sentry (for error tracking)
- BetterStack (for uptime monitoring)