/**
 * IMMEDIATE TRANSCRIPTION FIX - Force activate for current session
 * session_1756315542894_aywlqzboo - 27+ seconds recording
 */

console.log('🚨 IMMEDIATE TRANSCRIPTION FIX LOADING');
console.log('Target session: session_1756315542894_aywlqzboo');

// Force immediate activation
(function() {
    console.log('🔧 FORCING IMMEDIATE HTTP TRANSCRIPTION ACTIVATION');
    
    const sessionId = 'session_1756315542894_aywlqzboo';
    let isTranscribing = false;
    
    // Clear the "Ready to record" message immediately
    function clearReadyMessage() {
        const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
        if (transcriptContainer && transcriptContainer.textContent.includes('Ready to record')) {
            transcriptContainer.innerHTML = `
                <div class="immediate-fix-active p-3 text-center">
                    <div class="spinner-border text-danger mb-2" role="status">
                        <span class="visually-hidden">Activating...</span>
                    </div>
                    <h6 class="text-danger">🚨 IMMEDIATE FIX ACTIVATED</h6>
                    <p class="text-warning mb-2">Emergency HTTP transcription starting...</p>
                    <p class="text-muted small mb-0">Session: ${sessionId}</p>
                </div>
            `;
            console.log('✅ Cleared "Ready to record" message');
        }
    }
    
    // Start immediate HTTP transcription
    async function startImmediateTranscription() {
        if (isTranscribing) return;
        
        console.log('🎯 Starting immediate HTTP transcription for active session');
        isTranscribing = true;
        
        try {
            // Get microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000
                }
            });
            
            console.log('✅ Microphone access granted');
            
            // Create MediaRecorder
            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            let chunkCount = 0;
            
            mediaRecorder.ondataavailable = async (event) => {
                if (event.data.size > 0) {
                    chunkCount++;
                    console.log(`🎵 Processing immediate chunk ${chunkCount}: ${event.data.size} bytes`);
                    
                    // Show processing feedback
                    showProcessingFeedback(chunkCount);
                    
                    // Process audio chunk
                    await processImmediateChunk(event.data, chunkCount);
                }
            };
            
            mediaRecorder.onerror = (error) => {
                console.error('❌ MediaRecorder error:', error);
                showError('MediaRecorder failed: ' + error.message);
            };
            
            // Start recording with 1-second chunks
            mediaRecorder.start(1000);
            console.log('✅ Immediate HTTP transcription active - 1-second chunks');
            
            // Update UI
            showTranscriptionActive();
            
        } catch (error) {
            console.error('❌ Immediate transcription failed:', error);
            showError('Microphone access failed: ' + error.message);
        }
    }
    
    async function processImmediateChunk(audioBlob, chunkNumber) {
        try {
            // Convert blob to base64
            const arrayBuffer = await audioBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            const base64Audio = btoa(String.fromCharCode.apply(null, uint8Array));
            
            const startTime = Date.now();
            
            // Send to HTTP endpoint
            console.log(`📡 Sending chunk ${chunkNumber} to /api/transcribe-audio`);
            
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    audio_data: base64Audio
                })
            });
            
            const latency = Date.now() - startTime;
            console.log(`⏱️ Request completed in ${latency}ms`);
            
            if (response.ok) {
                const result = await response.json();
                console.log(`📥 Response:`, result);
                
                if (result.text && result.text.trim() && !result.text.includes('[No speech detected]')) {
                    showTranscriptionResult(result, chunkNumber, latency);
                } else {
                    console.log(`⚠️ No speech detected in chunk ${chunkNumber}`);
                }
            } else {
                console.error(`❌ HTTP ${response.status}:`, await response.text());
                showError(`HTTP ${response.status}: Transcription service error`);
            }
            
        } catch (error) {
            console.error('❌ Chunk processing failed:', error);
            showError('Chunk processing failed: ' + error.message);
        }
    }
    
    function showTranscriptionActive() {
        const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
        if (transcriptContainer) {
            transcriptContainer.innerHTML = `
                <div class="immediate-transcription-active p-3">
                    <div class="d-flex align-items-center mb-3">
                        <div class="spinner-border text-success me-2" role="status">
                            <span class="visually-hidden">Processing...</span>
                        </div>
                        <h6 class="text-success mb-0">🎤 IMMEDIATE HTTP TRANSCRIPTION ACTIVE</h6>
                    </div>
                    <div class="status-indicators">
                        <span class="badge bg-danger me-2">WebSocket: Failed</span>
                        <span class="badge bg-success me-2">HTTP: Active</span>
                        <span class="badge bg-info">Emergency Mode</span>
                    </div>
                    <div class="mt-3">
                        <p class="text-info mb-2">
                            <strong>Status:</strong> Processing your speech in real-time via HTTP
                        </p>
                        <p class="text-muted small mb-0">
                            Session: ${sessionId} | Continue speaking...
                        </p>
                    </div>
                </div>
            `;
        }
    }
    
    function showProcessingFeedback(chunkNumber) {
        const statusElement = document.querySelector('#connectionStatus, .connection-status, #wsStatus');
        if (statusElement) {
            statusElement.innerHTML = `
                <span class="text-info">
                    🎵 Processing chunk ${chunkNumber}... (HTTP Mode)
                </span>
            `;
        }
    }
    
    function showTranscriptionResult(result, chunkNumber, latency) {
        const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
        
        if (transcriptContainer) {
            const timestamp = new Date().toLocaleTimeString();
            
            transcriptContainer.innerHTML = `
                <div class="immediate-transcription-result mb-3">
                    <div class="transcript-header d-flex justify-content-between align-items-center mb-2">
                        <h6 class="text-success mb-0">🚨 IMMEDIATE FIX SUCCESS!</h6>
                        <div class="text-end">
                            <small class="text-muted">Chunk: ${chunkNumber}</small><br>
                            <small class="text-muted">${latency}ms</small>
                        </div>
                    </div>
                    <div class="transcript-content p-3 border border-success rounded">
                        <div class="transcription-text text-success fw-bold fs-5">
                            ${result.text}
                        </div>
                        <div class="transcript-metadata mt-3 pt-2 border-top border-secondary">
                            <div class="d-flex justify-content-between">
                                <small class="text-muted">
                                    ${timestamp} • ${Math.round((result.confidence || 0.95) * 100)}% confidence
                                </small>
                                <small class="text-success">
                                    ✅ HTTP Mode Working
                                </small>
                            </div>
                        </div>
                    </div>
                    <div class="success-indicators mt-2 p-2 bg-success bg-opacity-10 rounded">
                        <small class="text-success">
                            🎉 <strong>Transcription Fixed!</strong> Your speech is being processed successfully.
                        </small>
                    </div>
                </div>
            `;
            
            console.log(`🎉 IMMEDIATE FIX SUCCESS: "${result.text}"`);
        }
    }
    
    function showError(message) {
        const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
        if (transcriptContainer) {
            transcriptContainer.innerHTML = `
                <div class="immediate-fix-error p-3 border border-danger rounded">
                    <h6 class="text-danger mb-2">⚠️ Immediate Fix Error</h6>
                    <p class="text-warning mb-2">${message}</p>
                    <button class="btn btn-sm btn-outline-danger" onclick="location.reload()">
                        🔄 Reload Page
                    </button>
                </div>
            `;
        }
    }
    
    // Execute immediately
    console.log('🚀 EXECUTING IMMEDIATE FIX');
    
    // Clear message immediately
    clearReadyMessage();
    
    // Start transcription after brief delay
    setTimeout(() => {
        startImmediateTranscription();
    }, 500);
    
})();

console.log('✅ Immediate transcription fix loaded and executing');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
