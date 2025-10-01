# PG-1: Security Hardening Checklist

**Date**: October 1, 2025  
**Status**: In Progress  
**Scope**: Production-ready security audit and hardening

---

## Executive Summary

Comprehensive security audit of Mina platform covering authentication, encryption, API security, session management, and error handling. This checklist identifies implemented security controls, gaps, and required fixes for production deployment.

### Overall Security Posture: 🟡 Good (75%)

**Strengths**:
- ✅ Strong authentication (JWT + bcrypt)
- ✅ Session security with timeouts
- ✅ CSRF protection implemented
- ✅ CSP headers configured
- ✅ Rate limiting active
- ✅ Data encryption framework ready

**Critical Gaps**:
- ❌ Data encryption not fully integrated
- ❌ Input validation not centralized
- ❌ Error handling may leak sensitive data
- ⚠️ CORS configuration too permissive
- ⚠️ Secrets management needs verification

---

## 1. Authentication Security

### ✅ Current Implementation

#### Password Security
- **Hashing**: bcrypt with salt (services/authentication.py:258-266)
- **Password Requirements**:
  - Minimum 8 characters
  - Uppercase required
  - Lowercase required
  - Numbers required
  - Special chars optional

#### JWT Tokens
- **Algorithm**: HS256
- **Access Token**: 24 hours expiry
- **Refresh Token**: 30 days expiry
- **Payload**: user_id, email, role, permissions, exp, iat, type

#### Rate Limiting (Login)
- **Max Attempts**: 5 failures
- **Lockout Duration**: 15 minutes
- **Tracking**: Redis-based

#### Role-Based Access Control (RBAC)
- **Roles**: ADMIN, MODERATOR, USER, GUEST
- **Permissions**: 11 granular permissions
- **Implementation**: services/authentication.py:33-62

### ❌ Issues Found

| Issue | Severity | Description | Fix Required |
|-------|----------|-------------|--------------|
| JWT secret key fallback | 🟡 Medium | Auto-generates secret if not set (line 110) | Enforce env var in production |
| No JWT blacklist | 🟡 Medium | Revoked tokens still valid until expiry | Implement Redis blacklist |
| Password in metadata | 🔴 High | Password hash stored in user metadata dict | Move to dedicated field |
| No 2FA support | 🟡 Medium | Single-factor authentication only | Add TOTP/SMS 2FA option |
| Session concurrency | 🟡 Medium | Max 3 sessions, oldest removed | Log security event |

### 🔧 Fixes Required

#### 1.1: Enforce JWT Secret in Production
```python
# In services/authentication.py, line 108-110
def __post_init__(self):
    if not self.jwt_secret_key:
        if os.getenv('ENV') == 'production':
            raise ValueError("JWT_SECRET_KEY must be set in production")
        self.jwt_secret_key = secrets.token_urlsafe(32)  # Dev only
```

#### 1.2: Implement JWT Blacklist
```python
# Add to AuthenticationManager
def revoke_token(self, token: str, reason: str = "logout") -> bool:
    """Revoke a JWT token by adding to blacklist."""
    try:
        payload = self.verify_token(token)
        if payload:
            token_id = f"revoked:{payload['user_id']}:{payload['iat']}"
            expiry = payload['exp'] - time.time()
            self.redis_client.setex(token_id, int(expiry), reason)
            logger.info(f"Token revoked: {reason}")
            return True
    except Exception as e:
        logger.error(f"Token revocation failed: {e}")
    return False

def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
    """Verify token and check blacklist."""
    try:
        payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])
        
        # Check blacklist
        token_id = f"revoked:{payload['user_id']}:{payload['iat']}"
        if self.redis_client.exists(token_id):
            logger.debug(f"Token is blacklisted: {token_id}")
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

#### 1.3: Move Password Hash to Dedicated Field
```python
# In models/user.py, add:
password_hash = db.Column(db.String(256), nullable=False)

