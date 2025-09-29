/**
 * ADVANCED AUDIO VISUALIZER
 * Comprehensive real-time audio visualization with frequency analysis,
 * voice activity detection, speaker identification, and quality monitoring.
 */

class AdvancedAudioVisualizer {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('❌ Canvas element not found:', canvasId);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.config = {
            fftSize: 2048,
            smoothingTimeConstant: 0.8,
            minDecibels: -90,
            maxDecibels: -10,
            updateInterval: 16, // ~60fps
            ...options
        };

        // Visualization state
        this.isActive = false;
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.freqDataArray = null;
        
        // Visual elements
        this.animationId = null;
        this.gradients = this._createGradients();
        
        // Audio analysis
        this.audioMetrics = {
            rmsLevel: 0,
            peakLevel: 0,
            spectralCentroid: 0,
            zeroCrossingRate: 0,
            voiceActivity: false,
            speechProbability: 0,
            dominantFrequency: 0,
            spectralRolloff: 0
        };

        // Speaker visualization
        this.speakerColors = new Map();
        this.activeSpeakers = new Set();
        this.speakerHistory = [];

        // Performance tracking
        this.frameCount = 0;
        this.lastFpsUpdate = 0;
        this.currentFps = 0;

        // Event callbacks
        this.onAudioMetrics = options.onAudioMetrics || (() => {});
        this.onVoiceActivity = options.onVoiceActivity || (() => {});
        this.onSpeakerChange = options.onSpeakerChange || (() => {});

