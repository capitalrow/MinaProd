# Mina - Meeting Insights & Action Platform

## Overview

Mina is an enterprise-grade SaaS platform designed to transform meetings into actionable moments. It provides real-time transcription with speaker identification, voice activity detection, and AI-powered insights to generate comprehensive meeting summaries and extract actionable tasks. Its core purpose is to enhance productivity and streamline post-meeting workflows, aiming for a production-ready application with robust features and infrastructure. The business vision is to deliver a cutting-edge platform that significantly improves post-meeting productivity, tapping into the growing market for AI-powered business tools.

## Recent Development Progress (October 2025)

**Phase 1: Design System - ✅ COMPLETE (32/32 tasks - 100%)**
**Phase 2: Transcript Experience - 🔄 IN PROGRESS (26/31 tasks - 84%)**
**Overall Progress: 136/268 tasks (51%)**

### Phase 2 Group 4: Sharing & Integrations - 🔄 IN PROGRESS (4/9 tasks - 44%)

**Recently Completed (T2.23, T2.26, T2.27, T2.28):**
- ✅ Public sharing with link generation, privacy settings, expiration (1-90 days)
- ✅ Embed functionality with responsive iframe code generation  
- ✅ Email sharing with SendGrid integration (multiple recipients)
- ✅ Slack integration with webhook posting and Block Kit formatting

**Implementation Details:**
- Share modal with 3 tabs: Link, Email, Embed
- Active shares management with deactivation capability
- Beautiful HTML email templates with meeting summary
- Slack Block Kit messages with action buttons
- Graceful fallback when integrations not configured
- Crown+ glassmorphism design throughout

**Files Created:**
- `routes/api_sharing.py` (290 lines) - Sharing API endpoints
- `services/share_service.py` (120 lines) - Share link management
- `services/email_service.py` (195 lines) - SendGrid email service
- `services/slack_service.py` (175 lines) - Slack webhook integration
- `static/js/sharing.js` (310 lines) - Share modal interactions
- `static/css/sharing.css` (480 lines) - Share modal Crown+ styles
- `templates/share/session.html` - Public share view template
- `models/shared_link.py` - SharedLink database model

**Remaining in Group 4:**
- T2.24: Team sharing with role-based permissions
- T2.25: Share analytics tracking
- T2.29: Microsoft Teams integration
- T2.30: Notion integration
- T2.31: Google Docs integration

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application utilizes a layered architecture with Flask as the web framework and Socket.IO for real-time communication, following an application factory pattern. The frontend employs a "Crown+" design system with a dark theme, vanilla JavaScript, and Socket.IO client for a modern and accessible UI/UX.

**UI/UX Decisions:**
- **Crown+ Design System**: Glassmorphism effects, smooth animations, consistent design tokens.
- **Theming**: Dark theme, light mode support, system preference detection.
- **Responsiveness**: Mobile-first approach, tested across various breakpoints.
- **Accessibility**: WCAG 2.1 AA compliance, screen reader support, keyboard navigation, high contrast/large text modes.
- **UI States**: Comprehensive loading, empty, and error states with visual indicators.
- **Component Standardization**: Standardized modals, tooltips, forms, buttons, navigation, cards, tables, and badges.

**Technical Implementations & Feature Specifications:**
- **AI Intelligence**: Auto-summarization, key points, action items, questions, decisions, sentiment analysis, topic detection, language detection, custom AI prompts.
- **Sharing & Integrations**: Public sharing with privacy settings, embed functionality, email sharing (SendGrid), Slack integration (webhooks).
- **Real-time Audio Processing Pipeline**: Client-side VAD, WebSocket streaming, server-side processing, OpenAI Whisper API integration, real-time broadcasting.
- **Advanced AI Features**: Multi-speaker diarization, multi-language detection, adaptive VAD, real-time audio quality monitoring, confidence scoring.
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

**Production Infrastructure:**
- Gunicorn
- Eventlet

**Other Integrations:**
- SendGrid (for email sharing)
- Slack (for webhook integration)