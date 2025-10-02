# Developer Onboarding Guide

Welcome to the Mina development team! This guide will help you get up to speed quickly.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (or use Replit's managed database)
- Redis (optional, for horizontal scaling)

### Local Setup

1. **Clone and Install**
```bash
# Dependencies are auto-installed on Replit
# For local: pip install -r requirements.txt
```

2. **Environment Variables**
```bash
# Required
DATABASE_URL=postgresql://...
SESSION_SECRET=your-secret-key

# Optional
REDIS_URL=redis://...
SENTRY_DSN=https://...
OPENAI_API_KEY=sk-...
```

3. **Database Setup**
```bash
# Run migrations
flask db upgrade

# Seed test data (development only)
python scripts/seed_dev_data.py
```

4. **Start Development Server**
```bash
# Gunicorn with auto-reload
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

## Project Structure

```
mina/
├── app.py                 # Flask app factory
├── main.py               # Entry point
├── models.py             # SQLAlchemy models
├── routes/               # Route blueprints
│   ├── auth.py
│   ├── dashboard.py
│   ├── meeting.py
│   └── session.py
├── services/             # Business logic
│   ├── transcription_service.py
│   ├── vad_service.py
│   ├── whisper_streaming_service.py
│   └── performance_monitoring.py
├── middleware/           # Flask middleware
├── templates/            # Jinja2 templates
├── static/              # CSS, JS, images
├── tests/               # Test suite
├── docs/                # Documentation
└── migrations/          # Alembic migrations
```

## Architecture Overview

### Core Components

1. **Web Framework**: Flask with Socket.IO for real-time
2. **Database**: PostgreSQL with SQLAlchemy ORM
3. **Real-time**: Socket.IO with Redis adapter
4. **Transcription**: OpenAI Whisper API
5. **Authentication**: JWT + bcrypt + Flask-Login
6. **Monitoring**: Sentry + custom performance tracking

### Key Patterns

- **Application Factory**: `app.py` creates Flask app
- **Blueprints**: Routes organized by feature
- **Services**: Business logic separated from routes
- **ORM**: SQLAlchemy with relationship loading
- **Migrations**: Alembic via Flask-Migrate

## Development Workflow

### Making Changes

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature
```

2. **Write Tests First** (TDD encouraged)
```bash
pytest tests/test_your_feature.py
```

3. **Implement Feature**
   - Follow coding standards (see CODING_STANDARDS.md)
   - Add docstrings to all functions
   - Handle errors gracefully

4. **Run Test Suite**
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

5. **Check Code Quality**
```bash
# Security scan
bandit -r . -f json -o reports/bandit.json

# Secret detection
detect-secrets scan --baseline .secrets.baseline
```

### Database Migrations

```bash
# Create migration after model changes
flask db migrate -m "Add user preferences table"

# Review generated migration file
# Edit migrations/versions/xxx_add_user_preferences.py if needed

# Apply migration
flask db upgrade

# Rollback if needed
flask db downgrade
```

### Testing Socket.IO

```bash
# Start server
gunicorn --bind 0.0.0.0:5000 main:app

# Run Socket.IO tests
pytest tests/integration/test_socketio_connection.py -v
```

## Common Tasks

### Adding a New Model

1. Define in `models.py`:
```python
class NewModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

2. Create migration:
```bash
flask db migrate -m "Add NewModel"
flask db upgrade
```

3. Add indexes if needed:
```python
__table_args__ = (
    db.Index('ix_newmodel_name', 'name'),
)
```

### Adding a New Route

1. Create blueprint in `routes/`:
```python
from flask import Blueprint

new_bp = Blueprint('new', __name__, url_prefix='/new')

@new_bp.route('/')
def index():
    return render_template('new/index.html')
```

2. Register in `app.py`:
```python
from routes.new import new_bp
app.register_blueprint(new_bp)
```

### Adding a New Service

1. Create in `services/`:
```python
class NewService:
    def __init__(self):
        pass
    
    def do_something(self):
        pass

new_service = NewService()
```

2. Use in routes:
```python
from services.new_service import new_service

@bp.route('/action')
def action():
    result = new_service.do_something()
    return jsonify(result)
```

## Debugging

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug info")
logger.info("Info message")
logger.warning("Warning")
logger.error("Error occurred", exc_info=True)
```

### Database Queries
```python
# Enable SQL query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Socket.IO Events
```python
# Client-side debugging
socket.on('connect', () => console.log('Connected'));
socket.on('error', (err) => console.error('Error:', err));
```

## Production Considerations

### Performance
- Use `joinedload()` to prevent N+1 queries
- Add indexes for filtered/sorted columns
- Monitor slow queries (>500ms)
- Use Redis for session state in multi-worker deployments

### Security
- Never commit secrets (use environment variables)
- Validate all user input
- Use parameterized queries (SQLAlchemy handles this)
- Enable CSRF protection
- Set security headers

### Monitoring
- Check Sentry for errors
- Review performance metrics at `/metrics`
- Monitor health at `/health/detailed`

## Resources

- [Architecture Decision Records](docs/adr/)
- [API Documentation](http://localhost:5000/api/docs)
- [Database Schema](docs/api/DATABASE_SCHEMA.md)
- [Testing Standards](docs/testing/TESTING_STANDARDS.md)
- [Security Guidelines](docs/security/)
- [Deployment Guide](docs/operations/DEPLOYMENT_CHECKLIST.md)

## Getting Help

1. Check documentation in `docs/`
2. Review existing code for patterns
3. Ask team members
4. Check troubleshooting guide
5. Review ADRs for architectural decisions

## Next Steps

1. Read through the codebase
2. Run the test suite
3. Try making a small change
4. Review a pull request
5. Pick up a starter issue

Welcome aboard! 🚀