        this._initializeCanvas();
        console.log('🎨 Advanced Audio Visualizer initialized');
    }

    _initializeCanvas() {
        // Set canvas size for high-DPI displays
        const devicePixelRatio = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        
        this.canvas.width = rect.width * devicePixelRatio;
        this.canvas.height = rect.height * devicePixelRatio;
        
        this.ctx.scale(devicePixelRatio, devicePixelRatio);
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';

        // Set up context properties
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
    }

    _createGradients() {
        const gradients = {};
        
        // Voice activity gradient
        const voiceGradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        voiceGradient.addColorStop(0, 'rgba(16, 185, 129, 0.9)'); // Green
        voiceGradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.7)'); // Blue
        voiceGradient.addColorStop(1, 'rgba(99, 102, 241, 0.5)'); // Purple
        gradients.voice = voiceGradient;

        // Silence gradient
        const silenceGradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        silenceGradient.addColorStop(0, 'rgba(156, 163, 175, 0.5)'); // Gray
        silenceGradient.addColorStop(1, 'rgba(107, 114, 128, 0.3)');
        gradients.silence = silenceGradient;

        // Frequency gradient
        const freqGradient = this.ctx.createLinearGradient(0, 0, this.canvas.width, 0);
        freqGradient.addColorStop(0, 'rgba(239, 68, 68, 0.8)'); // Red (low freq)
        freqGradient.addColorStop(0.3, 'rgba(245, 158, 11, 0.8)'); // Orange
        freqGradient.addColorStop(0.6, 'rgba(34, 197, 94, 0.8)'); // Green (mid freq)
        freqGradient.addColorStop(1, 'rgba(59, 130, 246, 0.8)'); // Blue (high freq)
        gradients.frequency = freqGradient;

        return gradients;
    }

    connectAudioSource(audioSource) {
        try {
            if (!audioSource) {
                console.error('❌ No audio source provided');
                return false;
            }

            // Create audio context if needed
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }

            // Create analyser
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = this.config.fftSize;
            this.analyser.smoothingTimeConstant = this.config.smoothingTimeConstant;
            this.analyser.minDecibels = this.config.minDecibels;
            this.analyser.maxDecibels = this.config.maxDecibels;

            // Connect audio source
            const source = this.audioContext.createMediaStreamSource(audioSource);
            source.connect(this.analyser);

            // Initialize data arrays
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            this.freqDataArray = new Uint8Array(this.analyser.frequencyBinCount);

            console.log('🔊 Audio source connected to visualizer');
            return true;

        } catch (error) {
            console.error('❌ Failed to connect audio source:', error);
            return false;
        }
    }

    start() {
        if (!this.analyser) {
            console.warn('⚠️ No audio analyser available');
            return;
        }

        this.isActive = true;
        this.lastFpsUpdate = performance.now();
        this._animate();
        console.log('▶️ Audio visualizer started');
    }

    stop() {
        this.isActive = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        this._clearCanvas();
        console.log('⏹️ Audio visualizer stopped');
    }

    _animate() {
        if (!this.isActive) return;

        this.animationId = requestAnimationFrame(() => this._animate());

        // Get audio data
        this.analyser.getByteFrequencyData(this.dataArray);
        this.analyser.getByteTimeDomainData(this.freqDataArray);

        // Analyze audio
        this._analyzeAudio();

        // Render visualization
        this._render();

        // Update performance metrics
        this._updatePerformanceMetrics();
    }

    _analyzeAudio() {
        try {
            const freqData = this.dataArray;
            const timeData = this.freqDataArray;

            // Calculate RMS level
            let rmsSum = 0;
            let peakLevel = 0;
            for (let i = 0; i < timeData.length; i++) {
                const sample = (timeData[i] - 128) / 128; // Normalize to -1 to 1
                rmsSum += sample * sample;
                peakLevel = Math.max(peakLevel, Math.abs(sample));
            }
            this.audioMetrics.rmsLevel = Math.sqrt(rmsSum / timeData.length);
            this.audioMetrics.peakLevel = peakLevel;

            // Calculate spectral centroid
            let weightedSum = 0;
            let magnitudeSum = 0;
            const sampleRate = this.audioContext.sampleRate;
            const binSize = sampleRate / (2 * freqData.length);

            for (let i = 0; i < freqData.length; i++) {
                const frequency = i * binSize;
                const magnitude = freqData[i] / 255;
                weightedSum += frequency * magnitude;
                magnitudeSum += magnitude;
            }
            
            this.audioMetrics.spectralCentroid = magnitudeSum > 0 ? weightedSum / magnitudeSum : 0;

            // Calculate zero crossing rate
            let zeroCrossings = 0;
            for (let i = 1; i < timeData.length; i++) {
                if ((timeData[i] >= 128) !== (timeData[i - 1] >= 128)) {
                    zeroCrossings++;
                }
            }
            this.audioMetrics.zeroCrossingRate = zeroCrossings / timeData.length;

            // Voice activity detection
            const energyThreshold = 0.01;
            const zcrThreshold = 0.05;
            const spectralThreshold = 1000;

            const energyActive = this.audioMetrics.rmsLevel > energyThreshold;
            const zcrActive = this.audioMetrics.zeroCrossingRate > zcrThreshold && 
                            this.audioMetrics.zeroCrossingRate < 0.3;
            const spectralActive = this.audioMetrics.spectralCentroid > spectralThreshold;

            const voiceActivity = energyActive && zcrActive && spectralActive;
            this.audioMetrics.voiceActivity = voiceActivity;

            // Calculate speech probability
            let speechScore = 0;
            if (energyActive) speechScore += 0.3;
            if (zcrActive) speechScore += 0.3;
            if (spectralActive) speechScore += 0.4;
            this.audioMetrics.speechProbability = speechScore;

            // Find dominant frequency
            let maxMagnitude = 0;
            let dominantBin = 0;
            for (let i = 0; i < freqData.length; i++) {
                if (freqData[i] > maxMagnitude) {
                    maxMagnitude = freqData[i];
                    dominantBin = i;
                }
            }
            this.audioMetrics.dominantFrequency = dominantBin * binSize;

            // Calculate spectral rolloff (85% of energy)
            const totalEnergy = freqData.reduce((sum, val) => sum + val, 0);
            let cumulativeEnergy = 0;
            let rolloffBin = freqData.length - 1;
            
            for (let i = 0; i < freqData.length; i++) {
                cumulativeEnergy += freqData[i];
                if (cumulativeEnergy >= 0.85 * totalEnergy) {
                    rolloffBin = i;
                    break;
                }
            }
            this.audioMetrics.spectralRolloff = rolloffBin * binSize;

            // Emit callbacks
            this.onAudioMetrics(this.audioMetrics);
            
            if (voiceActivity !== this.previousVoiceActivity) {
                this.onVoiceActivity(voiceActivity, this.audioMetrics);
                this.previousVoiceActivity = voiceActivity;
            }

        } catch (error) {
            console.warn('⚠️ Audio analysis error:', error);
        }
    }

    _render() {
        this._clearCanvas();

        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        // Choose visualization mode based on voice activity
        if (this.audioMetrics.voiceActivity) {
            this._renderVoiceVisualization(width, height);
        } else {
            this._renderSilenceVisualization(width, height);
        }

        // Render additional overlays
        this._renderMetricsOverlay(width, height);
        this._renderSpeakerIndicators(width, height);
    }

    _renderVoiceVisualization(width, height) {
        const freqData = this.dataArray;
        const barWidth = width / freqData.length * 2.5;
        
        this.ctx.fillStyle = this.gradients.frequency;
        
        for (let i = 0; i < freqData.length; i++) {
            const barHeight = (freqData[i] / 255) * height * 0.8;
            const x = i * barWidth;
            const y = height - barHeight;
            
            // Add some visual effects
            const intensity = freqData[i] / 255;
            const alpha = 0.3 + intensity * 0.7;
            
            this.ctx.globalAlpha = alpha;
            this.ctx.fillRect(x, y, barWidth - 1, barHeight);
            
            // Add glow effect for high intensity
            if (intensity > 0.7) {
                this.ctx.shadowColor = 'rgba(59, 130, 246, 0.8)';
                this.ctx.shadowBlur = 10;
                this.ctx.fillRect(x, y, barWidth - 1, barHeight);
                this.ctx.shadowBlur = 0;
            }
        }
        
        this.ctx.globalAlpha = 1;
    }

    _renderSilenceVisualization(width, height) {
        const timeData = this.freqDataArray;
        
        // Draw waveform
        this.ctx.strokeStyle = this.gradients.silence;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        
        const sliceWidth = width / timeData.length;
        let x = 0;
        
        for (let i = 0; i < timeData.length; i++) {
            const v = (timeData[i] - 128) / 128; // Normalize
            const y = (v * height / 4) + height / 2;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        this.ctx.stroke();
        
        // Add subtle animated background
        const time = Date.now() * 0.001;
        const pulseAlpha = 0.1 + 0.05 * Math.sin(time * 2);
        
        this.ctx.fillStyle = `rgba(156, 163, 175, ${pulseAlpha})`;
        this.ctx.fillRect(0, height * 0.4, width, height * 0.2);
    }

    _renderMetricsOverlay(width, height) {
        // Voice activity indicator
        const indicatorSize = 20;
        const x = width - 30;
        const y = 30;
        
        this.ctx.beginPath();
        this.ctx.arc(x, y, indicatorSize / 2, 0, 2 * Math.PI);
        
        if (this.audioMetrics.voiceActivity) {
            this.ctx.fillStyle = '#10B981'; // Green
            this.ctx.shadowColor = '#10B981';
            this.ctx.shadowBlur = 10;
        } else {
            this.ctx.fillStyle = '#6B7280'; // Gray
            this.ctx.shadowBlur = 0;
        }
        
        this.ctx.fill();
        this.ctx.shadowBlur = 0;

        // Level meters
        this._renderLevelMeters(width, height);
    }

    _renderLevelMeters(width, height) {
        const meterWidth = 4;
        const meterHeight = height * 0.6;
        const meterX = 20;
        const meterY = (height - meterHeight) / 2;

        // RMS level meter
        this.ctx.fillStyle = '#374151';
        this.ctx.fillRect(meterX, meterY, meterWidth, meterHeight);
        
        const rmsHeight = this.audioMetrics.rmsLevel * meterHeight;
        const rmsGradient = this.ctx.createLinearGradient(0, meterY + meterHeight, 0, meterY);
        rmsGradient.addColorStop(0, '#10B981');
        rmsGradient.addColorStop(0.7, '#F59E0B');
        rmsGradient.addColorStop(1, '#EF4444');
        
        this.ctx.fillStyle = rmsGradient;
        this.ctx.fillRect(meterX, meterY + meterHeight - rmsHeight, meterWidth, rmsHeight);

        // Peak level meter
        const peakMeterX = meterX + meterWidth + 4;
        this.ctx.fillStyle = '#374151';
        this.ctx.fillRect(peakMeterX, meterY, meterWidth, meterHeight);
        
        const peakHeight = this.audioMetrics.peakLevel * meterHeight;
        this.ctx.fillStyle = '#EF4444';
        this.ctx.fillRect(peakMeterX, meterY + meterHeight - peakHeight, meterWidth, peakHeight);
    }

    _renderSpeakerIndicators(width, height) {
        if (this.activeSpeakers.size === 0) return;

        const indicatorY = height - 40;
        let indicatorX = 20;
        const indicatorSize = 24;
        const spacing = 8;

        let speakerIndex = 0;
        for (const speakerId of this.activeSpeakers) {
            const color = this._getSpeakerColor(speakerId);
            
            // Speaker indicator circle
            this.ctx.beginPath();
            this.ctx.arc(indicatorX + indicatorSize / 2, indicatorY, indicatorSize / 2, 0, 2 * Math.PI);
            this.ctx.fillStyle = color;
            this.ctx.fill();
            
            // Speaker label
            this.ctx.fillStyle = '#FFFFFF';
            this.ctx.font = '12px Inter, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(
                speakerId.replace('speaker_', 'S'),
                indicatorX + indicatorSize / 2,
                indicatorY + 4
            );
            
            indicatorX += indicatorSize + spacing;
            speakerIndex++;
        }
    }

    _getSpeakerColor(speakerId) {
        if (!this.speakerColors.has(speakerId)) {
            const colors = [
                '#EF4444', '#F59E0B', '#10B981', '#3B82F6',
                '#8B5CF6', '#F97316', '#06B6D4', '#84CC16'
            ];
            const colorIndex = this.speakerColors.size % colors.length;
            this.speakerColors.set(speakerId, colors[colorIndex]);
        }
        return this.speakerColors.get(speakerId);
    }

    _clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.clientWidth, this.canvas.clientHeight);
    }

    _updatePerformanceMetrics() {
        this.frameCount++;
        const now = performance.now();
        
        if (now - this.lastFpsUpdate > 1000) { // Update FPS every second
            this.currentFps = Math.round(this.frameCount * 1000 / (now - this.lastFpsUpdate));
            this.frameCount = 0;
            this.lastFpsUpdate = now;
        }
    }

    // Public API methods
    updateSpeakerActivity(speakers) {
        this.activeSpeakers = new Set(speakers);
        this.onSpeakerChange(speakers);
    }

    addSpeaker(speakerId) {
        this.activeSpeakers.add(speakerId);
        this.onSpeakerChange(Array.from(this.activeSpeakers));
    }

    removeSpeaker(speakerId) {
        this.activeSpeakers.delete(speakerId);
        this.onSpeakerChange(Array.from(this.activeSpeakers));
    }

    getAudioMetrics() {
        return { ...this.audioMetrics };
    }

    getPerformanceMetrics() {
        return {
            fps: this.currentFps,
            isActive: this.isActive,
            activeSpeakers: this.activeSpeakers.size
        };
    }

    resize() {
        this._initializeCanvas();
        this.gradients = this._createGradients();
    }
}

// Export for use in other modules
window.AdvancedAudioVisualizer = AdvancedAudioVisualizer;