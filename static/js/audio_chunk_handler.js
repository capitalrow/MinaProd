/**
 * Audio Chunk Handler - Properly assembles and sends complete audio
 */

class AudioChunkHandler {
    constructor() {
        this.audioChunks = [];
        this.isProcessing = false;
        this.chunkQueue = [];
        this.sessionId = null;
    }
    
    /**
     * Collect audio chunks and process interim results
     */
    collectChunk(chunk) {
        this.audioChunks.push(chunk);
        console.log(`📦 Collected chunk: ${chunk.size} bytes (${this.audioChunks.length} total)`);
        
        // Process interim results every few chunks (every 3-5 chunks for ~3-5 second intervals)
        if (this.audioChunks.length % 3 === 0 && this.audioChunks.length > 2) {
            const recentChunks = this.audioChunks.slice(-3); // Last 3 chunks
            const interimBlob = new Blob(recentChunks, { type: 'audio/webm' });
            this.processInterimChunk(interimBlob, Math.floor(this.audioChunks.length / 3));
        }
    }
    
    /**
     * Assemble chunks into a complete audio file
     */
    async assembleAndSend() {
        if (this.audioChunks.length === 0) {
            console.log('No chunks to process');
            return;
        }
        
        if (this.isProcessing) {
            console.log('Already processing chunks');
            return;
        }
        
        this.isProcessing = true;
        
        try {
            // Create a complete blob from all chunks
            const completeBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            console.log(`🎵 Assembled complete audio: ${completeBlob.size} bytes`);
            
            // Clear chunks after assembling
            this.audioChunks = [];
            
            // Send the complete audio file
            await this.sendCompleteAudio(completeBlob);
            
        } catch (error) {
            console.error('❌ Error assembling audio:', error);
            window.toastSystem?.error('Failed to process audio');
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * Send complete audio file to backend using correct base64 format
     */
    async sendCompleteAudio(audioBlob) {
        try {
            // Convert blob to base64 as expected by backend
            const arrayBuffer = await audioBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            let binary = '';
            for (let i = 0; i < uint8Array.byteLength; i++) {
                binary += String.fromCharCode(uint8Array[i]);
            }
            const base64Audio = btoa(binary);
            
            console.log(`🎵 Sending ${audioBlob.size} bytes as base64 (${base64Audio.length} chars)`);
            
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'session_id': this.sessionId || `session_${Date.now()}`,
                    'audio_data': base64Audio,
                    'action': 'transcribe',
                    'chunk_id': '1'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Transcription successful:', result);
                
                // Update UI with transcript
                if (result.final_text) {
                    this.displayFinalTranscript(result.final_text);
                } else if (result.text) {
                    this.displayFinalTranscript(result.text);
                }
                
                // Update statistics
                const processingTime = result.processing_time || (result.processing_time_ms ? result.processing_time_ms : 0);
                if (window.updateSessionStats) {
                    window.updateSessionStats({
                        words: result.word_count || (result.text ? result.text.split(' ').length : 0),
                        latency: `${Math.round(processingTime)}ms`,
                        accuracy: result.confidence ? `${Math.round(result.confidence * 100)}%` : '95%'
                    });
                }
                
                window.toastSystem?.success('Transcription complete');
                
            } else {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                console.error('❌ Transcription failed:', errorData);
                const errorMsg = errorData.message || errorData.error || 'Transcription failed';
                window.toastSystem?.error(`Error: ${errorMsg}`);
            }
            
        } catch (error) {
            console.error('❌ Network error:', error);
            window.toastSystem?.error(`Connection error: ${error.message}`);
        }
    }
    
    /**
     * Display final transcript in UI
     */
    displayFinalTranscript(text) {
        // Find transcript display areas
        const displays = [
            document.getElementById('fullTranscriptText'),
            document.getElementById('final-transcript'),
            document.querySelector('.complete-transcript-display'),
            document.querySelector('.transcript-content')
        ];
        
        for (const display of displays) {
            if (display) {
                if (display.tagName === 'INPUT' || display.tagName === 'TEXTAREA') {
                    display.value = text;
                } else {
                    display.textContent = text;
                }
                display.style.display = 'block';
            }
        }
        
        // Hide placeholder
        const placeholder = document.getElementById('transcriptPlaceholder');
        if (placeholder) placeholder.style.display = 'none';
        
        console.log(`📝 Final transcript displayed: "${text.substring(0, 50)}..."`);
    }
    
    /**
     * Add interim transcription processing for real-time results
     */
    async processInterimChunk(chunkBlob, chunkIndex) {
        if (this.isProcessing) return; // Prevent concurrent processing
        
        try {
            this.isProcessing = true;
            
            // Convert chunk to base64
            const arrayBuffer = await chunkBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            let binary = '';
            for (let i = 0; i < uint8Array.byteLength; i++) {
                binary += String.fromCharCode(uint8Array[i]);
            }
            const base64Audio = btoa(binary);
            
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'session_id': this.sessionId,
                    'audio_data': base64Audio,
                    'action': 'transcribe',
                    'chunk_id': chunkIndex.toString(),
                    'is_interim': 'true'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.text && result.text.trim()) {
                    this.displayInterimText(result.text, chunkIndex);
                }
            }
            
        } catch (error) {
            console.warn(`⚠️ Interim processing failed for chunk ${chunkIndex}:`, error);
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * Display interim text updates
     */
    displayInterimText(text, chunkIndex) {
        const interimDisplay = document.getElementById('interim-transcript') || 
                             document.querySelector('.interim-transcript');
        
        if (interimDisplay) {
            interimDisplay.innerHTML = `
                <div class="interim-chunk" data-chunk="${chunkIndex}">
                    <span class="interim-text">${text}</span>
                    <small class="interim-timestamp">${new Date().toLocaleTimeString()}</small>
                </div>
            `;
            interimDisplay.style.display = 'block';
        }
        
        console.log(`🔄 Interim result (chunk ${chunkIndex}): "${text}"`);
    }
    
    /**
     * Start a new recording session
     */
    startSession() {
        this.sessionId = `session_${Date.now()}`;
        this.audioChunks = [];
        this.isProcessing = false;
        console.log(`🎤 Started new session: ${this.sessionId}`);
    }
    
    /**
     * End the recording session and process audio
     */
    async endSession() {
        console.log(`🛑 Ending session: ${this.sessionId}`);
        await this.assembleAndSend();
    }
}

// Create global instance
window.audioChunkHandler = new AudioChunkHandler();

console.log('✅ Audio chunk handler initialized');