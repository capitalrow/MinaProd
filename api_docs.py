"""
OpenAPI/Swagger documentation for Mina API endpoints
Production-ready API documentation with comprehensive schemas
"""

from flask import Blueprint, jsonify, render_template_string
import json

api_docs_bp = Blueprint('api_docs', __name__)

# OpenAPI 3.0 specification
OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Mina Real-Time Transcription API",
        "description": "Production-grade real-time transcription service with WebSocket support",
        "version": "1.0.0",
        "contact": {
            "name": "Mina Support",
            "email": "support@mina.ai"
        }
    },
    "servers": [
        {
            "url": "https://api.mina.ai",
            "description": "Production server"
        },
        {
            "url": "http://localhost:5000",
            "description": "Development server"
        }
    ],
    "paths": {
        "/api/health": {
            "get": {
                "summary": "Health Check",
                "description": "Check API health and system status",
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HealthResponse"
                                }
                            }
                        }
                    },
                    "503": {
                        "description": "Service is unhealthy"
                    }
                }
            }
        },
        "/api/ready": {
            "get": {
                "summary": "Readiness Check",
                "description": "Check if service is ready to accept traffic",
                "responses": {
                    "200": {
                        "description": "Service is ready"
                    },
                    "503": {
                        "description": "Service is not ready"
                    }
                }
            }
        },
        "/api/metrics": {
            "get": {
                "summary": "System Metrics",
                "description": "Get system performance and application metrics",
                "responses": {
                    "200": {
                        "description": "Metrics retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/MetricsResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/sessions": {
            "post": {
                "summary": "Create Session",
                "description": "Create a new transcription session",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/CreateSessionRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Session created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SessionResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request"
                    }
                }
            },
            "get": {
                "summary": "List Sessions",
                "description": "Get all transcription sessions",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1}
                    },
                    {
                        "name": "limit",
                        "in": "query", 
                        "schema": {"type": "integer", "default": 20}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Sessions retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SessionListResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/sessions/{sessionId}": {
            "get": {
                "summary": "Get Session",
                "description": "Get a specific transcription session",
                "parameters": [
                    {
                        "name": "sessionId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Session retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SessionResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Session not found"
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["ok", "degraded", "error"]},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "version": {"type": "string"},
                    "database": {"type": "object"},
                    "services": {"type": "object"},
                    "system": {"type": "object"}
                }
            },
            "MetricsResponse": {
                "type": "object",
                "properties": {
                    "system": {
                        "type": "object",
                        "properties": {
                            "cpu_percent": {"type": "number"},
                            "memory_percent": {"type": "number"},
                            "disk_percent": {"type": "number"}
                        }
                    },
                    "application": {
                        "type": "object",
                        "properties": {
                            "active_sessions": {"type": "integer"},
                            "total_sessions": {"type": "integer"},
                            "total_segments": {"type": "integer"}
                        }
                    }
                }
            },
            "CreateSessionRequest": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "language": {"type": "string", "default": "en"},
                    "enable_speaker_detection": {"type": "boolean", "default": True},
                    "enable_sentiment_analysis": {"type": "boolean", "default": False}
                }
            },
            "SessionResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "external_id": {"type": "string"},
                    "title": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"},
                    "locale": {"type": "string"},
                    "segments_count": {"type": "integer"},
                    "average_confidence": {"type": "number"},
                    "total_duration": {"type": "number"}
                }
            },
            "SessionListResponse": {
                "type": "object",
                "properties": {
                    "sessions": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/SessionResponse"}
                    },
                    "pagination": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer"},
                            "limit": {"type": "integer"},
                            "total": {"type": "integer"},
                            "pages": {"type": "integer"}
                        }
                    }
                }
            }
        }
    }
}

@api_docs_bp.route('/api/docs')
def api_documentation():
    """Serve interactive API documentation."""
    swagger_ui_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mina API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin:0; background: #fafafa; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
        <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/api/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            });
        };
        </script>
    </body>
    </html>
    """
    return swagger_ui_html

@api_docs_bp.route('/api/openapi.json')
def openapi_spec():
    """Serve OpenAPI specification."""
    return jsonify(OPENAPI_SPEC)

@api_docs_bp.route('/api/docs/redoc')
def redoc_documentation():
    """Serve ReDoc API documentation."""
    redoc_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mina API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <redoc spec-url='/api/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return redoc_html