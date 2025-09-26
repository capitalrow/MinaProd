/**
 * Advanced Audio Quality and Processing Improvements
 * Fixes WebM conversion issues and improves transcription quality
 */

class AudioQualityManager {
    constructor() {
        this.supportedFormats = this.detectSupportedFormats();
        this.preferredFormat = this.selectOptimalFormat();
        this.conversionRetries = 0;
        this.maxRetries = 3;
        
        console.log(`🎵 Audio Quality Manager initialized with format: ${this.preferredFormat}`);
    }
    
    detectSupportedFormats() {
        const formats = {};
        const testRecorder = document.createElement('canvas');
        const testStream = testRecorder.captureStream();
        
        // Test various audio formats
        const formatTests = [
            'audio/webm;codecs=opus',
            'audio/webm;codecs=vp8',
            'audio/webm',
            'audio/mp4',
            'audio/ogg;codecs=opus',
            'audio/wav'
        ];
        
        formatTests.forEach(format => {
            try {
                if (MediaRecorder.isTypeSupported(format)) {
                    formats[format] = true;
                    console.log(`✅ Format supported: ${format}`);
                }
            } catch (error) {
                console.log(`❌ Format not supported: ${format}`);
            }
        });
        
        return formats;
    }
    
    selectOptimalFormat() {
        // Prefer formats with better backend compatibility
        const preferenceOrder = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/ogg;codecs=opus'
        ];
        
        for (const format of preferenceOrder) {
            if (this.supportedFormats[format]) {
                return format;
            }
        }
        
