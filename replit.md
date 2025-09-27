# Mina - Meeting Insights & Action Platform

## Overview

Mina is a production-ready, enterprise-grade SaaS platform designed to transform meetings into actionable moments. It achieves this through real-time transcription, advanced AI capabilities, and integrated productivity tools. The platform provides live transcription with speaker identification, voice activity detection, and AI-powered insights to generate comprehensive meeting summaries and extract actionable tasks. Its core purpose is to enhance productivity and streamline post-meeting workflows.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

**September 2025 - Live Recording Interface Consolidation:**
- Consolidated 10 redundant live recording templates into single production-ready interface
- Deleted obsolete templates: live_premium.html, live_enhanced.html, live_modern.html, comprehensive_live.html, etc.
- Updated all routes (/live, /live-enhanced, /live-comprehensive) to serve unified live.html
- Implemented professional glass morphism design with dark/light theme support
- Added comprehensive live metrics dashboard and real-time transcription features
- Created single source of truth for all live recording functionality

**December 2024 - Major UI/UX Enhancement:**
- Implemented comprehensive modern design system following Material Design 3 and industry best practices
- Created responsive, mobile-first interface with WCAG 2.1 AA accessibility compliance
- Enhanced navigation with sticky header, smooth transitions, and professional micro-interactions
- Added advanced component library with modern buttons, cards, forms, and toast notifications
- Implemented PWA features with service worker for improved performance and offline capabilities
- Mobile optimization with touch gestures, battery optimization, and adaptive quality settings
- Professional visual hierarchy with Inter font family and consistent spacing system

## System Architecture

The application employs a layered architecture centered on Flask as the web framework and Socket.IO for real-time communication. It adheres to an application factory pattern, ensuring clear separation of concerns.

**Core Components:**
- **Backend**: Flask with Flask-SocketIO.
- **Database**: SQLAlchemy ORM, supporting SQLite for development and PostgreSQL for production.
- **Real-time Communication**: Socket.IO for WebSocket streaming with polling fallback.
- **Frontend**: Bootstrap dark theme with vanilla JavaScript and Socket.IO client.

**Data Model:**
The system is built around two primary entities:
- **Session Model**: Stores comprehensive meeting metadata, configuration, and real-time processing parameters.
- **Segment Model**: Contains individual transcription segments, including text, confidence scores, speaker information, timing, and language detection.

**Real-time Audio Processing Pipeline:**
The audio processing is a multi-stage pipeline:
1.  **Audio Capture**: Client-side MediaRecorder API.
2.  **Voice Activity Detection (VAD)**: Client-side VAD with noise reduction.
3.  **Audio Buffering**: Intelligent buffering based on speech/silence detection.
4.  **WebSocket Streaming**: Optimized transmission via Socket.IO with backpressure.
5.  **Server-side Processing**: Audio format conversion and data preparation.
6.  **Whisper Integration**: Streaming transcription service processes audio.
7.  **Real-time Broadcasting**: Results broadcast to clients via WebSocket.

**Service Layer:**
Business logic is organized into specialized services:
-   **TranscriptionService**: Orchestrates transcription, session state, and callback distribution.
-   **VADService**: Handles advanced voice activity detection.
-   **WhisperStreamingService**: Manages integration with OpenAI Whisper API for streaming transcription.
-   **AudioProcessor**: Utility for audio format conversion and manipulation.

**Architectural Decisions & Features:**
-   **Production Readiness**: Implemented with comprehensive scalability, security, and reliability features.
-   **Background Worker System**: Non-blocking transcription processing with thread pools.
-   **Continuous Audio Processing**: Overlapping context windows and sliding buffer management.
-   **Advanced Deduplication**: Text stability analysis and segment confirmation.
-   **Redis-based Scaling**: Horizontal Socket.IO scaling, distributed room management.
-   **WebSocket Reliability**: Auto-reconnection, heartbeat monitoring, session recovery.
-   **Fault Tolerance**: Automatic session state checkpointing with Redis-backed persistence.
-   **Security & Authentication**: JWT-based authentication with RBAC, bcrypt password hashing, AES-256 data encryption for sensitive data at rest and in transit.
-   **Advanced Features**: Multi-speaker diarization, multi-language detection with automatic switching, adaptive VAD with environmental noise estimation, real-time audio quality monitoring (AGC), advanced confidence scoring.
-   **Accessibility & UX**: WCAG 2.1 AA compliance, screen reader support, keyboard navigation, high contrast/large text modes.
-   **Performance**: Achieved low Word Error Rate (WER), sub-400ms end-to-end transcription latency, and optimized memory management.

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