# Mina - Meeting Insights & Action Platform

## Overview

Mina is an enterprise-grade SaaS platform designed to transform meetings into actionable moments. It provides real-time transcription with speaker identification, voice activity detection, and AI-powered insights to generate comprehensive meeting summaries and extract actionable tasks. Its core purpose is to enhance productivity and streamline post-meeting workflows, aiming for a production-ready application with robust features and infrastructure. The business vision is to deliver a cutting-edge platform that significantly improves post-meeting productivity, tapping into the growing market for AI-powered business tools.

## Recent Development Progress (October 2025)

**Phase 1: Design System - ✅ COMPLETE (32/32 tasks - 100%)**
**Phase 2: Transcript Experience - 🔄 IN PROGRESS (22/31 tasks - 71%)**

### Phase 2 Group 3: AI Intelligence - ✅ COMPLETE (12/12 tasks - 100%)

**Completed (T2.11-T2.22):**
- Auto-summarization with GPT-4 Turbo
- Key points extraction (5-10 points with importance ranking)
- Action items extraction (who, what, when, priority)
- Questions extraction (answered/unanswered status)
- Decisions extraction (with rationale and impact)
- Sentiment analysis (positive/neutral/negative with score)
- Topic detection and filtering
- Language detection support
- Custom AI prompts with 5 templates
- Cost optimization (8K token limit, efficient prompting)
- Quality feedback system (thumbs up/down)
- Confidence indicators (visual 3-dot system)

**Files Created:**
- `services/ai_insights_service.py` (420 lines) - AI analysis service
- `routes/api_ai_insights.py` (360 lines) - REST API endpoints
- `static/css/ai-insights.css` (750+ lines) - Crown+ styled components
- `static/js/ai-insights.js` (630+ lines) - Interactive AI insights manager
- Integrated into `templates/dashboard/meeting_detail.html` with 8-tab interface

**Technical Implementation:**
- GPT-4 Turbo Preview model
- Structured JSON responses
- Token truncation at 8K characters
- Synchronous OpenAI client
- Glassmorphism design throughout
- Mobile-responsive layouts
- Fixed interaction bugs (currentTarget vs target)

**Phase 1: Design System - ✅ COMPLETE (32/32 tasks - 100%)**

Enhanced pages now following Crown+ design system with glassmorphism effects, smooth animations, and consistent design token usage:

1. **Dashboard** (T1.7) - Complete
   - KPI cards with glassmorphism effects and gradient accents
   - Fade-in animations with stagger effect
   - Mobile-responsive grid layout
   - Proper design token integration

2. **Meetings List** (T1.8) - Complete
   - Meeting cards with glassmorphism background
   - Smooth hover lift effects and transitions
   - Stagger animations for card appearance
   - Consistent spacing and typography

3. **Meeting Detail** (T1.9) - Complete
   - Interactive timeline with smooth scroll
   - Glassmorphism transcript display with speaker avatars
   - Enhanced action buttons with hover effects
   - Responsive layout for all screen sizes

4. **Analytics** (T1.10) - Complete
   - KPI cards with glassmorphism and gradient overlays
   - Chart containers with proper backdrop blur
   - Tab navigation with smooth transitions
   - Comprehensive Chart.js integration
   - Insights section with actionable recommendations
   - Fixed CSP nonce issue for inline scripts

5. **Tasks** (T1.11) - Complete
   - Glassmorphism task cards with status indicators
   - Priority badges with gradient accents (high/medium/low)
   - Interactive filter tabs with counters
   - Smooth hover effects and border animations
   - Stagger animations for card appearance
   - Completed/pending task visual distinction
   - Mobile-responsive layout with flex-wrap

6. **Calendar** (T1.12) - Complete
   - Calendar grid with glassmorphism day cells
   - Event indicators and today highlighting
   - Upcoming events list with colored indicators
   - Smooth hover effects and animations
   - Empty state with call-to-action
   - Navigation controls for month browsing
   - Calendar link added to main navigation

7. **Settings Pages** (T1.13) - Complete
   - All 4 settings pages enhanced: Preferences, Profile, Integrations, Workspace
   - Created shared `static/css/settings.css` for consistency
   - Settings-specific component classes: `.settings-card`, `.integration-card`
   - Gradient card titles with webkit background clip
   - Glassmorphism effects across all settings sections
   - Tab navigation with active state indicators
   - Mobile-responsive layouts for all settings pages

8. **Copilot/Chat** (T1.14) - Complete
   - Centered workspace with responsive max-width constraints
   - Glassmorphism chat bubbles with proper width limits
   - Smooth message animations
   - Responsive breakpoints (≤1280px, ≤1024px, ≤768px)
   - Created shared `static/css/copilot.css` for consistency

9. **Auth Pages** (T1.15) - Complete
   - Login and Register pages enhanced with Crown+ quality
   - Enhanced glassmorphism card effects with hover states
   - Animated gradient backgrounds (15s shift animation)
   - Interactive feature/benefit cards with lift effects
   - Button shine effects on primary CTAs
   - Friendly messaging and professional first impression

10. **Landing Page** (T1.16) - Complete
    - Glassmorphism hero section with pulsing glow effect
    - Smooth fade-in animations with stagger delays
    - Interactive feature cards with hover states and icon rotation
    - Button shine effects on CTAs
    - Multi-color radial gradient backgrounds
    - Responsive design with clamp() for fluid typography
    - Clean semantic CSS replacing inline styles

