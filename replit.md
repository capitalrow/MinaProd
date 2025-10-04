# Mina - Meeting Insights & Action Platform

## Overview

Mina is an enterprise-grade SaaS platform designed to transform meetings into actionable moments. It provides real-time transcription with speaker identification, voice activity detection, and AI-powered insights to generate comprehensive meeting summaries and extract actionable tasks. Its core purpose is to enhance productivity and streamline post-meeting workflows, aiming for a production-ready application with robust features and infrastructure. The business vision is to deliver a cutting-edge platform that significantly improves post-meeting productivity, tapping into the growing market for AI-powered business tools.

## Recent Development Progress (October 2025)

**Phase 1: Design System - ✅ COMPLETE (32/32 tasks - 100%)**
**Phase 2: Transcript Experience - ✅ COMPLETE (43/43 tasks - 100%)**
**Phase 2.3: Analytics - ✅ COMPLETE (9/9 tasks - 100%)**
**Overall Progress: 179/268 tasks (66.8%)**

### Phase 2 Group 2: AI Intelligence - ✅ COMPLETE (12/12 tasks - 100%)

**Completed Features (T2.11-T2.22):**
- ✅ Auto-summarization with 3-paragraph meeting summaries
- ✅ Key points extraction (5-10 actionable insights per meeting)
- ✅ Action items extraction with assignee, priority, due dates
- ✅ Questions tracking (asked vs answered status)
- ✅ Decisions extraction with rationale and impact analysis
- ✅ Sentiment analysis with overall score and key moments
- ✅ Topic detection (main discussion themes)
- ✅ Language detection with confidence scoring
- ✅ Custom AI prompts for user-defined analysis
- ✅ Cost optimization with token limits and batching
- ✅ Quality scoring system (0.0-0.95 confidence)
- ✅ Confidence indicators in all AI responses

**Implementation Details:**
- Comprehensive AI service using OpenAI GPT-4 Turbo
- Single optimized API call for all insights (cost-efficient)
- Individual endpoints for granular control
- JSON-structured responses for consistent parsing
- Fallback handling when API key not configured
- Token optimization (~8K char limit per request)
- Temperature tuning per analysis type
- Error handling with graceful degradation

**Files Created/Enhanced:**
- `services/ai_insights_service.py` (450+ lines) - Complete AI intelligence layer
- `routes/api_ai_insights.py` (380+ lines) - REST API for all AI features
- Endpoints: /ai/insights, /ai/summary, /ai/key-points, /ai/action-items, /ai/questions, /ai/decisions, /ai/sentiment, /ai/topics, /ai/language, /ai/custom-prompt, /ai/cost-estimate

### Phase 2.3: Analytics Dashboard - ✅ COMPLETE (9/9 tasks - 100%)

**Completed Features (T2.32-T2.40):**
- ✅ Speaking time distribution analysis with bar and pie charts
- ✅ Participation balance metrics with 6-dimensional scoring system
- ✅ Sentiment analysis tracking across meetings
- ✅ Topic trend analysis with timeline visualization
- ✅ Question/Answer tracking with answer detection heuristics
- ✅ Action items completion rate dashboard
- ✅ Analytics export functionality (JSON format)
- ✅ Custom analytics widgets with toggle interface and localStorage persistence

**Implementation Details:**
- Enhanced analytics.js (1300+ lines) with Chart.js visualizations
- 10 API endpoints for granular analytics data
- Speaking time analysis: Bar chart + pie chart with percentage breakdowns
- Participation balance: 6-dimensional scoring (Productivity 25%, Time 15%, Participation 15%, Engagement 15%, Preparation 15%, Decision 15%)
- Topic trends: 5-minute time windows with AI topic extraction
- Q&A tracking: Question detection with answer pattern matching
- Widget customization: 14 widgets grouped by category (KPIs, Charts, Engagement, Productivity)
- All widgets have data-widget attributes for show/hide functionality
- Reset functionality with immediate DOM updates

**Files Created/Enhanced:**
- `services/analytics_service.py` - Enhanced with topic trends, Q&A analytics methods
- `routes/api_analytics.py` - Added endpoints for topic-trends, questions, action-items-completion
- `static/js/analytics.js` (1300+ lines) - Widget customization system, data fetching
- `templates/dashboard/analytics.html` - Widget attributes, customization modal
- `static/css/analytics.css` - Crown+ glassmorphism styles for analytics

