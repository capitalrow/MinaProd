# Mina - Meeting Insights & Action Platform

## Overview

Mina is an enterprise-grade SaaS platform designed to transform meetings into actionable moments. It provides real-time transcription with speaker identification, voice activity detection, and AI-powered insights to generate comprehensive meeting summaries and extract actionable tasks. Its core purpose is to enhance productivity and streamline post-meeting workflows, aiming for a production-ready application with robust features and infrastructure.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application utilizes a layered architecture with Flask as the web framework and Socket.IO for real-time communication, following an application factory pattern.

**Core Components:**
-   **Backend**: Flask with Flask-SocketIO.
-   **Database**: SQLAlchemy ORM, supporting SQLite (development) and PostgreSQL (production).
-   **Real-time Communication**: Socket.IO for WebSocket streaming with polling fallback.
-   **Frontend**: Bootstrap dark theme with vanilla JavaScript and Socket.IO client, adhering to a "Crown+" design system for a modern UI/UX.

**Data Model:**
The system primarily uses two models:
-   **Session Model**: Stores meeting metadata, configuration, and real-time processing parameters.
-   **Segment Model**: Contains individual transcription segments, including text, confidence scores, speaker information, timing, and language detection.

**Real-time Audio Processing Pipeline:**
A multi-stage pipeline handles audio:
1.  **Audio Capture & VAD**: Client-side MediaRecorder API with Voice Activity Detection and noise reduction.
2.  **Audio Buffering & Streaming**: Intelligent buffering and optimized WebSocket transmission via Socket.IO.
3.  **Server-side Processing**: Audio format conversion and data preparation.
4.  **Whisper Integration**: Streaming transcription via OpenAI Whisper API.
5.  **Real-time Broadcasting**: Results broadcast to clients via WebSocket.

**Service Layer:**
Business logic is organized into services like `TranscriptionService`, `VADService`, `WhisperStreamingService`, and `AudioProcessor`.

**Architectural Decisions & Features:**
-   **Production Readiness**: Focus on scalability, security, and reliability.
-   **Background Worker System**: Non-blocking transcription processing with thread pools.
-   **Continuous Audio Processing**: Overlapping context windows and sliding buffer management.
-   **Advanced Deduplication**: Text stability analysis and segment confirmation.
-   **Redis-based Scaling**: Horizontal Socket.IO scaling and distributed room management.
-   **WebSocket Reliability**: Auto-reconnection, heartbeat monitoring, and session recovery.
-   **Fault Tolerance**: Automatic session state checkpointing with Redis.
-   **Security & Authentication**: JWT-based authentication with RBAC, bcrypt password hashing, AES-256 encryption.
-   **Advanced Features**: Multi-speaker diarization, multi-language detection, adaptive VAD, real-time audio quality monitoring, and advanced confidence scoring.
-   **Accessibility & UX**: WCAG 2.1 AA compliance, screen reader support, keyboard navigation, high contrast/large text modes, and a consistent "Crown+" design system with 3 theme variants.
-   **Performance**: Achieved low Word Error Rate (WER) and sub-400ms end-to-end transcription latency.

**Development Strategy:**
A "Hybrid Approach" balances user-visible progress with production infrastructure. The roadmap includes phases for management/settings pages, codebase cleanup, quality/polish, critical foundation (testing, monitoring, security, CI/CD), SaaS business pages, and collaboration features.

## Recent Changes

### Phase 1: Management & Settings Pages (October 2025) - COMPLETED
**Status**: 7 of 8 tasks complete (1 deferred to Phase 6)

**Completed Crown+ Transformations:**
- ✅ **Profile/Account Settings** (P1-T1): Personal info forms, password change, avatar upload with validation and AJAX submissions
- ✅ **Preferences Page** (P1-T3): 4-tab interface (Transcription, Notifications, Privacy, Appearance) with API persistence and proper value conversions
- ✅ **Integrations Page** (P1-T4): 8 third-party services (Google Calendar, Outlook, Slack, Notion, Linear, Jira, GitHub, Zapier) with persistent connect/disconnect states
- ✅ **Calendar Page** (P1-T5): Monthly grid view with meeting indicators, month navigation with proper event refetching, sync status sidebar
- ✅ **Analytics Page** (P1-T6): 4 metric cards + 4 Chart.js visualizations (2 real data, 2 mock), time range selector, mobile responsive
- ✅ **Mobile Navigation** (P1-T7): Slide-in hamburger menu with Crown+ glass morphism, touch-friendly targets, accessibility support

**Deferred:**
- ⏸️ **Workspace Management** (P1-T2): Basic UI complete, full invite/permission system deferred to Phase 6 (Collaboration Features)

**Crown+ Design System Applied:**
- Glass morphism backgrounds with backdrop blur
- Purple accent color (#8b5cf6) throughout
- Feather icons loaded globally in base.html
- Breadcrumb navigation on all settings pages
- Consistent card layouts and spacing
- Mobile-first responsive design
- Accessibility: ARIA labels, keyboard navigation, reduced motion support

**Known Issues for Follow-up:**
- Mobile menu hamburger may have z-index/positioning issue preventing clicks on some viewports (functionality implemented, CSS needs refinement)
- Mock data in 2/4 analytics charts (Duration Analysis, Status Distribution) - backend API extension needed
- CSRF protection needed for JSON POST endpoints (deferred to Phase 3)

## External Dependencies

**AI/ML Services:**
-   OpenAI Whisper API
-   WebRTC MediaRecorder

**Database Systems:**
-   PostgreSQL
-   SQLAlchemy
-   Redis

**Real-time Communication:**
-   Socket.IO with Redis Adapter
-   Flask-SocketIO

**Security & Authentication:**
-   Flask-Login
-   Cryptography
-   bcrypt
-   PyJWT

**Audio Processing Libraries:**
-   NumPy/SciPy
-   WebRTCVAD
-   PyDub

**Web Framework Dependencies:**
-   Flask
-   Bootstrap
-   WhiteNoise
-   ProxyFix

**Production Infrastructure:**
-   Gunicorn
-   Eventlet