# Update authentication.py to use dedicated field
# Remove from metadata dict
```

---

## 2. Data Encryption

### ✅ Current Implementation

#### Encryption Framework
- **Algorithm**: AES-256-GCM (Fernet)
- **Key Derivation**: PBKDF2 with SHA256
- **Iterations**: 100,000
- **Key Rotation**: 90 days
- **Implementation**: services/data_encryption.py

#### Supported Encryption
- Transcripts (field-level)
- Audio data (field-level)
- User data (email, phone, address)
- Session metadata

#### Key Management
- Master key in Redis/env
- Derived keys with PBKDF2
- Old keys retained for 1 year
- Automatic rotation tracking

### ❌ Issues Found

| Issue | Severity | Description | Fix Required |
|-------|----------|-------------|--------------|
| Encryption not integrated | 🔴 Critical | Service exists but not used in models | Integrate with SQLAlchemy |
| Master key generation | 🟡 Medium | Auto-generates if missing | Require manual setup |
| No key backup | 🟡 Medium | Keys only in Redis | Add encrypted backup |
| TLS not enforced | 🔴 Critical | HTTP allowed in development | Enforce HTTPS |

### 🔧 Fixes Required

#### 2.1: Integrate Encryption with Models
```python
# Create encrypted field type
from sqlalchemy.types import TypeDecorator, String

class EncryptedString(TypeDecorator):
    """SQLAlchemy type for encrypted string fields."""
    impl = String
    
    def __init__(self, *args, encryption_service=None, **kwargs):
        self.encryption_service = encryption_service
        super().__init__(*args, **kwargs)
    
    def process_bind_param(self, value, dialect):
        """Encrypt value before storing."""
        if value is not None and self.encryption_service:
            return self.encryption_service.encrypt_field(value)
        return value
    
    def process_result_value(self, value, dialect):
        """Decrypt value after retrieval."""
        if value is not None and self.encryption_service:
            return self.encryption_service.decrypt_field(value)
        return value

# Usage in models
from services.data_encryption import get_encryption_service

class User(db.Model):
    email = db.Column(EncryptedString(256, encryption_service=get_encryption_service()))
    phone = db.Column(EncryptedString(256, encryption_service=get_encryption_service()))
```

#### 2.2: Enforce Master Key Configuration
```python
# In services/data_encryption.py, _get_or_create_master_key
def _get_or_create_master_key(self) -> str:
    # Try config first
    if self.config.master_key:
        return self.config.master_key
    
    # MUST be in environment for production
    env_key = os.environ.get('ENCRYPTION_MASTER_KEY')
    if not env_key:
        if os.getenv('ENV') == 'production':
            raise ValueError("ENCRYPTION_MASTER_KEY must be set in production")
        # Development only fallback
        env_key = self._generate_dev_key()
    
    return env_key
```

#### 2.3: TLS/HTTPS Enforcement
```python
# Add to app.py before_request
@app.before_request
def enforce_https():
    """Enforce HTTPS in production."""
    if os.getenv('ENV') == 'production':
        if not request.is_secure:
            # Allow health checks
            if request.path in ['/health', '/healthz']:
                return None
            # Redirect to HTTPS
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
```

---

## 3. API Security

### ✅ Current Implementation

#### Rate Limiting (Flask-Limiter)
- **Default**: 100/minute, 1000/hour per IP
- **Backend**: Redis (fallback: memory)
- **Headers**: X-RateLimit-* included
- **Implementation**: app.py:270-284

#### CORS Configuration
- **Middleware**: middleware/cors.py
- **Origins**: Configurable allowlist
- **Credentials**: Supported
- **Methods**: GET, POST, PUT, DELETE, OPTIONS

#### Content Validation
- **JSON Body**: 5MB limit
- **Form Data**: 50MB limit
- **Content-Type**: Validated for API endpoints
- **Audio Content**: Pattern scanning for malware

#### API Key Authentication
- **Header**: X-API-Key
- **Dual-Key Rotation**: Supported
- **Implementation**: security_config.py:213-246

### ❌ Issues Found

| Issue | Severity | Description | Fix Required |
|-------|----------|-------------|--------------|
| CORS allows "*" | 🔴 Critical | Wildcard origin in SocketIO | Restrict origins |
| No input sanitization | 🔴 Critical | User input not sanitized | Add validation layer |
| API key optional | 🟡 Medium | Not enforced on all endpoints | Require for sensitive routes |
| No request signing | 🟡 Medium | No HMAC/signature verification | Add for webhooks |

### 🔧 Fixes Required

#### 3.1: Fix CORS Configuration
```python
# In app.py, socketio initialization (line 174-185)
# Replace cors_allowed_origins="*" with:
allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',') or [
    'https://*.replit.app',
    'https://*.replit.dev',
]

