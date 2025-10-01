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

### Phase 0: Foundation & Quality Infrastructure (October 2025) - IN PROGRESS
**Status**: 19 of 45 tasks complete (42%)

**Testing Infrastructure (Tasks 0.1, 0.2, 0.6, 0.7, 0.9):**
- ✅ **pytest Setup** (T0.1): pytest-cov, pytest-mock, pytest-flask, pytest-html, pytest-playwright installed; pytest.ini with 80% coverage threshold, --cov-append, test markers, HTML/XML reports to tests/results/; .coveragerc scoped to application code
- ✅ **Playwright E2E** (T0.2): Playwright 1.55.0 with comprehensive async fixtures in tests/setup/conftest.py; mobile testing (iPhone 13), video recording always enabled, async screenshot-on-failure with error handling
- ✅ **Test Data Factories** (T0.6): 8 factories (User, Session, Segment, Meeting, Summary, Task, Workspace, Participant) using factory-boy and faker; batch creation helpers; complete meeting data generator; 9/9 tests passing
- ✅ **Integration Tests** (T0.7): tests/conftest.py with Flask app fixture using create_app() and test database; tests/integration/test_api_sessions.py with API endpoint tests; 4/4 passing
- ✅ **CI/CD Pipeline** (T0.9): .github/workflows/ci.yml with 3 jobs: test (unit+integration with Postgres 13, DB init, coverage to Codecov), lint (Ruff+Black), security (Safety+Bandit with JSON reports); complements existing e2e-tests.yml; 18/18 tests passing

**Security & Authentication (Tasks 0.10, 0.11, 0.12, 0.13, 0.14, 0.20):**
- ✅ **Database Migrations** (T0.10): Flask-Migrate (Alembic) with lightweight app factory, all commands functional (<2s execution), circular imports fixed, comprehensive documentation (docs/database/MIGRATION-WORKFLOW.md)
- ✅ **Rate Limiting** (T0.11): 100 req/min per IP via middleware/limits.py, Redis-backed tracking, configurable limits by endpoint type
- ✅ **CSP Headers** (T0.12): Content-Security-Policy via middleware/csp.py, nonce-based script execution, strict resource loading policies
- ✅ **OWASP Audit** (T0.13): Security scan completed, findings documented, high-priority issues resolved
- ✅ **Session Security** (T0.14): 30min idle timeout, 8h absolute timeout, session rotation on login, fixation prevention, secure cookies (HTTPOnly, SameSite=Lax)
- ✅ **CSRF Protection** (T0.20): Flask-WTF CSRFProtect globally initialized, csrf.js auto-injects X-CSRFToken headers, HTML forms protected, Socket.IO exempted, tested working (docs/security/CSRF-PROTECTION.md)

**Secrets & Key Management (Tasks 0.15, 0.18):**
- ✅ **Secrets Scanning** (T0.15): git-secrets hooks, automated scanning in CI/CD, SECRET_KEY validation
- ✅ **API Key Rotation** (T0.18): 30/90/365-day rotation schedules, GPG AES256-encrypted backups (GPG_BACKUP_PASSPHRASE), dual-key support (API_SECRET_KEY + API_SECRET_KEY_OLD), scripts/rotate_secrets.sh automation, comprehensive documentation (docs/security/API-KEY-ROTATION.md)

**Monitoring & Observability (Tasks 0.16, 0.17, 0.19, 0.21, 0.29):**
- ✅ **Sentry Error Tracking** (T0.16): SENTRY_DSN integration, error aggregation, stack traces, release tracking
- ✅ **Sentry APM** (T0.17): Performance monitoring, transaction tracing, 10% sample rate, profiling enabled
- ✅ **Uptime Monitoring** (T0.19): BetterStack integration, /ops/health endpoint, multi-region checks
- ✅ **Structured Logging** (T0.21): JSON logging (JSON_LOGS env var), comprehensive fields (timestamp, hostname, process/thread IDs, HTTP context, user context, exceptions), Sentry integration, 700+ line documentation (docs/monitoring/STRUCTURED-LOGGING.md)
- ✅ **SLO/SLI Metrics** (T0.29): 5 core SLIs defined (availability, latency, error rate, throughput, data quality), concrete targets per service (Web 99.9%, API 99.95%, DB 99.99%), error budget framework with burn-rate alerting, monitoring integration (Sentry, BetterStack, Grafana), SLO review processes, scripts/check_error_budget.sh, comprehensive documentation (docs/monitoring/SLO-SLI-METRICS.md)

**Incident Response (Task 0.23):**
- ✅ **Security Incident Response** (T0.23): 800+ line incident response plan (docs/security/INCIDENT-RESPONSE.md), P0-P3 classification with SLAs (<15min for P0), 5-phase lifecycle (Detection, Containment, Eradication, Recovery, Post-Incident), GDPR/CCPA/HIPAA compliance, communication protocols, forensic procedures, contact information, tabletop exercises

**Documentation & Files Created:**
- docs/database/MIGRATION-WORKFLOW.md: Database migration procedures
- docs/security/CSRF-PROTECTION.md: CSRF implementation and testing
- docs/security/API-KEY-ROTATION.md: Key rotation schedules and procedures
- docs/security/INCIDENT-RESPONSE.md: Comprehensive incident response plan
- docs/monitoring/STRUCTURED-LOGGING.md: Logging architecture and usage
- docs/monitoring/SLO-SLI-METRICS.md: Service level objectives and indicators
- scripts/rotate_secrets.sh: Automated secret rotation with GPG encryption
- scripts/check_error_budget.sh: SLO compliance and error budget tracking
- tests/conftest.py, tests/factories.py: Test infrastructure
- .github/workflows/ci.yml: CI/CD pipeline

**Test Results:**
- 18 tests passing (9 unit + 4 integration + 5 app basic)
- Coverage enforced at 80% minimum
- All infrastructure architect-reviewed and approved

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