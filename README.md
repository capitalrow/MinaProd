# Mina - Meeting Insights & Action Platform

A next-generation SaaS platform that transforms meetings into actionable moments, combining real-time transcription, advanced AI capabilities, and integrated productivity tools.

## 🚀 Features

### Core Real-time Capabilities
- **Live Transcription**: High-accuracy real-time transcription with WebSocket streaming
- **Speaker Identification**: Automatic speaker detection and tagging
- **Voice Activity Detection (VAD)**: Intelligent audio processing with noise reduction
- **Live Editable Notes**: Real-time collaborative editing during meetings

### AI-Powered Insights
- **Actionable Summaries**: AI-generated meeting summaries with key insights
- **Task Extraction**: Automatic identification and prioritization of action items
- **Sentiment Analysis**: Conversational tone analysis for engagement insights
- **Impact Scoring**: Priority-based task ranking for effective follow-ups

### Production-Ready Infrastructure
- **Flask + Socket.IO**: EventLoop-based WebSocket handling with eventlet
- **PostgreSQL Database**: Scalable data storage with SQLAlchemy ORM  
- **Layered Architecture**: Clean separation with services, routes, and models
- **Health Monitoring**: Comprehensive health checks and system monitoring
- **RESTful API**: Complete API for external integrations and automation

## 🏗️ Architecture

### Runtime Configuration
- **WSGI Server**: Gunicorn with eventlet workers for WebSocket compatibility
- **Development Mode**: Direct Socket.IO server with hot reload
- **Static Serving**: Flask built-in static file serving (Socket.IO compatible)
- **Database**: SQLAlchemy with connection pooling and health monitoring

### Service Architecture
- **TranscriptionService**: Orchestrates VAD, audio processing, and Whisper integration
- **VADService**: Advanced voice activity detection with noise reduction  
- **WhisperStreamingService**: Real-time OpenAI Whisper API integration
- **AudioProcessor**: Signal processing and audio format conversion

## 🚀 Quick Start

### Installation and Setup

```bash
# Install dependencies  
make install

# Set up environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Initialize database
make db-init
```

### Running the Application

**Development Server:**
```bash
make dev
# Or: python main.py
# Runs on http://localhost:8000
```

**Production Server:**
```bash  
make run
# Or: gunicorn -k eventlet -w 1 main:app --bind 0.0.0.0:8000
```

### Verification Steps

1. **Health Check:**
   ```bash
   curl -s http://localhost:8000/health
   # Expected: {"status":"ok","database":"connected",...}
   ```

2. **Live Interface:**
   - Open `http://localhost:8000/live`
   - Check browser console for "Socket connected" message
   - Should see "Connection state: connected" indicator

3. **Run Tests:**
   ```bash
   make test
   # Includes health checks and WebSocket smoke tests
   ```

## 🧪 Testing

Mina follows comprehensive testing standards with 80% minimum coverage requirement.

### Quick Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test types
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/ -m e2e    # E2E tests
pytest tests/accessibility/ -m e2e  # Accessibility tests
```

### Test Types

- **Unit Tests**: Individual function and class testing
- **Integration Tests**: Service layer and database testing  
- **E2E Tests**: Full user workflow testing with Playwright
- **Accessibility Tests**: WCAG 2.1 AA compliance with axe-core

### Documentation

- 📚 [Testing Guide](docs/testing-guide.md) - Comprehensive testing documentation
- ⚡ [Testing Quick Start](docs/testing-quickstart.md) - Quick reference guide
- ✅ [PR Checklist](docs/pull-request-checklist.md) - Pre-submission checklist (use before submitting PRs)

### CI/CD

All tests run automatically in GitHub Actions:
- ✅ Unit & Integration tests
- ✅ E2E tests (Chromium, Firefox, WebKit)
- ✅ Accessibility compliance
- ✅ Code quality (Ruff, Black)
- ✅ Security scanning (Bandit)

## 🗄️ Database Migrations

Mina uses Flask-Migrate (Alembic) for safe database schema management.

### Quick Commands

```bash
# Create new migration
python manage_migrations.py migrate "Description of changes"

# Apply migrations
python manage_migrations.py upgrade

# Rollback last migration
python manage_migrations.py downgrade
```

### Workflow

1. **Modify models** in `models.py`
2. **Generate migration**: `python manage_migrations.py migrate "Add field"`
3. **Review migration** in `migrations/versions/`
4. **Apply**: `python manage_migrations.py upgrade`
5. **Test** your changes

### Documentation

- 📖 [Database Migrations Guide](docs/database-migrations.md) - Complete migration documentation

### Best Practices

- ✅ Always review auto-generated migrations
- ✅ Test migrations locally before deploying
- ✅ Use descriptive migration messages
- ✅ One logical change per migration
- ✅ Never edit applied migrations