11. **Error Pages** (T1.17) - Complete
    - Enhanced 404 page with Crown+ quality
    - Glassmorphism icon wrapper with bouncing animation
    - Floating gradient glows in background
    - Large gradient error code text
    - Helpful resource links with hover effects
    - Friendly, reassuring messaging
    - Button shine effects on CTAs

12. **Share Pages** (T1.18) - Complete
    - Created `templates/share/session.html` for shared meeting view
    - Created `templates/share/expired.html` for invalid/expired links
    - Public-friendly Crown+ design with glassmorphism
    - Transcript display with speaker avatars
    - Summary sections with gradient accents
    - Branded CTA footer with feature showcase
    - Helpful expiration explanations
    - Responsive mobile-first layouts

13. **UI States** (T1.19-T1.21) - Complete
    - **Loading States**: Created `loading-states.css` with skeleton loaders, spinners, pulse animations, and progress bars
    - **Empty States**: Created `empty-states.css` with interactive empty states for all page types (meetings, tasks, calendar, search)
    - **Error States**: Created `error-states.css` with error banners, toasts, inline errors, and retry functionality

14. **Component Standardization** (T1.22-T1.29) - Complete
    - Comprehensive `components.css` with all standardized UI components:
    - **Modals/Dialogs**: Glassmorphism overlays with smooth animations
    - **Tooltips**: Four-directional positioning (top/bottom/left/right)
    - **Forms**: Glassmorphism inputs, textareas, selects with validation states
    - **Buttons**: Primary, secondary, tertiary, danger variants with shine effects
    - **Navigation**: Sidebar and breadcrumb components
    - **Cards**: Interactive glassmorphism cards with headers and footers
    - **Tables**: Glassmorphism containers with sortable headers
    - **Badges/Chips**: Six color variants with consistent sizing

15. **Theme System** (T1.30) - Complete
    - Created `theme-toggle.js` with localStorage persistence
    - Created `theme-light.css` with full light mode support
    - Theme toggle button integrated in navigation
    - System preference detection with auto-switching

16. **Responsive Design** (T1.31) - Complete
    - All components tested across breakpoints: 375px, 768px, 1024px, 1440px
    - Mobile-first approach with @media queries
    - Flexible layouts with clamp() and grid/flexbox
    - Touch-friendly button sizes (min 44px)

17. **Documentation** (T1.32) - Complete
    - Inline documentation in all CSS files
    - Clear component descriptions and usage examples
    - Comprehensive code comments

**Design System Consistency:**
- All enhanced pages use `var(--glass-bg)` and `var(--backdrop-blur)` for glassmorphism
- Gradient accents using Crown+ color palette (purple, cyan, pink)
- Fade-in animations with CSS keyframes
- Consistent component classes: `.kpi-card`, `.chart-card`, `.meeting-card`, `.settings-card`, `.integration-card`

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application utilizes a layered architecture with Flask as the web framework and Socket.IO for real-time communication, following an application factory pattern. The frontend employs a "Crown+" design system with a dark theme, vanilla JavaScript, and Socket.IO client for a modern and accessible UI/UX.

**Core Components:**
-   **Backend**: Flask with Flask-SocketIO.
-   **Database**: SQLAlchemy ORM, supporting SQLite (development) and PostgreSQL (production).
-   **Real-time Communication**: Socket.IO for WebSocket streaming with polling fallback.
-   **Frontend**: Bootstrap dark theme with vanilla JavaScript, Socket.IO client, and a "Crown+" design system.

**Data Model:**
-   **Session Model**: Stores meeting metadata and configuration.
-   **Segment Model**: Contains individual transcription segments (text, confidence, speaker, timing, language).

**Real-time Audio Processing Pipeline:**
The pipeline includes client-side audio capture with VAD, intelligent buffering and WebSocket streaming, server-side audio processing, OpenAI Whisper API integration for transcription, and real-time broadcasting of results.

**Service Layer:**
Business logic is encapsulated in services like `TranscriptionService`, `VADService`, `WhisperStreamingService`, and `AudioProcessor`.

**Architectural Decisions & Features:**
-   **Production Readiness**: Focus on scalability, security, reliability, and fault tolerance with Redis for horizontal scaling, distributed room management, and session state checkpointing. Includes robust error handling with background task retry systems and Redis failover management.
-   **Background Processing**: Non-blocking transcription using thread pools.
-   **Continuous Audio Processing**: Overlapping context windows and sliding buffer management.
-   **Advanced Deduplication**: Text stability analysis.
-   **WebSocket Reliability**: Auto-reconnection, heartbeat monitoring, and session recovery.
-   **Security & Authentication**: JWT-based authentication with RBAC, bcrypt, AES-256 encryption, rate limiting, CSP headers, CSRF protection, and comprehensive input validation.
-   **Advanced AI Features**: Multi-speaker diarization, multi-language detection, adaptive VAD, real-time audio quality monitoring, and confidence scoring.
-   **Accessibility & UX**: WCAG 2.1 AA compliance, screen reader support, keyboard navigation, high contrast/large text modes, and a consistent "Crown+" design system with 3 theme variants and comprehensive design tokens.
-   **Performance**: Achieves low Word Error Rate (WER) and sub-400ms end-to-end transcription latency. Database performance optimized with extensive indexing across key models.
-   **Monitoring & Observability**: Sentry for error tracking and APM, BetterStack for uptime monitoring, structured JSON logging, and defined SLO/SLI metrics.
-   **Backup & Disaster Recovery**: Automated PostgreSQL backups with GPG AES256 encryption, multi-tier retention, and documented RPO/RTO targets (<5min / <30min).
-   **Deployment**: CI/CD pipeline with GitHub Actions, Alembic migrations, blue-green deployment, and rollback procedures.

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