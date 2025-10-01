# Mina - Meeting Insights & Action Platform

## Overview

Mina is an enterprise-grade SaaS platform designed to transform meetings into actionable moments. It provides real-time transcription with speaker identification, voice activity detection, and AI-powered insights to generate comprehensive meeting summaries and extract actionable tasks. Its core purpose is to enhance productivity and streamline post-meeting workflows, aiming for a production-ready application with robust features and infrastructure. The business vision is to deliver a cutting-edge platform that significantly improves post-meeting productivity, tapping into the growing market for AI-powered business tools.

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
-   **Production Readiness**: Focus on scalability, security, reliability, and fault tolerance with Redis for horizontal scaling, distributed room management, and session state checkpointing.
-   **Background Processing**: Non-blocking transcription using thread pools.
-   **Continuous Audio Processing**: Overlapping context windows and sliding buffer management.
-   **Advanced Deduplication**: Text stability analysis.
-   **WebSocket Reliability**: Auto-reconnection, heartbeat monitoring, and session recovery.
-   **Security & Authentication**: JWT-based authentication with RBAC, bcrypt, AES-256 encryption, rate limiting, CSP headers, and CSRF protection.
-   **Advanced AI Features**: Multi-speaker diarization, multi-language detection, adaptive VAD, real-time audio quality monitoring, and confidence scoring.
-   **Accessibility & UX**: WCAG 2.1 AA compliance, screen reader support, keyboard navigation, high contrast/large text modes, and a consistent "Crown+" design system with 3 theme variants.
-   **Performance**: Achieves low Word Error Rate (WER) and sub-400ms end-to-end transcription latency.
-   **Monitoring & Observability**: Sentry for error tracking and APM, BetterStack for uptime monitoring, structured JSON logging, and defined SLO/SLI metrics.
-   **Backup & Disaster Recovery**: Automated PostgreSQL backups with GPG AES256 encryption, multi-tier retention, and documented RPO/RTO targets (<5min / <30min).

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