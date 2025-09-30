# Route Consolidation Plan

## Current State
- **Total route files**: 60
- **Actively registered**: 19
- **Unused files**: 41 (68%)

## Duplicate Routes Found
- 7x "/" (root)
- 5x "/health"  
- 3x "/live"
- 3x "/api/transcribe-audio"

## Actively Used Routes (app.py)
1. pages_bp
2. enhanced_transcription_websocket
3. comprehensive_transcription_api
4. live_socketio
5. unified_api_bp
6. live_transcription_bp
7. auth_bp
8. dashboard_bp
9. api_meetings_bp
10. api_tasks_bp
11. api_analytics_bp
12. api_markers_bp
13. api_generate_insights_bp
14. settings_bp
15. calendar_bp
16. copilot_bp
17. monitoring_bp
18. quick_analytics_bp
19. meetings_api_fix_bp

## Unused Route Categories
### Transcription API Duplicates
- transcription_api.py
- enhanced_transcription_api.py
- streaming_transcription_api.py
- transcription_endpoint_fix.py
- audio_transcription_http.py

### WebSocket Duplicates  
- websocket.py
- transcription_websocket.py
- enhanced_websocket_routes.py
- enhanced_websocket_eventlet_routes.py
- enhanced_websocket_handler.py
- enhanced_websocket_simple.py
- eventlet_websocket_server.py
- browser_websocket_routes.py
- library_websocket_routes.py
- native_websocket_routes.py
- sync_websocket_routes.py

### API Duplicates
- api.py
- http.py
- missing_endpoints.py

### Audio Processing
- audio_http.py
- audio_processing_http.py
- audio_processing_fixes.py
- final_upload.py

### Analytics/Metrics
- advanced_analytics.py
- api_performance.py
- api_profiler.py
- internal_metrics.py
- metrics_stream.py

### Other
- error_handlers.py
- export.py
- health.py
- insights.py
- integration_marketplace.py
- nudges.py
- sharing.py
- speech_detection_enhancement.py
- summary.py
- team_collaboration.py
- transcription.py

## Recommended Action
Move to routes/archived/ for review before deletion.
