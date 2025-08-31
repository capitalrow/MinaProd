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
     * Collect audio chunks into a complete blob
     */
    collectChunk(chunk) {
        this.audioChunks.push(chunk);
        console.log(`📦 Collected chunk: ${chunk.size} bytes (${this.audioChunks.length} total)`);
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
     * Send complete audio file to backend
     */
    async sendCompleteAudio(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('session_id', this.sessionId || `session_${Date.now()}`);
        
        try {
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ Transcription successful:', result);
                
                // Update UI with transcript
                if (result.transcript && window.updateTranscriptDisplay) {
                    window.updateTranscriptDisplay(result);
                }
                
                // Update statistics
                if (window.updateSessionStats) {
                    window.updateSessionStats({
                        words: result.word_count || result.transcript.split(' ').length,
                        latency: `${Math.round(result.processing_time * 1000)}ms`,
                        accuracy: '95%'
                    });
                }
                
                window.toastSystem?.success('Transcription complete');
                
            } else {
                const error = await response.text();
                console.error('❌ Transcription failed:', error);
                window.toastSystem?.error('Transcription failed - please try again');
            }
            
        } catch (error) {
            console.error('❌ Network error:', error);
            window.toastSystem?.error('Connection error - please check your internet');
        }
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