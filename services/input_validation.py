"""
Input Validation and Sanitization Service

Centralized input validation to prevent injection attacks, XSS, and other
security vulnerabilities. All user input should pass through these validators
before processing.

Phase: PG-1.3 - API Security
"""

import re
import os
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from flask import request, abort, jsonify
import bleach

class InputValidator:
    """Centralized input validation and sanitization."""
    
    # Regex patterns for common validations
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    USERNAME_PATTERN = r'^[a-zA-Z0-9_]{3,32}$'
    UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    ALPHANUMERIC_PATTERN = r'^[a-zA-Z0-9]+$'
    
    # Dangerous patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b|\bALTER\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b\s+\d+\s*=\s*\d+|\bAND\b\s+\d+\s*=\s*\d+)",
        r"(\bUNION\b.*\bSELECT\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e/",
        r"%2e%2e\\",
    ]
    
    @classmethod
    def sanitize_html(cls, text: str, allowed_tags: List[str] = None) -> str:
        """
        Remove dangerous HTML/JS from text.
        
        Args:
            text: Input text
            allowed_tags: List of allowed HTML tags (default: none)
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        allowed_tags = allowed_tags or []
        return bleach.clean(
            text,
            tags=allowed_tags,
            attributes={},
            strip=True
        )
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email or len(email) > 320:  # RFC 5321
            return False
        return re.match(cls.EMAIL_PATTERN, email.lower()) is not None
    
    @classmethod
    def validate_username(cls, username: str) -> bool:
        """
        Validate username format (alphanumeric, 3-32 chars).
        
        Args:
            username: Username to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not username:
            return False
        return re.match(cls.USERNAME_PATTERN, username) is not None
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> bool:
        """
        Validate UUID format.
        
        Args:
            uuid_str: UUID string to validate
            
        Returns:
            True if valid UUID, False otherwise
        """
        if not uuid_str:
            return False
        return re.match(cls.UUID_PATTERN, uuid_str.lower()) is not None
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and injection.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        if not filename:
            return "unnamed_file"
        
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename or "unnamed_file"
    
    @classmethod
    def detect_sql_injection(cls, text: str) -> bool:
        """
        Detect potential SQL injection patterns.
        
        Args:
            text: Input text to check
            
        Returns:
            True if suspicious patterns detected, False otherwise
        """
        if not text:
            return False
        
        text_upper = text.upper()
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def detect_xss(cls, text: str) -> bool:
        """
        Detect potential XSS patterns.
        
        Args:
            text: Input text to check
            
        Returns:
            True if suspicious patterns detected, False otherwise
        """
        if not text:
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def detect_path_traversal(cls, text: str) -> bool:
        """
        Detect potential path traversal attacks.
        
        Args:
            text: Input text to check
            
        Returns:
            True if suspicious patterns detected, False otherwise
        """
        if not text:
            return False
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    @classmethod
    def validate_string(
        cls,
        value: str,
        min_length: int = 0,
        max_length: int = 10000,
        pattern: Optional[str] = None,
        allow_empty: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Validate string with length and pattern checks.
        
        Args:
            value: String to validate
            min_length: Minimum length
            max_length: Maximum length
            pattern: Regex pattern to match
            allow_empty: Whether to allow empty strings
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value:
            if allow_empty:
                return True, None
            return False, "Value cannot be empty"
        
        if len(value) < min_length:
            return False, f"Value must be at least {min_length} characters"
        
        if len(value) > max_length:
            return False, f"Value must not exceed {max_length} characters"
        
        if pattern and not re.match(pattern, value):
            return False, "Value does not match required format"
        
        # Check for injection attacks
        if cls.detect_sql_injection(value):
            return False, "Value contains suspicious SQL patterns"
        
        if cls.detect_xss(value):
            return False, "Value contains suspicious XSS patterns"
        
        if cls.detect_path_traversal(value):
            return False, "Value contains path traversal patterns"
        
        return True, None
    
    @classmethod
    def validate_integer(
        cls,
        value: Any,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate integer with range checks.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            return False, "Value must be an integer"
        
        if min_value is not None and int_value < min_value:
            return False, f"Value must be at least {min_value}"
        
        if max_value is not None and int_value > max_value:
            return False, f"Value must not exceed {max_value}"
        
        return True, None
    
    @classmethod
    def validate_json_keys(cls, data: Dict, required_keys: List[str], optional_keys: List[str] = None) -> tuple[bool, Optional[str]]:
        """
        Validate JSON object has required keys and no unexpected keys.
        
        Args:
            data: JSON object to validate
            required_keys: List of required keys
            optional_keys: List of optional keys
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "Data must be a JSON object"
        
        # Check required keys
        for key in required_keys:
            if key not in data:
                return False, f"Missing required field: {key}"
        
        # Check for unexpected keys
        allowed_keys = set(required_keys) | set(optional_keys or [])
        unexpected_keys = set(data.keys()) - allowed_keys
        
        if unexpected_keys:
            return False, f"Unexpected fields: {', '.join(unexpected_keys)}"
        
        return True, None

def validate_request_json(
    required_fields: List[str] = None,
    optional_fields: List[str] = None,
    validators: Dict[str, callable] = None
):
    """
    Decorator to validate JSON request body.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        validators: Dict of {field_name: validator_function}
    
    Usage:
        @app.route('/api/users', methods=['POST'])
        @validate_request_json(
            required_fields=['email', 'password'],
            optional_fields=['name'],
            validators={
                'email': InputValidator.validate_email,
                'password': lambda p: len(p) >= 8
            }
        )
        def create_user():
            data = request.get_json()
            # ... data is validated
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'invalid_content_type',
                    'message': 'Content-Type must be application/json'
                }), 400
            
            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({
                    'error': 'invalid_json',
                    'message': 'Request body is not valid JSON'
                }), 400
            
            if not isinstance(data, dict):
                return jsonify({
                    'error': 'invalid_format',
                    'message': 'Request body must be a JSON object'
                }), 400
            
            # Validate keys
            is_valid, error = InputValidator.validate_json_keys(
                data,
                required_fields or [],
                optional_fields or []
            )
            
            if not is_valid:
                return jsonify({
                    'error': 'validation_error',
                    'message': error
                }), 400
            
            # Run field validators
            if validators:
                for field, validator in validators.items():
                    if field in data:
                        if not validator(data[field]):
                            return jsonify({
                                'error': 'validation_error',
                                'message': f'Invalid value for field: {field}'
                            }), 400
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorator

def sanitize_input(fields: List[str] = None):
    """
    Decorator to sanitize specific fields in request JSON.
    
    Args:
        fields: List of field names to sanitize (default: all string fields)
    
    Usage:
        @app.route('/api/comments', methods=['POST'])
        @sanitize_input(fields=['text', 'author'])
        def create_comment():
            data = request.get_json()
            # data['text'] and data['author'] are sanitized
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.is_json:
                data = request.get_json()
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        # Sanitize specified fields or all string fields
                        if (fields is None or key in fields) and isinstance(value, str):
                            data[key] = InputValidator.sanitize_html(value)
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorator
