# Mina - Meeting Insights & Action Platform

## Overview

Mina is a next-generation SaaS platform that transforms meetings into actionable moments through real-time transcription, advanced AI capabilities, and integrated productivity tools. The platform combines live transcription with speaker identification, voice activity detection, and AI-powered insights to create comprehensive meeting summaries and extract actionable tasks.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern

The application follows a layered architecture pattern using Flask as the web framework with Socket.IO for real-time communication. The system is designed around the application factory pattern with clear separation of concerns across multiple layers.

**Framework Stack:**
- **Backend**: Flask with Flask-SocketIO for WebSocket support
- **Database**: SQLAlchemy ORM with configurable database backends (SQLite for development, supports PostgreSQL for production)
- **Real-time Communication**: Socket.IO with WebSocket streaming and polling fallback
- **Frontend**: Bootstrap dark theme with vanilla JavaScript and Socket.IO client

### Database Schema Design

The data model centers around two core entities:

**Session Model**: Represents meeting sessions with comprehensive metadata including timing, configuration, and processing statistics. Stores real-time settings like VAD sensitivity, confidence thresholds, and audio processing parameters.

**Segment Model**: Represents individual transcription segments within a session. Each segment contains transcribed text, confidence scores, speaker information, timing data, and language detection results.

### Real-time Audio Processing Pipeline

The audio processing follows a sophisticated multi-stage pipeline:

1. **Audio Capture**: Client-side MediaRecorder API captures audio with WebRTC
2. **Voice Activity Detection (VAD)**: Advanced client-side VAD processing with noise reduction and energy analysis
3. **Audio Buffering**: Intelligent buffering system that accumulates audio chunks based on speech/silence detection
4. **WebSocket Streaming**: Optimized transmission of audio data via Socket.IO with backpressure handling
5. **Server-side Processing**: Audio processor converts formats and prepares data for transcription
6. **Whisper Integration**: Streaming transcription service processes audio chunks and returns results
7. **Real-time Broadcasting**: Transcription results are broadcast back to clients via WebSocket

### Service Layer Architecture

The business logic is organized into specialized service classes:

**TranscriptionService**: High-level orchestrator that coordinates all transcription operations, manages session state, and handles callback distribution.

**VADService**: Advanced voice activity detection with sophisticated algorithms for speech/silence classification, noise estimation, and confidence scoring.

**WhisperStreamingService**: Manages integration with OpenAI Whisper API, handles chunk processing, and provides streaming transcription capabilities.

**AudioProcessor**: Utility service for audio format conversion, signal processing, and audio manipulation tasks.

### Real-time Communication Design

Socket.IO is configured with specific optimizations for real-time audio streaming:
- Threading async mode for Flask compatibility
- CORS configuration for cross-origin requests
- WebSocket with polling fallback for reliable connections
- Custom event handlers for session management and audio streaming

### Configuration Management

Environment-based configuration system supports development and production deployments with settings for:
- Database connections with connection pooling
- Real-time transcription parameters
- VAD sensitivity and thresholds
- Audio processing configuration
- OpenAI API integration

### Frontend Architecture

Client-side architecture uses modular JavaScript classes:
- **RealTimeTranscription**: Main application controller
- **VADProcessorAdvanced**: Client-side voice activity detection
- **WebSocketStreaming**: Audio streaming and connection management
- Bootstrap dark theme for consistent UI/UX

## External Dependencies

### AI/ML Services
- **OpenAI Whisper API**: Primary transcription engine for speech-to-text conversion
- **WebRTC MediaRecorder**: Browser-based audio capture and processing

### Database Systems
- **SQLite**: Default development database with support for PostgreSQL in production
- **SQLAlchemy**: ORM layer with relationship management and query optimization

### Real-time Communication
- **Socket.IO**: WebSocket communication with polling fallback
- **Flask-SocketIO**: Server-side Socket.IO integration for Flask

### Audio Processing Libraries
- **NumPy/SciPy**: Audio signal processing and analysis
- **WebRTCVAD**: Voice activity detection algorithms
- **PyDub**: Audio format conversion and manipulation

### Web Framework Dependencies
- **Flask**: Core web framework with templating and routing
- **Bootstrap**: UI framework with dark theme support
- **WhiteNoise**: Static file serving for production deployments
- **ProxyFix**: Request handling behind reverse proxies

### Development and Testing
- **pytest**: Testing framework with async support
- **pytest-flask**: Flask-specific testing utilities
- **pytest-socketio**: Socket.IO testing capabilities

### Production Infrastructure
- **Gunicorn**: WSGI server for production deployment
- **Eventlet**: Async worker support for Socket.IO
- **Redis**: Optional session storage and message queuing