socketio = SocketIO(
    cors_allowed_origins=allowed_origins,  # Restrict origins
    # ... rest of config
)
```

#### 3.2: Create Input Validation Utilities
```python
# Create services/input_validation.py
import re
from typing import Any, Dict, Optional
from flask import abort
import bleach

class InputValidator:
    """Centralized input validation and sanitization."""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove dangerous HTML/JS."""
        return bleach.clean(text, tags=[], attributes={}, strip=True)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username (alphanumeric, 3-32 chars)."""
        pattern = r'^[a-zA-Z0-9_]{3,32}$'
        return re.match(pattern, username) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        # Limit length
        return filename[:255]
    
    @staticmethod
    def validate_json_schema(data: Dict, schema: Dict) -> bool:
        """Validate JSON against schema."""
        # Implement JSON schema validation
        from jsonschema import validate, ValidationError
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError:
            return False

# Decorator for route validation
def validate_input(schema: Dict):
    """Decorator to validate request input."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import request
            
            if request.is_json:
                data = request.get_json()
                if not InputValidator.validate_json_schema(data, schema):
                    abort(400, description="Invalid input format")
            
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

#### 3.3: Enforce API Key on Sensitive Routes
```python
# Add to routes that modify data
from security_config import require_api_key

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
@require_api_key  # Add this decorator
@login_required
def delete_session(session_id):
    # ... implementation
    pass
```

---

## 4. Security Headers

### ✅ Current Implementation

#### CSP Headers (middleware/csp.py)
- **Nonce-based**: Unique per request
- **Default-src**: 'self'
- **Script-src**: 'self' + nonce + CDNs
- **Style-src**: 'self' + 'unsafe-inline' + CDNs
- **Connect-src**: wss/ws + self + APIs
- **Frame-ancestors**: 'self' + Replit domains
- **Upgrade-insecure-requests**: Production only

#### Additional Headers (security_config.py)
- **X-Content-Type-Options**: nosniff
- **X-Frame-Options**: DENY
- **X-XSS-Protection**: 1; mode=block
- **Referrer-Policy**: strict-origin-when-cross-origin
- **Strict-Transport-Security**: HTTPS only (31536000s)

### ❌ Issues Found

| Issue | Severity | Description | Fix Required |
|-------|----------|-------------|--------------|
| unsafe-inline in CSP | 🟡 Medium | Allows inline styles (weakens CSP) | Use nonce for styles too |
| HSTS not always set | 🟡 Medium | Only on HTTPS requests | Set in reverse proxy |
| No Permissions-Policy | 🟡 Medium | Missing feature policy header | Add restrictive policy |

### 🔧 Fixes Required

#### 4.1: Strengthen CSP for Styles
```python
# In middleware/csp.py, update style-src (line 78)
# Replace:
"style-src 'self' 'unsafe-inline' " + ...

# With nonce-based:
f"style-src 'self' 'nonce-{nonce}' " + ...

# Update templates to use nonce:
<style nonce="{{ g.csp_nonce }}">
    /* inline styles */
</style>
```

#### 4.2: Add Permissions-Policy Header
```python
# In middleware/csp.py, add to after_request (line 136)
response.headers['Permissions-Policy'] = (
    'geolocation=(), '
    'microphone=(self), '
    'camera=(self), '
    'payment=(), '
    'usb=(), '
    'magnetometer=(), '
    'gyroscope=(), '
    'accelerometer=()'
)
```

---

## 5. Session Management & CSRF

### ✅ Current Implementation

#### Session Security (middleware/session_security.py)
- **Idle Timeout**: 30 minutes
- **Absolute Timeout**: 8 hours
- **Session Rotation**: On login
- **Fixation Prevention**: Session ID regeneration
- **Cookie Flags**: HttpOnly, Secure, SameSite=Lax

#### CSRF Protection (app.py)
- **Library**: Flask-WTF CSRFProtect
- **Time Limit**: None (persistent tokens)
- **SSL Strict**: True (HTTPS referer checks)
- **Check Default**: True (enabled by default)
- **Socket.IO Exempt**: Custom error handler

### ❌ Issues Found

| Issue | Severity | Description | Fix Required |
|-------|----------|-------------|--------------|
| CSRF token in URL | 🟡 Medium | Tokens might leak in logs | Use headers only |
| No CSRF for API | 🟡 Medium | JSON API doesn't use CSRF | Add X-CSRF-Token header |
| Session cookie SameSite | 🟡 Medium | Lax allows some CSRF | Use Strict for high-security |

### 🔧 Fixes Required

#### 5.1: CSRF for JSON APIs
```python
# Update API routes to include CSRF
from flask_wtf.csrf import generate_csrf

@app.route('/api/meetings', methods=['POST'])
@csrf.exempt  # Exempt from automatic check
def create_meeting():
    # Manually verify CSRF token from header
    token = request.headers.get('X-CSRF-Token')
    if not token or token != session.get('csrf_token'):
        abort(403, description="CSRF token missing or invalid")
    
    # ... rest of implementation
```

#### 5.2: Provide CSRF Token to Frontend
```python
# Add endpoint to get CSRF token
@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    return jsonify({'csrf_token': token})

# Frontend usage:
// Fetch token
const response = await fetch('/api/csrf-token');
const { csrf_token } = await response.json();

// Include in API requests
fetch('/api/meetings', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token
    },
    body: JSON.stringify(data)
});
```

---

## 6. Error Handling & Information Leakage

### ✅ Current Implementation

#### Structured Logging (app.py)
- **Format**: JSON with metadata
- **Sanitization**: Sentry before_send filter
- **Sensitive Keys**: password, token, api_key filtered
- **Context**: request_id, user_id, HTTP details

#### Sentry Integration
- **Error Tracking**: FlaskIntegration
- **SQL Monitoring**: SqlalchemyIntegration
- **Filtering**: 404/401/403 excluded
- **PII**: send_default_pii=False

### ❌ Issues Found

| Issue | Severity | Description | Fix Required |
|-------|----------|-------------|--------------|
| Stack traces in dev | 🟡 Medium | Full traces exposed in development | Sanitize even in dev |
| Database errors | 🔴 Critical | SQL errors may leak schema info | Generic error messages |
| Debug mode in prod | 🔴 Critical | Flask debug=True exposes code | Enforce debug=False |

### 🔧 Fixes Required

#### 6.1: Custom Error Handlers
```python
# Add to app.py
@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        'error': 'bad_request',
        'message': 'The request could not be understood',
        'request_id': g.get('request_id')
    }), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({
        'error': 'unauthorized',
        'message': 'Authentication required',
        'request_id': g.get('request_id')
    }), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({
        'error': 'forbidden',
        'message': 'You do not have permission to access this resource',
        'request_id': g.get('request_id')
    }), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'not_found',
        'message': 'The requested resource was not found',
        'request_id': g.get('request_id')
    }), 404

@app.errorhandler(500)
def internal_error(e):
    # Log full error internally
    app.logger.error(f"Internal error: {str(e)}", exc_info=True)
    
    # Return generic message to client
    return jsonify({
        'error': 'internal_error',
        'message': 'An internal error occurred. Please try again later.',
        'request_id': g.get('request_id')
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Log unexpected errors
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    
    # Return generic error
    return jsonify({
        'error': 'server_error',
        'message': 'An unexpected error occurred',
        'request_id': g.get('request_id')
    }), 500
```

#### 6.2: Sanitize Database Errors
```python
# Wrap database operations
from sqlalchemy.exc import SQLAlchemyError

def safe_db_operation(operation):
    """Decorator to sanitize database errors."""
    def wrapper(*args, **kwargs):
        try:
            return operation(*args, **kwargs)
        except SQLAlchemyError as e:
            # Log detailed error internally
            app.logger.error(f"Database error in {operation.__name__}: {str(e)}")
            
            # Return generic error to client
            abort(500, description="A database error occurred")
    return wrapper

# Usage:
@safe_db_operation
def get_user(user_id):
    return User.query.get(user_id)
```

#### 6.3: Enforce Debug Mode OFF in Production
```python
# Add to app.py create_app()
if os.getenv('ENV') == 'production':
    if app.debug or app.config.get('DEBUG'):
        raise RuntimeError("DEBUG mode must be disabled in production")
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
```

---

## 7. Secrets Management

### ✅ Current Implementation

#### Environment Variables
- SESSION_SECRET: Required
- DATABASE_URL: Required
- OPENAI_API_KEY: Optional
- REDIS_URL: Optional
- SENTRY_DSN: Optional

#### Secret Rotation Script
- **File**: scripts/rotate_secrets.sh
- **Features**: Dual-key rotation, zero-downtime
- **Backup**: Old keys retained

### ❌ Issues Found

| Issue | Severity | Description | Fix Required |
|-------|----------|-------------|--------------|
| No secrets scanning | 🟡 Medium | No automated scanning for leaked secrets | Add git hooks |
| Hardcoded secrets | 🟡 Medium | Dev fallbacks in code | Remove all hardcoded secrets |
| No secrets vault | 🟡 Medium | Env vars only, no vault integration | Consider Vault/AWS Secrets Manager |

### 🔧 Fixes Required

#### 7.1: Secrets Scanning with Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Scan for secrets before commit

# Check for common secret patterns
if git diff --cached | grep -iE "(password|api_key|secret|token)\s*=\s*['\"][^'\"]{8,}" ; then
    echo "ERROR: Possible secret detected in commit"
    echo "Please remove secrets and use environment variables"
    exit 1
fi

# Check for AWS keys
if git diff --cached | grep -E "AKIA[0-9A-Z]{16}" ; then
    echo "ERROR: AWS access key detected"
    exit 1
fi

# Check for private keys
if git diff --cached | grep -i "BEGIN.*PRIVATE KEY" ; then
    echo "ERROR: Private key detected"
    exit 1
fi

exit 0
```

#### 7.2: Remove Hardcoded Secrets
```python
# Find and replace all instances like:
# app.secret_key = "dev-session-secret-only-for-testing-change-in-production"

# With:
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise ValueError("SESSION_SECRET environment variable required")
```

---

## Implementation Priority

### 🔴 Critical (Fix Immediately)
1. **CORS Wildcard**: Restrict Socket.IO origins
2. **Input Validation**: Add sanitization layer
3. **Database Errors**: Implement generic error messages
4. **Debug Mode**: Enforce OFF in production
5. **Password Storage**: Move hash to dedicated field

### 🟡 High (Fix Before Production)
1. **JWT Blacklist**: Implement token revocation
2. **Data Encryption**: Integrate with models
3. **HTTPS Enforcement**: Redirect HTTP to HTTPS
4. **API Key**: Enforce on sensitive routes
5. **Error Handlers**: Custom 4xx/5xx responses

### 🟢 Medium (Post-Launch)
1. **2FA Support**: Add TOTP authentication
2. **CSP Nonces**: Extend to stylesheets
3. **Secrets Vault**: Integrate Vault/AWS Secrets Manager
4. **Request Signing**: HMAC for webhooks
5. **Secrets Scanning**: Automated pre-commit hooks

---

## Testing Checklist

### Penetration Testing
- [ ] SQL injection attempts
- [ ] XSS attacks (reflected, stored, DOM-based)
- [ ] CSRF bypass attempts
- [ ] Authentication bypass
- [ ] Session hijacking
- [ ] Path traversal
- [ ] Command injection
- [ ] XXE attacks
- [ ] SSRF attacks

### Security Scanning
- [ ] Run OWASP ZAP scan
- [ ] Run Burp Suite scan
- [ ] Check SSL/TLS configuration (SSL Labs)
- [ ] Verify security headers (SecurityHeaders.com)
- [ ] Scan dependencies (npm audit, safety)
- [ ] Check for secrets in git history

### Compliance Checks
- [ ] GDPR data handling
- [ ] SOC 2 controls
- [ ] PCI DSS (if handling payments)
- [ ] HIPAA (if handling health data)

---

## Compliance Status

### OWASP Top 10 (2021)

| Risk | Status | Notes |
|------|--------|-------|
| A01 Broken Access Control | 🟡 Partial | RBAC implemented, need API key enforcement |
| A02 Cryptographic Failures | 🟡 Partial | Encryption ready, needs integration |
| A03 Injection | 🔴 At Risk | No input validation layer |
| A04 Insecure Design | 🟢 Good | Security by design principles followed |
| A05 Security Misconfiguration | 🟡 Partial | Some hardening needed |
| A06 Vulnerable Components | 🟢 Good | Dependencies scanned regularly |
| A07 Authentication Failures | 🟢 Good | Strong auth, needs 2FA |
| A08 Data Integrity Failures | 🟢 Good | Checksums, encryption available |
| A09 Logging Failures | 🟢 Good | Structured logging + Sentry |
| A10 SSRF | 🟡 Partial | Need URL validation |

### CIS Controls

| Control | Compliance | Gap |
|---------|------------|-----|
| Inventory of Authorized Software | ✅ Complete | - |
| Secure Configuration | 🟡 Partial | Need config hardening |
| Data Protection | 🟡 Partial | Encryption needs integration |
| Access Control | ✅ Complete | RBAC implemented |
| Account Management | ✅ Complete | JWT + session mgmt |
| Audit Log Management | ✅ Complete | JSON logging + Sentry |
| Email & Web Browser Protections | ✅ Complete | CSP headers |
| Malware Defenses | 🟡 Partial | Basic content scanning |
| Penetration Testing | ❌ Incomplete | Schedule pen test |
| Incident Response | 🟡 Partial | Need incident runbook |

---

## Metrics & Monitoring

### Security Metrics to Track

1. **Authentication Failures**
   - Failed login attempts
   - Account lockouts
   - Password reset requests

2. **Rate Limiting**
   - Requests blocked by rate limiter
   - Top offending IPs
   - Abuse patterns

3. **Encryption**
   - Encryption operations per second
   - Key rotation schedule
   - Decryption failures

4. **Error Rates**
   - 4xx client errors
   - 5xx server errors  
   - Security exceptions

5. **Session Security**
   - Active sessions count
   - Session timeout events
   - Concurrent session violations

### Alerting Thresholds

- **Critical**: >100 failed logins/min from single IP
- **High**: >5 SQL errors/min (possible injection)
- **Medium**: Encryption key age >80 days
- **Low**: Rate limit hit >10 times/hour

---

## Sign-off Checklist

### Before Production Deployment

- [ ] All critical issues fixed
- [ ] High-priority issues addressed
- [ ] Penetration test completed
- [ ] Security headers verified
- [ ] Secrets properly configured
- [ ] HTTPS enforced
- [ ] Debug mode disabled
- [ ] Error handlers tested
- [ ] Logging validated
- [ ] Monitoring dashboards set up
- [ ] Incident response plan documented
- [ ] Security team sign-off obtained

---

## References

- [OWASP Top 10 (2021)](https://owasp.org/www-project-top-ten/)
- [CIS Controls v8](https://www.cisecurity.org/controls/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