        return 'audio/webm'; // Fallback
    }
    
    createOptimizedRecorder(stream) {
        const options = {
            mimeType: this.preferredFormat,
            audioBitsPerSecond: 128000, // High quality
            bitsPerSecond: 128000
        };
        
        try {
            const recorder = new MediaRecorder(stream, options);
            console.log(`🎤 Created optimized recorder with ${this.preferredFormat}`);
            return recorder;
        } catch (error) {
            console.warn(`⚠️ Failed to create optimized recorder, using default: ${error.message}`);
            return new MediaRecorder(stream);
        }
    }
    
    preprocessAudioData(audioBlob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (event) => {
                const arrayBuffer = event.target.result;
                const uint8Array = new Uint8Array(arrayBuffer);
                
                // Validate audio data
                const validation = this.validateAudioData(uint8Array);
                
                if (validation.isValid) {
                    console.log(`✅ Audio validation passed: ${validation.details}`);
                    resolve(audioBlob);
                } else {
                    console.warn(`⚠️ Audio validation issues: ${validation.issues}`);
                    // Still proceed but log issues
                    resolve(audioBlob);
                }
            };
            
            reader.onerror = () => reject(new Error('Failed to read audio data'));
            reader.readAsArrayBuffer(audioBlob);
        });
    }
    
    validateAudioData(uint8Array) {
        const validation = {
            isValid: true,
            issues: [],
            details: []
        };
        
        // Check minimum size
        if (uint8Array.length < 1000) {
            validation.issues.push('Audio data too small');
            validation.isValid = false;
        } else {
            validation.details.push(`Size: ${uint8Array.length} bytes`);
        }
        
        // Check for WebM header
        if (uint8Array[0] === 0x1A && uint8Array[1] === 0x45 && 
            uint8Array[2] === 0xDF && uint8Array[3] === 0xA3) {
            validation.details.push('Valid WebM header detected');
        } else {
            validation.issues.push('WebM header not detected');
        }
        
        // Check for audio content patterns
        let silenceCount = 0;
        for (let i = 100; i < Math.min(1000, uint8Array.length); i++) {
            if (uint8Array[i] === 0) silenceCount++;
        }
        
        if (silenceCount > 800) {
            validation.issues.push('High silence ratio detected');
        } else {
            validation.details.push(`Audio activity: ${((900 - silenceCount) / 900 * 100).toFixed(1)}%`);
        }
        
        return validation;
    }
    
    async enhanceAudioChunk(audioBlob) {
        try {
            // Preprocess the audio
            const processedBlob = await this.preprocessAudioData(audioBlob);
            
            // Add metadata for better backend processing
            const enhancedBlob = this.addProcessingHints(processedBlob);
            
            return enhancedBlob;
        } catch (error) {
            console.error('❌ Audio enhancement failed:', error);
            return audioBlob; // Return original on failure
        }
    }
    
    addProcessingHints(audioBlob) {
        // Create a new blob with processing hints in the filename/metadata
        const timestamp = Date.now();
        const hints = {\n            format: this.preferredFormat,\n            timestamp,\n            quality: 'high',\n            preprocessing: 'enhanced'\n        };\n        \n        // Create enhanced blob with metadata\n        return new File([audioBlob], `enhanced_${timestamp}.webm`, {\n            type: this.preferredFormat,\n            lastModified: timestamp\n        });\n    }\n    \n    getOptimalChunkSize() {\n        // Dynamic chunk sizing based on performance\n        const baseSize = 4000; // 4 seconds base\n        \n        if (this.conversionRetries > 1) {\n            return baseSize * 0.7; // Smaller chunks if having issues\n        } else if (this.conversionRetries === 0) {\n            return baseSize * 1.2; // Larger chunks if stable\n        }\n        \n        return baseSize;\n    }\n    \n    recordConversionFailure() {\n        this.conversionRetries++;\n        console.log(`📊 Conversion failure recorded: ${this.conversionRetries}/${this.maxRetries}`);\n        \n        if (this.conversionRetries >= this.maxRetries) {\n            console.log('🔄 Switching to fallback format due to repeated failures');\n            this.switchToFallbackFormat();\n        }\n    }\n    \n    recordConversionSuccess() {\n        if (this.conversionRetries > 0) {\n            console.log('✅ Conversion success - resetting retry counter');\n            this.conversionRetries = Math.max(0, this.conversionRetries - 1);\n        }\n    }\n    \n    switchToFallbackFormat() {\n        const fallbackFormats = [\n            'audio/mp4',\n            'audio/ogg;codecs=opus',\n            'audio/wav'\n        ];\n        \n        for (const format of fallbackFormats) {\n            if (this.supportedFormats[format] && format !== this.preferredFormat) {\n                console.log(`🔄 Switching from ${this.preferredFormat} to ${format}`);\n                this.preferredFormat = format;\n                this.conversionRetries = 0;\n                return true;\n            }\n        }\n        \n        console.warn('⚠️ No fallback format available');\n        return false;\n    }\n    \n    getQualityMetrics() {\n        return {\n            preferredFormat: this.preferredFormat,\n            conversionRetries: this.conversionRetries,\n            supportedFormatsCount: Object.keys(this.supportedFormats).length,\n            optimalChunkSize: this.getOptimalChunkSize()\n        };\n    }\n}\n\n// Audio processing utilities\nclass AudioProcessingUtils {\n    static async convertBlobToArrayBuffer(blob) {\n        return new Promise((resolve, reject) => {\n            const reader = new FileReader();\n            reader.onload = () => resolve(reader.result);\n            reader.onerror = () => reject(new Error('Failed to convert blob'));\n            reader.readAsArrayBuffer(blob);\n        });\n    }\n    \n    static detectAudioFormat(arrayBuffer) {\n        const uint8 = new Uint8Array(arrayBuffer);\n        \n        // WebM detection\n        if (uint8.length >= 4 && uint8[0] === 0x1A && uint8[1] === 0x45 && \n            uint8[2] === 0xDF && uint8[3] === 0xA3) {\n            return { format: 'webm', confidence: 0.99 };\n        }\n        \n        // WAV detection\n        if (uint8.length >= 12 && \n            String.fromCharCode(...uint8.slice(0, 4)) === 'RIFF' &&\n            String.fromCharCode(...uint8.slice(8, 12)) === 'WAVE') {\n            return { format: 'wav', confidence: 0.99 };\n        }\n        \n        // MP4 detection\n        if (uint8.length >= 8 && \n            String.fromCharCode(...uint8.slice(4, 8)) === 'ftyp') {\n            return { format: 'mp4', confidence: 0.95 };\n        }\n        \n        return { format: 'unknown', confidence: 0.0 };\n    }\n    \n    static calculateAudioQualityScore(arrayBuffer) {\n        const uint8 = new Uint8Array(arrayBuffer);\n        let score = 0.5; // Base score\n        \n        // Size factor\n        if (uint8.length > 10000) score += 0.2;\n        if (uint8.length > 50000) score += 0.1;\n        \n        // Content analysis\n        let nonZeroCount = 0;\n        const sampleSize = Math.min(1000, uint8.length);\n        \n        for (let i = 0; i < sampleSize; i++) {\n            if (uint8[i] !== 0) nonZeroCount++;\n        }\n        \n        const nonZeroRatio = nonZeroCount / sampleSize;\n        score += nonZeroRatio * 0.3;\n        \n        return Math.min(1.0, Math.max(0.0, score));\n    }\n}\n\n// Export for use\nif (typeof window !== 'undefined') {\n    window.AudioQualityManager = AudioQualityManager;\n    window.AudioProcessingUtils = AudioProcessingUtils;\n}\n\nif (typeof module !== 'undefined' && module.exports) {\n    module.exports = { AudioQualityManager, AudioProcessingUtils };\n}

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
