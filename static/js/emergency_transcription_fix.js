/**
 * EMERGENCY FIX: Activate HTTP transcription for current session
 */

console.log('🚨 EMERGENCY TRANSCRIPTION FIX LOADING');

// Wait for page to load, then check if recording is active
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        console.log('🔍 Checking for active recording session...');
        
        // Look for red recording button or timer
        const recordButton = document.querySelector('.record-button, .recording-button, button[onclick*="toggleRecording"]');
        const timer = document.querySelector('.timer, #timer, .recording-timer');
        
        if (recordButton && recordButton.classList.contains('recording')) {
            console.log('🎤 ACTIVE RECORDING DETECTED - FORCING HTTP MODE');
            forceHttpTranscription();
        } else if (timer && timer.textContent.includes(':')) {
            console.log('🎤 TIMER DETECTED - FORCING HTTP MODE');
            forceHttpTranscription();
        }
    }, 1000);
});

function forceHttpTranscription() {
    console.log('🔧 FORCING HTTP TRANSCRIPTION MODE');
    
    // Get session ID from any visible element or generate
    let sessionId = 'session_1756315009342_kzdotxgrk'; // User's current session
    
    // Try to find session ID in page
    const sessionElements = document.querySelectorAll('[data-session-id], [id*="session"], [class*="session"]');
    for (const element of sessionElements) {
        const foundSessionId = element.dataset.sessionId || element.id || element.textContent;
        if (foundSessionId && foundSessionId.includes('session_')) {
            sessionId = foundSessionId;
            break;
        }
    }
    
    console.log(`🎯 Using session ID: ${sessionId}`);
    
    // Clear any "Ready to record" message
    const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
    if (transcriptContainer && transcriptContainer.textContent.includes('Ready to record')) {
        transcriptContainer.innerHTML = `
            <div class="emergency-activation p-3 text-center">
                <div class="spinner-border text-warning mb-2" role="status">
                    <span class="visually-hidden">Activating...</span>
                </div>
                <h6 class="text-warning">🚨 Emergency HTTP Mode Activated</h6>
                <p class="text-muted mb-0">Processing your active recording...</p>
            </div>
        `;
    }
    
    // Start HTTP transcription if available
    if (window.directAudioTranscription) {
        console.log('✅ Starting Direct HTTP Audio Transcription');
        window.directAudioTranscription.startTranscription(sessionId);
    } else {
        console.log('⚠️ Direct Audio Transcription not available, creating fallback');
        createFallbackHttpTranscription(sessionId);
    }
}

function createFallbackHttpTranscription(sessionId) {
    console.log('🔧 Creating fallback HTTP transcription system');
    
    // Initialize basic HTTP transcription
    window.emergencyHttpTranscription = {
        sessionId: sessionId,
        isRecording: false,
        chunkCount: 0,
        
        async startTranscription() {
            try {
                console.log('🎯 Emergency HTTP transcription starting');
                
                // Get microphone access
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 16000
                    }
                });
                
                // Create MediaRecorder
                const mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                
                mediaRecorder.ondataavailable = async (event) => {
                    if (event.data.size > 0) {
                        this.chunkCount++;
                        console.log(`🎵 Emergency processing chunk ${this.chunkCount}`);
                        await this.processChunk(event.data);
                    }
                };
                
                mediaRecorder.start(1000); // 1-second chunks
                this.isRecording = true;
                
                console.log('✅ Emergency HTTP transcription active');
                
            } catch (error) {
                console.error('❌ Emergency transcription failed:', error);
            }
        },
        
        async processChunk(audioBlob) {
            try {
                // Convert to base64
                const arrayBuffer = await audioBlob.arrayBuffer();
                const uint8Array = new Uint8Array(arrayBuffer);
                const base64Audio = btoa(String.fromCharCode.apply(null, uint8Array));
                
                // Send to HTTP endpoint
                const response = await fetch('/api/transcribe-audio', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        audio_data: base64Audio
                    })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    this.displayResult(result);
                }
                
            } catch (error) {
                console.error('❌ Emergency chunk processing failed:', error);
            }
        },
        
        displayResult(result) {
            const transcriptContainer = document.querySelector('.live-transcript-container, #transcript, #transcriptContent, .transcript-content');
            if (transcriptContainer && result.text && result.text.trim()) {
                const timestamp = new Date().toLocaleTimeString();
                
                transcriptContainer.innerHTML = `
                    <div class="emergency-transcript mb-3">
                        <div class="transcript-header d-flex justify-content-between align-items-center mb-2">
                            <h6 class="text-warning mb-0">🚨 Emergency HTTP Mode</h6>
                            <small class="text-muted">Chunk: ${this.chunkCount}</small>
                        </div>
                        <div class="transcript-content p-3 border border-warning rounded">
                            <div class="emergency-text text-warning fw-bold">
                                ${result.text}
                            </div>
                            <div class="transcript-metadata mt-2 pt-2 border-top border-secondary">
                                <small class="text-muted">
                                    ${timestamp} • Emergency Mode Active
                                </small>
                            </div>
                        </div>
                    </div>
                `;
                
                console.log(`📝 EMERGENCY TRANSCRIPT: "${result.text}"`);
            }
        }
    };
    
    // Start emergency transcription
    window.emergencyHttpTranscription.startTranscription();
}

console.log('✅ Emergency transcription fix loaded and ready');