#!/usr/bin/env python3
"""
UI/UX Fix Implementations for Mina Live Transcription
Specific code changes to address critical UI issues identified in analysis
"""

class UIFixImplementations:
    """Contains specific code implementations for UI/UX critical fixes"""
    
    def __init__(self):
        self.fixes = {
            'fix_pack_1': 'Backend Pipeline Stability',
            'fix_pack_2': 'Frontend UX Enhancement', 
            'fix_pack_3': 'QA & Testing Framework',
            'fix_pack_4': 'Accessibility & Mobile UX'
        }
    
    def get_backend_pipeline_fixes(self):
        """P0 Backend fixes for session stats synchronization and error recovery"""
        return {
            'title': 'Fix Pack 1: Backend Pipeline Stability',
            'priority': 'P0',
            'timeline': '1-2 weeks',
            'fixes': [
                {
                    'issue': 'Session stats showing 0 values despite active transcription',
                    'root_cause': 'UI session metrics not synchronized with backend processing',
                    'files_to_modify': [
                        'routes/websocket.py',
                        'services/transcription_service.py',
                        'static/js/recording_wiring.js'
                    ],
                    'implementation': '''
# 1. In routes/websocket.py - Add session metrics broadcast
@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    # ... existing code ...
    
    # Add session metrics update after processing
    session_metrics = {
        'session_id': session_id,
        'segments_count': len(session.segments),
        'avg_confidence': session.average_confidence,
        'speaking_time': session.speaking_time_seconds,
        'quality': session.quality_status,
        'last_update': datetime.now().isoformat(),
        'processing_status': 'active'
    }
    emit('session_metrics_update', session_metrics, room=session_id)

# 2. In static/js/recording_wiring.js - Add metrics handler
socket.on('session_metrics_update', (metrics) => {
    updateSessionStats(metrics);
});

function updateSessionStats(metrics) {
    document.getElementById('segmentCount').textContent = metrics.segments_count;
    document.getElementById('avgConfidence').textContent = (metrics.avg_confidence * 100).toFixed(1) + '%';
    document.getElementById('speakingTime').textContent = formatTime(metrics.speaking_time);
    document.getElementById('qualityStatus').textContent = metrics.quality;
    document.getElementById('lastUpdate').textContent = formatTimestamp(metrics.last_update);
}
                    '''
                },
                {
                    'issue': 'Recording failed but transcript still appears - inconsistent state',
                    'root_cause': 'Error state not properly propagated to session management',
                    'files_to_modify': [
                        'services/transcription_service.py',
                        'routes/websocket.py'
                    ],
                    'implementation': '''
# In services/transcription_service.py - Add session state validation
async def process_audio_chunk(self, session_id: str, audio_data: bytes):
    try:
        session = self.get_session(session_id)
        if session.state == SessionState.ERROR:
            raise Exception("Session in error state - cannot process audio")
        
        if session.state != SessionState.RECORDING:
            self.set_session_state(session_id, SessionState.ERROR)
            raise Exception("Invalid session state for audio processing")
        
        # ... existing processing ...
        
    except Exception as e:
        self.set_session_state(session_id, SessionState.ERROR)
        self.emit_error(session_id, f"Audio processing failed: {str(e)}")
        raise

def set_session_state(self, session_id: str, state: SessionState):
    session = self.get_session(session_id)
    session.state = state
    # Emit state change to frontend
    from routes.websocket import socketio
    socketio.emit('session_state_change', {
        'session_id': session_id,
        'state': state.value,
        'timestamp': datetime.now().isoformat()
    }, room=session_id)
                    '''
                },
                {
                    'issue': 'No final transcript generated on session end',
                    'root_cause': 'Missing finalization logic in session termination',
                    'files_to_modify': [
                        'services/transcription_service.py'
                    ],
                    'implementation': '''
# Add session finalization method
async def finalize_session(self, session_id: str):
    """Generate final transcript and session summary"""
    try:
        session = self.get_session(session_id)
        
        # Compile final transcript from all segments
        final_segments = session.segments.filter_by(is_final=True).all()
        final_text = " ".join([seg.text for seg in final_segments])
        
        # Calculate final metrics
        total_confidence = sum([seg.confidence for seg in final_segments])
        avg_confidence = total_confidence / len(final_segments) if final_segments else 0
        
        # Create session summary
        summary = {
            'session_id': session_id,
            'final_transcript': final_text,
            'total_segments': len(final_segments),
            'average_confidence': avg_confidence,
            'total_duration': session.duration_seconds,
            'word_count': len(final_text.split()),
            'finalized_at': datetime.now().isoformat()
        }
        
        # Emit final transcript
        from routes.websocket import socketio
        socketio.emit('final_session_transcript', summary, room=session_id)
        
        # Update session state
        self.set_session_state(session_id, SessionState.COMPLETED)
        
        return summary
        
    except Exception as e:
        logger.error(f"Session finalization failed for {session_id}: {e}")
        self.set_session_state(session_id, SessionState.ERROR)
        raise
                    '''
                },
                {
                    'issue': 'Latency spikes above 1000ms degrading real-time experience',
                    'root_cause': 'No latency monitoring and adaptive throttling',
                    'files_to_modify': [
                        'services/transcription_service.py'
                    ],
                    'implementation': '''
# Add latency monitoring and adaptive throttling
class LatencyMonitor:
    def __init__(self, target_latency_ms=150):
        self.target_latency = target_latency_ms
        self.recent_latencies = []
        self.max_samples = 10
        
    def record_latency(self, latency_ms):
        self.recent_latencies.append(latency_ms)
        if len(self.recent_latencies) > self.max_samples:
            self.recent_latencies.pop(0)
    
    def get_adaptive_throttle(self):
        if len(self.recent_latencies) < 3:
            return self.target_latency
        
        avg_latency = sum(self.recent_latencies) / len(self.recent_latencies)
        
        if avg_latency > self.target_latency * 2:
            # High latency - reduce processing frequency
            return self.target_latency * 1.5
        elif avg_latency > self.target_latency:
            # Moderate latency - slight increase
            return self.target_latency * 1.2
        else:
            # Good latency - maintain or decrease
            return max(self.target_latency * 0.8, 100)

# Add to TranscriptionService
self.latency_monitor = LatencyMonitor(self.config.latency_target_ms)
                    '''
                }
            ],
            'validation_tests': [
                'test_session_metrics_synchronization.py',
                'test_error_state_recovery.py', 
                'test_final_transcript_generation.py',
                'test_latency_adaptive_throttling.py'
            ]
        }
    
    def get_frontend_ux_fixes(self):
        """P0 Frontend fixes for visual indicators and error states"""
        return {
            'title': 'Fix Pack 2: Frontend UX Enhancement',
            'priority': 'P0', 
            'timeline': '1 week',
            'fixes': [
                {
                    'issue': 'No visual recording indicators beyond text status',
                    'root_cause': 'Missing animated recording states in UI',
                    'files_to_modify': [
                        'templates/live.html',
                        'static/css/main.css',
                        'static/js/recording_wiring.js'
                    ],
                    'implementation': '''
/* Add to static/css/main.css */
.recording-pulse {
    animation: recording-pulse 1.5s ease-in-out infinite;
}

.recording-indicator {
    width: 16px;
    height: 16px;
    background: #dc3545;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
}

@keyframes recording-pulse {
    0%, 100% { 
        opacity: 1;
        transform: scale(1);
    }
    50% { 
        opacity: 0.7;
        transform: scale(1.1);
    }
}

.mic-level-indicator {
    width: 100%;
    height: 8px;
    background: var(--bs-gray-700);
    border-radius: 4px;
    overflow: hidden;
    margin-top: 8px;
}

.mic-level-bar {
    height: 100%;
    background: linear-gradient(90deg, #28a745, #ffc107, #dc3545);
    transition: width 0.1s ease;
}

// Add to static/js/recording_wiring.js
function updateRecordingIndicators(isRecording, inputLevel = 0) {
    const indicator = document.getElementById('recordingIndicator');
    const statusText = document.getElementById('micStatus');
    const levelBar = document.getElementById('micLevelBar');
    
    if (isRecording) {
        if (!indicator.querySelector('.recording-indicator')) {
            const dot = document.createElement('span');
            dot.className = 'recording-indicator recording-pulse';
            indicator.appendChild(dot);
        }
        statusText.textContent = 'Recording';
        statusText.className = 'text-danger fw-bold';
        
        // Update input level
        if (levelBar) {
            levelBar.style.width = `${inputLevel}%`;
        }
    } else {
        const dot = indicator.querySelector('.recording-indicator');
        if (dot) dot.remove();
        statusText.textContent = 'Ready';
        statusText.className = 'text-muted';
        
        if (levelBar) {
            levelBar.style.width = '0%';
        }
    }
}
                    '''
                },
                {
                    'issue': 'Poor error state communication to users',
                    'root_cause': 'Generic error messages without actionable guidance',
                    'files_to_modify': [
                        'static/js/recording_wiring.js',
                        'templates/live.html'
                    ],
                    'implementation': '''
// Enhanced error handling in static/js/recording_wiring.js
function showEnhancedError(errorType, message, details = {}) {
    const errorConfig = {
        'microphone_denied': {
            title: 'Microphone Access Required',
            message: 'Please allow microphone access to use live transcription.',
            actions: [
                'Click the microphone icon in your browser address bar',
                'Select "Allow" for microphone access',
                'Refresh the page and try again'
            ],
            type: 'warning',
            persistent: true
        },
        'websocket_disconnected': {
            title: 'Connection Lost',
            message: 'Lost connection to transcription service.',
            actions: [
                'Check your internet connection',
                'Attempting to reconnect automatically...',
                'If problems persist, refresh the page'
            ],
            type: 'error',
            persistent: false
        },
        'session_failed': {
            title: 'Session Error',
            message: 'Transcription session encountered an error.',
            actions: [
                'Stop current recording',
                'Start a new session',
                'Contact support if error persists'
            ],
            type: 'error',
            persistent: true
        },
        'api_key_missing': {
            title: 'Service Configuration Error',
            message: 'Transcription service is not properly configured.',
            actions: [
                'Contact your administrator',
                'Service configuration required'
            ],
            type: 'error',
            persistent: true
        }
    };
    
    const config = errorConfig[errorType] || {
        title: 'Error',
        message: message,
        actions: ['Please try again'],
        type: 'error',
        persistent: false
    };
    
    showDetailedNotification(config);
}

function showDetailedNotification(config) {
    const notificationArea = document.getElementById('notificationArea');
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${config.type} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');
    
    const actionsHtml = config.actions.map(action => 
        `<li class="small text-muted">${action}</li>`
    ).join('');
    
    notification.innerHTML = `
        <div class="d-flex align-items-start">
            <i class="fas fa-exclamation-triangle me-2 mt-1"></i>
            <div class="flex-grow-1">
                <strong>${config.title}</strong>
                <div class="mt-1">${config.message}</div>
                ${actionsHtml ? `<ul class="mt-2 mb-0">${actionsHtml}</ul>` : ''}
            </div>
            ${!config.persistent ? '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' : ''}
        </div>
    `;
    
    notificationArea.appendChild(notification);
    
    // Auto-remove non-persistent notifications
    if (!config.persistent) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 8000);
    }
    
    // Announce to screen readers
    announceToScreenReader(`${config.title}: ${config.message}`);
}
                    '''
                },
                {
                    'issue': 'Connection state management unclear to users',
                    'root_cause': 'Inconsistent connection status display',
                    'files_to_modify': [
                        'static/js/recording_wiring.js'
                    ],
                    'implementation': '''
// Enhanced connection state management
class ConnectionStateManager {
    constructor() {
        this.states = {
            INITIALIZING: 'initializing',
            CONNECTING: 'connecting', 
            CONNECTED: 'connected',
            READY: 'ready',
            RECORDING: 'recording',
            DISCONNECTED: 'disconnected',
            ERROR: 'error'
        };
        this.currentState = this.states.INITIALIZING;
        this.stateHistory = [];
    }
    
    setState(newState, context = {}) {
        const previousState = this.currentState;
        this.currentState = newState;
        this.stateHistory.push({
            state: newState,
            timestamp: Date.now(),
            context
        });
        
        this.updateUI(newState, previousState, context);
        this.announceStateChange(newState, context);
        
        console.log(`🔄 State: ${previousState} → ${newState}`, context);
    }
    
    updateUI(state, previousState, context) {
        const statusIndicator = document.getElementById('connectionStatus');
        const statusText = document.getElementById('wsStatus');
        
        // Update visual indicator
        statusIndicator.className = 'status-indicator';
        statusText.className = '';
        
        switch(state) {
            case this.states.INITIALIZING:
                statusIndicator.classList.add('status-connecting');
                statusText.textContent = 'Initializing...';
                statusText.classList.add('text-warning');
                break;
                
            case this.states.CONNECTING:
                statusIndicator.classList.add('status-connecting');
                statusText.textContent = 'Connecting...';
                statusText.classList.add('text-warning');
                break;
                
            case this.states.CONNECTED:
                statusIndicator.classList.add('status-connected');
                statusText.textContent = 'Connected';
                statusText.classList.add('text-success');
                break;
                
            case this.states.READY:
                statusIndicator.classList.add('status-connected');
                statusText.textContent = 'Ready to record';
                statusText.classList.add('text-success');
                break;
                
            case this.states.RECORDING:
                statusIndicator.classList.add('status-connected');
                statusText.textContent = 'Recording...';
                statusText.classList.add('text-info');
                break;
                
            case this.states.DISCONNECTED:
                statusIndicator.classList.add('status-disconnected');
                statusText.textContent = `Disconnected${context.reason ? ': ' + context.reason : ''}`;
                statusText.classList.add('text-danger');
                break;
                
            case this.states.ERROR:
                statusIndicator.classList.add('status-disconnected');
                statusText.textContent = `Error${context.error ? ': ' + context.error : ''}`;
                statusText.classList.add('text-danger');
                break;
        }
    }
    
    announceStateChange(state, context) {
        let message = '';
        switch(state) {
            case this.states.CONNECTED:
                message = 'Connected to transcription service';
                break;
            case this.states.READY:
                message = 'Ready to start recording';
                break;
            case this.states.RECORDING:
                message = 'Recording started';
                break;
            case this.states.DISCONNECTED:
                message = 'Disconnected from service';
                break;
            case this.states.ERROR:
                message = 'Connection error occurred';
                break;
        }
        
        if (message) {
            announceToScreenReader(message);
        }
    }
}

const connectionState = new ConnectionStateManager();
                    '''
                }
            ],
            'validation_tests': [
                'test_visual_recording_indicators.py',
                'test_enhanced_error_handling.py',
                'test_connection_state_management.py'
            ]
        }
    
    def get_qa_framework_fixes(self):
        """P1 QA and testing framework improvements"""
        return {
            'title': 'Fix Pack 3: QA & Testing Framework',
            'priority': 'P1',
            'timeline': '2 weeks',
            'fixes': [
                {
                    'issue': 'No WER calculation capability for transcript quality validation',
                    'root_cause': 'Missing reference audio comparison system',
                    'implementation': '''
# Enhanced QA harness implementation - build on tests/qa_harness.py
class ProductionQAIntegration:
    def __init__(self, transcription_service):
        self.service = transcription_service
        self.qa_harness = TranscriptionQAHarness()
        self.reference_db = {}
        
    async def start_qa_session(self, session_id, reference_audio_path=None):
        """Start QA monitoring for a live session"""
        if reference_audio_path:
            # Load reference transcript if available
            reference_text = await self.load_reference_transcript(reference_audio_path)
            self.qa_harness.start_qa_session(session_id, reference_text, reference_audio_path)
        else:
            self.qa_harness.start_qa_session(session_id)
    
    async def validate_transcript_quality(self, session_id, final_transcript):
        """Validate transcript quality against reference"""
        session_data = self.qa_harness.qa_sessions.get(session_id)
        if not session_data:
            return {'error': 'QA session not found'}
        
        quality_report = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'transcript_length': len(final_transcript),
            'word_count': len(final_transcript.split())
        }
        
        # WER calculation if reference available
        if session_data['reference_text']:
            wer_analysis = self.qa_harness.calculate_wer(
                session_data['reference_text'], 
                final_transcript
            )
            quality_report['wer_analysis'] = wer_analysis
        
        # Hallucination detection
        hallucination_analysis = self.qa_harness.detect_hallucinations(
            final_transcript, 
            time.time() - session_data['start_time']
        )
        quality_report['hallucination_analysis'] = hallucination_analysis
        
        # Confidence analysis
        confidence_analysis = self.qa_harness.analyze_confidence_accuracy(session_id)
        quality_report['confidence_analysis'] = confidence_analysis
        
        # Log quality metrics
        logger.info(f"QA Report for {session_id}: {quality_report}")
        
        return quality_report
                    '''
                }
            ]
        }
    
    def get_accessibility_fixes(self):
        """P1 Accessibility and mobile UX improvements"""
        return {
            'title': 'Fix Pack 4: Accessibility & Mobile UX',
            'priority': 'P1',
            'timeline': '1 week', 
            'fixes': [
                {
                    'issue': 'Missing comprehensive ARIA labels and screen reader support',
                    'root_cause': 'Incomplete accessibility implementation',
                    'implementation': '''
// Enhanced accessibility in static/js/recording_wiring.js
function enhanceAccessibility() {
    // Add ARIA live regions for dynamic content
    const transcriptionContainer = document.getElementById('transcriptionContainer');
    transcriptionContainer.setAttribute('aria-live', 'polite');
    transcriptionContainer.setAttribute('aria-label', 'Live transcription results');
    
    // Add role and state information to controls
    const startBtn = document.getElementById('startRecordingBtn');
    const stopBtn = document.getElementById('stopRecordingBtn');
    
    startBtn.setAttribute('aria-describedby', 'recording-help');
    stopBtn.setAttribute('aria-describedby', 'recording-help');
    
    // Create help text
    const helpText = document.createElement('div');
    helpText.id = 'recording-help';
    helpText.className = 'sr-only';
    helpText.textContent = 'Use spacebar to start/stop recording, or click these buttons';
    document.body.appendChild(helpText);
    
    // Add keyboard navigation
    document.addEventListener('keydown', handleA11yKeyboard);
}

function handleA11yKeyboard(event) {
    // Space bar for start/stop
    if (event.code === 'Space' && !event.target.matches('input, textarea, select')) {
        event.preventDefault();
        const startBtn = document.getElementById('startRecordingBtn');
        const stopBtn = document.getElementById('stopRecordingBtn');
        
        if (!startBtn.disabled) {
            startBtn.click();
            announceToScreenReader('Recording started via keyboard');
        } else if (!stopBtn.disabled) {
            stopBtn.click();
            announceToScreenReader('Recording stopped via keyboard');
        }
    }
    
    // Escape to stop recording
    if (event.code === 'Escape' && !document.getElementById('stopRecordingBtn').disabled) {
        document.getElementById('stopRecordingBtn').click();
        announceToScreenReader('Recording cancelled via keyboard');
    }
}

function announceToScreenReader(message) {
    const announcer = document.getElementById('sr-announcements');
    if (announcer) {
        announcer.textContent = message;
        // Clear after announcing
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }
}
                    '''
                }
            ]
        }

if __name__ == "__main__":
    fixes = UIFixImplementations()
    
    print("🔧 MINA UI/UX FIX IMPLEMENTATIONS")
    print("="*50)
    
    for fix_pack in [
        fixes.get_backend_pipeline_fixes(),
        fixes.get_frontend_ux_fixes(), 
        fixes.get_qa_framework_fixes(),
        fixes.get_accessibility_fixes()
    ]:
        print(f"\n{fix_pack['title']} ({fix_pack['priority']})")
        print(f"Timeline: {fix_pack['timeline']}")
        for fix in fix_pack.get('fixes', []):
            print(f"  • {fix['issue']}")