**Latest Updates (Oct 4, 2025):**
- ✅ Widget customization modal with categorized toggles
- ✅ All widgets have data-widget attributes for DOM manipulation
- ✅ Reset functionality immediately applies preferences
- ✅ localStorage persistence for user preferences
- ✅ Production-ready with architect approval

### Phase 2 Group 4: Sharing & Integrations - ✅ COMPLETE (6/9 tasks - 67%)

**Completed Features (T2.23-T2.28):**
- ✅ Public sharing with link generation, privacy settings, expiration (1-90 days)
- ✅ Embed functionality with responsive iframe code generation  
- ✅ Email sharing with SendGrid integration (multiple recipients)
- ✅ Slack integration with webhook posting and Block Kit formatting
- ✅ Team sharing with role-based permissions (viewer/editor/admin)
- ✅ Share analytics tracking (views, unique visitors, referrers)

**Implementation Details:**
- Share modal with 3 tabs: Link, Email, Embed
- Active shares management with deactivation capability
- Beautiful HTML email templates with meeting summary
- Slack Block Kit messages with action buttons
- Role-based access control for team collaboration
- Comprehensive analytics dashboard with visitor tracking
- Graceful fallback when integrations not configured
- Crown+ glassmorphism design throughout

**Files Created/Enhanced:**
- `routes/api_sharing.py` (490 lines) - Sharing & analytics API
- `services/share_service.py` (120 lines) - Share link management
- `services/email_service.py` (195 lines) - SendGrid email service
- `services/slack_service.py` (175 lines) - Slack webhook integration
- `models/team_share.py` - Team collaboration with roles
- `models/share_analytics.py` - View tracking and analytics
- `static/js/sharing.js` (310 lines) - Share modal interactions
- `static/css/sharing.css` (480 lines) - Share modal Crown+ styles
- `templates/share/session.html` - Public share view template

**Skipped (per user request):**
- T2.29: Microsoft Teams integration
- T2.30: Notion integration
- T2.31: Google Docs integration

### Phase 2 Group 1: Transcript Display - ✅ COMPLETE (10/10 tasks - 100%)

**Completed Features (T2.1-T2.10):**
- ✅ Enhanced transcript layout with glassmorphism, speaker labels, timestamps, confidence indicators
- ✅ Search functionality with real-time highlighting, prev/next navigation, result counter
- ✅ Export options (TXT, DOCX, PDF, JSON) with proper formatting
- ✅ Copy functionality (entire transcript or individual segments) with clipboard API
- ✅ Inline editing with double-click, auto-save, edit history tracking
- ✅ Speaker identification with color-coding, editable names, filter by speaker
- ✅ Highlight functionality (yellow/green/blue) with right-click menu, filter by color
- ✅ Comment functionality with dialog, load/submit, backend integration
- ✅ Playback sync with click-to-jump, auto-scroll during playback
- ✅ Comprehensive keyboard shortcuts (Ctrl+F, Space, Arrows, N/P, ?, ESC)

**Implementation Details:**
- Enhanced CSS with gradient backgrounds, pulsing confidence indicators
- Debounced search with regex matching and `<mark>` highlighting
- Full keyboard navigation with shortcut panel
- TranscriptManager class orchestrating all interactions
- Speaker legend with segment counts and filtering
- Context menu for quick actions (highlight, comment)
- Toast notifications for user feedback
- Responsive design for mobile/tablet

**Key Files:**
- `static/js/transcript.js` (1075 lines) - Complete transcript interaction system
- `static/css/transcript.css` (726 lines) - Enhanced Crown+ transcript styles
- `routes/api_transcript.py` (622 lines) - Export, edit, speaker, comment APIs with real DB persistence
- `models/comment.py` - Comment model with threaded replies support
- `templates/dashboard/meeting_detail.html` - Transcript UI integration

**Latest Updates (Oct 3, 2025):**
- ✅ Comment system upgraded from mock to real database persistence
- ✅ Comment model with user relationship, threading (parent_id), timestamps
- ✅ GET/POST endpoints now fully functional with database operations
- ✅ Support for threaded comment replies

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