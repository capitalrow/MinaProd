# Coding Standards

## Python Code Style

### General Principles
- **PEP 8**: Follow Python's official style guide
- **Readability**: Code is read more than written
- **Simplicity**: Prefer simple over clever
- **Consistency**: Match existing patterns

### Formatting
- **Line Length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Organized in 3 groups (stdlib, third-party, local)
```python
import os
import sys

from flask import Flask, request
from sqlalchemy import desc

from models import User, Meeting
from services.auth import auth_service
```

### Naming Conventions
- **Classes**: PascalCase (`UserService`, `MeetingModel`)
- **Functions/Methods**: snake_case (`get_user`, `create_meeting`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_LANGUAGE`)
- **Private**: Prefix with underscore (`_internal_method`)

### Docstrings
All public functions, classes, and modules must have docstrings:

```python
def create_meeting(title: str, organizer_id: int, workspace_id: int) -> Meeting:
    """
    Create a new meeting.
    
    Args:
        title: Meeting title
        organizer_id: ID of meeting organizer
        workspace_id: ID of workspace
        
    Returns:
        Created Meeting object
        
    Raises:
        ValueError: If title is empty
        IntegrityError: If organizer/workspace doesn't exist
    """
    pass
```

### Type Hints
Use type hints for function signatures:

```python
from typing import List, Optional, Dict, Any

def get_meetings(
    workspace_id: int,
    status: Optional[str] = None,
    limit: int = 20
) -> List[Meeting]:
    pass
```

## Database & ORM

### Model Definitions
- Always define `__tablename__`
- Add indexes for foreign keys and frequent queries
- Use `db.relationship()` for associations
- Add `__repr__` for debugging

```python
class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('ix_task_meeting_status', 'meeting_id', 'status'),
    )
    
    # Relationships
    meeting = db.relationship('Meeting', back_populates='tasks')
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
```

### Queries
- Use SQLAlchemy query API (avoid raw SQL)
- Prevent N+1 with `joinedload()` or `selectinload()`
- Use `filter_by()` for simple equality, `filter()` for complex
- Always paginate list queries

```python
# Good
meetings = db.session.query(Meeting).filter_by(
    workspace_id=workspace_id,
    status='active'
).options(
    joinedload(Meeting.organizer)
).order_by(desc(Meeting.created_at)).limit(20).all()

# Avoid
meetings = db.session.execute(
    "SELECT * FROM meetings WHERE workspace_id=?"
    (workspace_id,)
).fetchall()
```

### Transactions
- Use context managers for transactions
- Rollback on errors
- Commit only after all operations succeed

```python
try:
    meeting = Meeting(title=title, workspace_id=workspace_id)
    db.session.add(meeting)
    db.session.flush()  # Get ID without committing
    
    task = Task(title="Follow-up", meeting_id=meeting.id)
    db.session.add(task)
    
    db.session.commit()
except Exception as e:
    db.session.rollback()
    logger.error(f"Failed to create meeting: {e}")
    raise
```

## Flask Routes

### Organization
- Group related routes in blueprints
- Use URL prefixes
- Apply decorators in order: route, auth, validation

```python
from flask import Blueprint, jsonify
from flask_login import login_required

meeting_bp = Blueprint('meeting', __name__, url_prefix='/api/meetings')

@meeting_bp.route('/', methods=['GET'])
@login_required
def list_meetings():
    pass
```

### Request Handling
- Validate input with `services/input_validation.py`
- Return consistent JSON responses
- Use appropriate HTTP status codes
- Handle errors gracefully

```python
from services.input_validation import validate_email, sanitize_text

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    data = request.get_json()
    
    # Validate
    if not validate_email(data.get('email')):
        return jsonify({'error': 'Invalid email'}), 400
    
    # Sanitize
    username = sanitize_text(data.get('username'))
    
    try:
        user = User(username=username, email=data['email'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'User already exists'}), 409
```

### Error Handling
```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error("Internal error", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500
```

## Security

### Input Validation
```python
from services.input_validation import (
    detect_sql_injection,
    prevent_xss,
    validate_uuid
)

user_input = request.args.get('query')

# Check for SQL injection
if detect_sql_injection(user_input):
    return jsonify({'error': 'Invalid input'}), 400

# Prevent XSS
safe_text = prevent_xss(user_input)
```

### Authentication
```python
from flask_login import current_user, login_required

@app.route('/api/meetings/<int:meeting_id>')
@login_required
def get_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    
    # Check authorization
    if meeting.workspace_id != current_user.workspace_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(meeting.to_dict())
```

### Secrets
- Never hardcode secrets
- Use environment variables
- Never log secrets

```python
# Good
api_key = os.environ.get('OPENAI_API_KEY')

# Bad
api_key = 'sk-1234567890'
```

## Testing

### Test Structure
```python
import pytest
from app import create_app, db
from models import User

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_create_user(app):
    """Test user creation."""
    with app.app_context():
        user = User(username='test', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.username == 'test'
```

### Coverage Requirements
- Minimum 80% code coverage
- 100% for critical paths (auth, payments)
- Test happy path and error cases

## Frontend (JavaScript)

### Style
- **ES6+**: Use modern JavaScript
- **Const/Let**: No `var`
- **Arrow Functions**: For callbacks
- **Template Literals**: For strings

```javascript
// Good
const formatDate = (date) => {
    return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`;
};

// Avoid
var formatDate = function(date) {
    return date.getFullYear() + '-' + (date.getMonth()+1) + '-' + date.getDate();
};
```

### Event Handlers
```javascript
// Bind events with delegation
document.addEventListener('click', (e) => {
    if (e.target.matches('.btn-delete')) {
        handleDelete(e.target.dataset.id);
    }
});
```

## Git Workflow

### Commit Messages
```
feat: Add meeting export functionality
fix: Resolve session timeout issue
docs: Update API documentation
test: Add tests for task creation
refactor: Simplify transcription pipeline
```

### Branch Names
- `feature/meeting-export`
- `fix/session-timeout`
- `docs/api-update`

## Performance

### Database
- Add indexes for filtered/sorted columns
- Use `EXPLAIN ANALYZE` for slow queries
- Batch operations when possible
- Use connection pooling

### Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_workspace_settings(workspace_id: int):
    return db.session.query(Workspace).get(workspace_id).settings
```

### Async Operations
- Use background tasks for slow operations
- Don't block request-response cycle
- Provide progress feedback

## Code Review Checklist

- [ ] Tests pass
- [ ] Code follows style guide
- [ ] No security vulnerabilities
- [ ] No secrets committed
- [ ] Documentation updated
- [ ] Migration created (if DB changes)
- [ ] Performance impact considered
- [ ] Error handling present

## Tools

### Pre-commit Hooks
Configured in `.pre-commit-config.yaml`:
- Black (formatting)
- Flake8 (linting)
- Bandit (security)
- detect-secrets

### IDE Setup
Recommended VS Code extensions:
- Python
- Pylance
- SQLTools
- GitLens
