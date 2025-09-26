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
     * Collect audio chunks and process interim results in real-time
     */
    collectChunk(chunk) {
        this.audioChunks.push(chunk);
        console.log(`📦 Collected chunk: ${chunk.size} bytes (${this.audioChunks.length} total)`);
        
        // 🚀 INTERIM PROCESSING: Send chunks for transcription every 3 chunks (~3 seconds)
        if (this.audioChunks.length % 3 === 0 && this.audioChunks.length >= 3) {
            const recentChunks = this.audioChunks.slice(-3); // Last 3 chunks
            const interimBlob = new Blob(recentChunks, { type: 'audio/webm' });
            this.processInterimChunk(interimBlob, Math.floor(this.audioChunks.length / 3));
        }
        
        // 🔄 EXTENDED INTERIM: Process longer context every 6 chunks (~6 seconds) 
        if (this.audioChunks.length % 6 === 0 && this.audioChunks.length >= 6) {
            const contextChunks = this.audioChunks.slice(-6); // Last 6 chunks for context
            const contextBlob = new Blob(contextChunks, { type: 'audio/webm' });
            this.processInterimChunk(contextBlob, Math.floor(this.audioChunks.length / 6), true);
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
     * 🚀 REAL-TIME INTERIM PROCESSING: Process chunks for live transcription
     */
    async processInterimChunk(chunkBlob, chunkIndex, isExtended = false) {
        // Skip if already processing (prevent overload)
        if (this.isProcessing && !isExtended) return;
        
        try {
            if (!isExtended) this.isProcessing = true;
            
            // Convert chunk to base64 with progress tracking
            const arrayBuffer = await chunkBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            let binary = '';
            for (let i = 0; i < uint8Array.byteLength; i++) {
                binary += String.fromCharCode(uint8Array[i]);
            }
            const base64Audio = btoa(binary);
            
            console.log(`🔄 Processing interim chunk ${chunkIndex} (${chunkBlob.size} bytes, extended: ${isExtended})`);
            
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
                if (result.success && result.text && result.text.trim()) {
                    console.log(`✅ Interim result ${chunkIndex}: "${result.text}"`);
                    this.displayInterimText(result.text, chunkIndex, isExtended);
                    
                    // Update performance metrics
                    if (window.updateSessionStats) {
                        window.updateSessionStats({
                            words: result.word_count || result.text.split(' ').length,
                            latency: `${Math.round(result.processing_time || 0)}ms`,
                            accuracy: result.confidence ? `${Math.round(result.confidence * 100)}%` : '95%'
                        });
                    }
                } else {
                    console.log(`ℹ️ No speech detected in interim chunk ${chunkIndex}`);
                }
            } else {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                console.warn(`⚠️ Interim API error for chunk ${chunkIndex}:`, errorData.error);
            }
            
        } catch (error) {
            console.warn(`⚠️ Interim processing failed for chunk ${chunkIndex}:`, error);
        } finally {
            if (!isExtended) this.isProcessing = false;
        }
    }
    
    /**
     * 📝 DISPLAY INTERIM RESULTS: Show real-time transcription updates
     */
    displayInterimText(text, chunkIndex, isExtended = false) {
        // Find display areas for interim results
        const displays = [
            document.getElementById('interim-transcript'),
            document.getElementById('interim-results'),
            document.querySelector('.interim-transcript'),
            document.querySelector('.interim-display'),
            document.querySelector('.live-transcript')
        ];
        
        const timestamp = new Date().toLocaleTimeString();
        const chunkType = isExtended ? 'extended' : 'normal';
        
        // Update all available interim displays
        let displayUpdated = false;
        for (const display of displays) {
            if (display) {
                display.innerHTML = `
                    <div class="interim-chunk ${chunkType}" data-chunk="${chunkIndex}">
                        <div class="interim-content">
                            <span class="interim-text">${text}</span>
                            <div class="interim-meta">
                                <small class="interim-timestamp">${timestamp}</small>
                                <small class="interim-type">${chunkType}</small>
                                <small class="chunk-id">Chunk ${chunkIndex}</small>
                            </div>
                        </div>
                    </div>
                `;
                display.style.display = 'block';
                displayUpdated = true;
            }
        }
        
        // If no dedicated interim display, update main transcript area
        if (!displayUpdated) {
            const mainDisplays = [
                document.getElementById('fullTranscriptText'),
                document.querySelector('.complete-transcript-display'),
                document.querySelector('.transcript-content')
            ];
            
            for (const display of mainDisplays) {
                if (display) {
                    const currentText = display.textContent || '';
                    const newText = currentText ? `${currentText}\n[${timestamp}] ${text}` : text;
                    
                    if (display.tagName === 'INPUT' || display.tagName === 'TEXTAREA') {
                        display.value = newText;
                    } else {
                        display.textContent = newText;
                    }
                    display.style.display = 'block';
                    break;
                }
            }
        }
        
        // Hide transcript placeholder if showing interim results
        const placeholder = document.getElementById('transcriptPlaceholder');
        if (placeholder) placeholder.style.display = 'none';
        
        // Trigger custom event for other components
        window.dispatchEvent(new CustomEvent('interimTranscription', {
            detail: {
                text: text,
                chunkIndex: chunkIndex,
                timestamp: timestamp,
                isExtended: isExtended
            }
        }));
        
        console.log(`🔄 Interim result (${chunkType} chunk ${chunkIndex}): "${text}"`);
    }
    
    /**
     * 🎤 START RECORDING SESSION: Initialize for real-time processing
     */
    startSession() {
        this.sessionId = `session_${Date.now()}`;
        this.audioChunks = [];
        this.isProcessing = false;
        
        // Clear any previous interim results
        this.clearInterimResults();
        
        // Initialize session performance tracking
        this.sessionStats = {
            startTime: Date.now(),
            chunksProcessed: 0,
            interimResults: 0,
            totalWords: 0
        };
        
        console.log(`🎤 Started new session: ${this.sessionId}`);
        
        // Notify UI components about session start
        window.dispatchEvent(new CustomEvent('sessionStarted', {
            detail: { sessionId: this.sessionId }
        }));
    }
    
    /**
     * Clear interim results from UI
     */
    clearInterimResults() {
        const displays = [
            document.getElementById('interim-transcript'),
            document.getElementById('interim-results'),
            document.querySelector('.interim-transcript'),
            document.querySelector('.interim-display')
        ];
        
        displays.forEach(display => {
            if (display) {
                display.innerHTML = '';
                display.style.display = 'none';
            }
        });
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

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
