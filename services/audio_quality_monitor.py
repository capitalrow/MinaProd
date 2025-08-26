#!/usr/bin/env python3
# 🎧 Production Feature: Real-time Audio Quality Monitoring & Enhancement Pipeline
"""
Enterprise-grade real-time audio quality monitoring and enhancement service.
Implements automatic gain control, quality assessment, and adaptive audio processing.

Addresses: "Real-time audio quality monitoring and enhancement pipeline with AGC" for Fix Pack 4.

Key Features:
- Real-time audio quality assessment and monitoring
- Automatic Gain Control (AGC) with adaptive algorithms
- Dynamic range processing and loudness normalization
- Quality-based audio enhancement pipeline
- Noise gate and compressor/limiter processing
- Performance metrics and quality trending
- Integration with transcription quality optimization
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import time
from scipy import signal
import threading
import queue

logger = logging.getLogger(__name__)

class AudioQualityLevel(Enum):
    """Audio quality classification levels."""
    EXCELLENT = "excellent"    # > 90% quality score
    GOOD = "good"             # 75-90% quality score
    FAIR = "fair"             # 60-75% quality score
    POOR = "poor"             # 40-60% quality score
    UNACCEPTABLE = "unacceptable"  # < 40% quality score

class AGCMode(Enum):
    """Automatic Gain Control modes."""
    ADAPTIVE = "adaptive"      # Adapts to content and environment
    BROADCAST = "broadcast"    # Broadcasting standards compliance
    SPEECH = "speech"          # Optimized for speech clarity
    MUSIC = "music"           # Optimized for music content
    CONFERENCE = "conference"  # Conference call optimization

@dataclass
class AudioQualityMetrics:
    """Comprehensive audio quality metrics."""
    # Overall quality
    overall_score: float = 0.0        # 0-1 overall quality
    quality_level: AudioQualityLevel = AudioQualityLevel.POOR
    
    # Signal characteristics
    peak_level_db: float = -100.0     # Peak level in dB
    rms_level_db: float = -100.0      # RMS level in dB
    dynamic_range_db: float = 0.0     # Dynamic range
    crest_factor: float = 0.0         # Peak to RMS ratio
    
    # Frequency domain
    spectral_balance: float = 0.0     # Frequency balance score
    spectral_clarity: float = 0.0     # Clarity score
    high_frequency_content: float = 0.0  # HF content ratio
    
    # Distortion and artifacts
    clipping_percent: float = 0.0     # Percentage of clipped samples
    noise_floor_db: float = -100.0    # Noise floor estimate
    snr_db: float = 0.0              # Signal-to-noise ratio
    thd_percent: float = 0.0         # Total harmonic distortion
    
    # Speech-specific
    speech_intelligibility: float = 0.0  # Speech clarity score
    vowel_clarity: float = 0.0        # Vowel pronunciation clarity
    consonant_clarity: float = 0.0    # Consonant clarity
    
    # Temporal characteristics
    level_stability: float = 0.0      # Level consistency over time
    micro_interruptions: int = 0      # Count of brief dropouts
    
    # Enhancement recommendations
    needs_gain_adjustment: bool = False
    needs_noise_reduction: bool = False
    needs_eq_adjustment: bool = False
    needs_compression: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall_score': self.overall_score,
            'quality_level': self.quality_level.value,
            'peak_level_db': self.peak_level_db,
            'rms_level_db': self.rms_level_db,
            'dynamic_range_db': self.dynamic_range_db,
            'crest_factor': self.crest_factor,
            'spectral_balance': self.spectral_balance,
            'spectral_clarity': self.spectral_clarity,
            'high_frequency_content': self.high_frequency_content,
            'clipping_percent': self.clipping_percent,
            'noise_floor_db': self.noise_floor_db,
            'snr_db': self.snr_db,
            'thd_percent': self.thd_percent,
            'speech_intelligibility': self.speech_intelligibility,
            'vowel_clarity': self.vowel_clarity,
            'consonant_clarity': self.consonant_clarity,
            'level_stability': self.level_stability,
            'micro_interruptions': self.micro_interruptions,
            'needs_gain_adjustment': self.needs_gain_adjustment,
            'needs_noise_reduction': self.needs_noise_reduction,
            'needs_eq_adjustment': self.needs_eq_adjustment,
            'needs_compression': self.needs_compression
        }

@dataclass
class AGCConfig:
    """Automatic Gain Control configuration."""
    mode: AGCMode = AGCMode.ADAPTIVE
    
    # Target levels (dBFS)
    target_level_db: float = -18.0    # Target RMS level
    max_peak_db: float = -3.0         # Maximum peak level
    noise_gate_db: float = -60.0      # Noise gate threshold
    
    # Response characteristics
    attack_time_ms: float = 10.0      # Attack time in milliseconds
    release_time_ms: float = 100.0    # Release time in milliseconds
    
    # Processing parameters
    max_gain_db: float = 30.0         # Maximum gain boost
    max_attenuation_db: float = -20.0 # Maximum gain reduction
    lookahead_ms: float = 5.0         # Lookahead time for peak limiting
    
    # Adaptive settings
    adaptation_speed: float = 0.1     # Speed of adaptation (0-1)
    environment_aware: bool = True    # Adapt to environmental conditions
    speech_priority: bool = True      # Prioritize speech content
    
    # Quality control
    quality_threshold: float = 0.6    # Minimum quality before intervention
    enhance_speech: bool = True       # Enable speech enhancement
    preserve_dynamics: bool = True    # Maintain some dynamic range

@dataclass
class AudioQualityConfig:
    """Audio quality monitoring configuration."""
    # Monitoring settings
    analysis_window_ms: float = 50.0  # Analysis window size
    overlap_ratio: float = 0.5        # Window overlap ratio
    update_interval_ms: float = 100.0 # Quality update interval
    
    # Quality thresholds
    excellent_threshold: float = 0.9
    good_threshold: float = 0.75
    fair_threshold: float = 0.6
    poor_threshold: float = 0.4
    
    # Detection sensitivity
    clipping_sensitivity: float = 0.95  # Clipping detection threshold
    noise_sensitivity: float = -50.0    # Noise floor sensitivity (dB)
    distortion_sensitivity: float = 2.0 # THD sensitivity (%)
    
    # Enhancement settings
    enable_real_time_enhancement: bool = True
    enable_predictive_enhancement: bool = True
    enhancement_strength: float = 0.7  # 0-1 enhancement strength

class AudioQualityMonitor:
    """
    🎧 Enterprise-grade real-time audio quality monitoring and enhancement service.
    
    Provides comprehensive audio quality assessment, automatic gain control,
    and intelligent enhancement pipeline for optimal transcription quality.
    """
    
    def __init__(self, sample_rate: int = 16000, 
                 quality_config: Optional[AudioQualityConfig] = None,
                 agc_config: Optional[AGCConfig] = None):
        self.sample_rate = sample_rate
        self.quality_config = quality_config or AudioQualityConfig()
        self.agc_config = agc_config or AGCConfig()
        
        # Analysis parameters
        self.frame_size = int(self.sample_rate * self.quality_config.analysis_window_ms / 1000)
        self.hop_size = int(self.frame_size * (1 - self.quality_config.overlap_ratio))
        
        # Quality monitoring
        self.current_metrics = AudioQualityMetrics()
        self.metrics_history = deque(maxlen=1000)  # Store last 1000 measurements
        self.quality_trend = deque(maxlen=50)      # Quality trend analysis
        
        # AGC state
        self.current_gain_db = 0.0
        self.target_gain_db = 0.0
        self.peak_envelope = 0.0
        self.rms_envelope = 0.0
        self.gain_reduction_db = 0.0
        
        # Enhancement pipeline
        self.noise_gate_active = False
        self.compressor_active = False
        self.limiter_active = False
        
        # Processing buffers
        self.input_buffer = deque(maxlen=self.frame_size * 4)
        self.output_buffer = deque(maxlen=self.frame_size * 2)
        self.lookahead_buffer = deque(maxlen=int(self.agc_config.lookahead_ms * self.sample_rate / 1000))
        
        # Analysis filters and processors
        self._initialize_processors()
        
        # Performance tracking
        self.processing_stats = {
            'total_frames': 0,
            'enhanced_frames': 0,
            'quality_improvements': 0,
            'agc_adjustments': 0,
            'clipping_prevented': 0,
            'processing_time_ms': deque(maxlen=100)
        }
        
        # Threading for real-time processing
        self.processing_queue = queue.Queue(maxsize=100)
        self.enhancement_thread = None
        self.running = False
        
        logger.info(f"🎧 Audio Quality Monitor initialized - Mode: {self.agc_config.mode.value}")
    
    def _initialize_processors(self):
        """Initialize audio processing components."""
        # Frequency analysis
        self.fft_window = np.hanning(self.frame_size)
        
        # Bandpass filters for speech analysis
        nyquist = self.sample_rate / 2
        
        # Speech clarity filters
        self.vowel_filter = signal.butter(4, [300/nyquist, 3400/nyquist], btype='band')
        self.consonant_filter = signal.butter(4, [2000/nyquist, 8000/nyquist], btype='band')
        
        # Noise reduction filter
        self.high_pass_filter = signal.butter(2, 80/nyquist, btype='high')
        
        # AGC envelope followers
        self.attack_coeff = np.exp(-1 / (self.agc_config.attack_time_ms * self.sample_rate / 1000))
        self.release_coeff = np.exp(-1 / (self.agc_config.release_time_ms * self.sample_rate / 1000))
    
    def start_real_time_processing(self):
        """Start real-time audio enhancement processing."""
        if not self.running:
            self.running = True
            self.enhancement_thread = threading.Thread(target=self._enhancement_worker)
            self.enhancement_thread.start()
            logger.info("🎧 Real-time audio enhancement started")
    
    def stop_real_time_processing(self):
        """Stop real-time processing."""
        if self.running:
            self.running = False
            if self.enhancement_thread:
                self.enhancement_thread.join()
            logger.info("🎧 Real-time audio enhancement stopped")
    
    def _enhancement_worker(self):
        """Background worker for real-time enhancement."""
        while self.running:
            try:
                # Get audio chunk from queue (with timeout)
                audio_chunk, timestamp = self.processing_queue.get(timeout=0.1)
                
                # Process the chunk
                enhanced_chunk = self.process_audio_chunk(audio_chunk, timestamp)
                
                # Mark task done
                self.processing_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error in enhancement worker: {e}")
    
    def analyze_quality(self, audio_data: np.ndarray) -> AudioQualityMetrics:
        """
        🎧 Comprehensive audio quality analysis.
        
        Args:
            audio_data: Audio samples as numpy array
            
        Returns:
            Detailed audio quality metrics
        """
        start_time = time.time()
        
        if len(audio_data) == 0:
            return AudioQualityMetrics()
        
        metrics = AudioQualityMetrics()
        
        try:
            # === LEVEL ANALYSIS ===
            # Peak and RMS levels
            peak_level = np.max(np.abs(audio_data))
            rms_level = np.sqrt(np.mean(audio_data ** 2))
            
            if peak_level > 0:
                metrics.peak_level_db = 20 * np.log10(peak_level)
            if rms_level > 0:
                metrics.rms_level_db = 20 * np.log10(rms_level)
            
            # Dynamic range and crest factor
            if peak_level > 0 and rms_level > 0:
                metrics.crest_factor = peak_level / rms_level
                metrics.dynamic_range_db = metrics.peak_level_db - metrics.rms_level_db
            
            # === DISTORTION ANALYSIS ===
            # Clipping detection
            clipped_samples = np.sum(np.abs(audio_data) > self.quality_config.clipping_sensitivity)
            metrics.clipping_percent = (clipped_samples / len(audio_data)) * 100
            
            # === FREQUENCY DOMAIN ANALYSIS ===
            if len(audio_data) >= 64:  # Minimum for meaningful FFT
                windowed = audio_data * np.hanning(len(audio_data))
                fft = np.fft.rfft(windowed)
                magnitude_spectrum = np.abs(fft)
                power_spectrum = magnitude_spectrum ** 2
                frequencies = np.fft.rfftfreq(len(audio_data), 1/self.sample_rate)
                
                # Spectral balance (energy distribution)
                metrics.spectral_balance = self._calculate_spectral_balance(power_spectrum, frequencies)
                
                # Spectral clarity (sharpness of peaks)
                metrics.spectral_clarity = self._calculate_spectral_clarity(magnitude_spectrum)
                
                # High frequency content
                high_freq_mask = frequencies > 4000
                if np.any(high_freq_mask):
                    hf_energy = np.sum(power_spectrum[high_freq_mask])
                    total_energy = np.sum(power_spectrum)
                    metrics.high_frequency_content = hf_energy / (total_energy + 1e-10)
            
            # === NOISE ANALYSIS ===
            # Noise floor estimation (using lower percentiles)
            sorted_abs = np.sort(np.abs(audio_data))
            noise_samples = sorted_abs[:len(sorted_abs)//10]  # Bottom 10%
            if len(noise_samples) > 0:
                noise_floor = np.mean(noise_samples)
                if noise_floor > 0:
                    metrics.noise_floor_db = 20 * np.log10(noise_floor)
                
                # SNR calculation
                if rms_level > 0 and noise_floor > 0:
                    metrics.snr_db = 20 * np.log10(rms_level / noise_floor)
            
            # === SPEECH ANALYSIS ===
            if len(audio_data) >= self.sample_rate // 10:  # At least 100ms of audio
                metrics.speech_intelligibility = self._analyze_speech_intelligibility(audio_data)
                metrics.vowel_clarity = self._analyze_vowel_clarity(audio_data)
                metrics.consonant_clarity = self._analyze_consonant_clarity(audio_data)
            
            # === TEMPORAL ANALYSIS ===
            if len(self.metrics_history) > 10:
                metrics.level_stability = self._calculate_level_stability()
                metrics.micro_interruptions = self._detect_micro_interruptions()
            
            # === OVERALL QUALITY SCORING ===
            metrics.overall_score = self._calculate_overall_quality_score(metrics)
            metrics.quality_level = self._determine_quality_level(metrics.overall_score)
            
            # === ENHANCEMENT RECOMMENDATIONS ===
            self._generate_enhancement_recommendations(metrics)
            
            # Store metrics
            self.current_metrics = metrics
            self.metrics_history.append(metrics)
            self.quality_trend.append(metrics.overall_score)
            
            # Update processing stats
            processing_time = (time.time() - start_time) * 1000
            self.processing_stats['processing_time_ms'].append(processing_time)
            self.processing_stats['total_frames'] += 1
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error analyzing audio quality: {e}")
            return AudioQualityMetrics()
    
    def _calculate_spectral_balance(self, power_spectrum: np.ndarray, frequencies: np.ndarray) -> float:
        """Calculate spectral balance score (0-1)."""
        # Define frequency bands for analysis
        bands = [
            (80, 250),     # Bass
            (250, 500),    # Low-mid
            (500, 2000),   # Mid (speech fundamentals)
            (2000, 4000),  # High-mid (speech clarity)
            (4000, 8000)   # High (consonants)
        ]
        
        band_energies = []
        total_energy = np.sum(power_spectrum)
        
        for low_freq, high_freq in bands:
            band_mask = (frequencies >= low_freq) & (frequencies <= high_freq)
            if np.any(band_mask):
                band_energy = np.sum(power_spectrum[band_mask])
                band_energies.append(band_energy / (total_energy + 1e-10))
            else:
                band_energies.append(0.0)
        
        # Good spectral balance has reasonable energy in speech-critical bands
        # Emphasize mid frequencies (speech fundamentals and clarity)
        speech_energy = band_energies[2] + band_energies[3]  # 500-4000 Hz
        
        # Penalize excessive low or high frequency content
        bass_penalty = max(0, band_energies[0] - 0.2)  # Too much bass
        high_penalty = max(0, band_energies[4] - 0.15)  # Too much high freq
        
        balance_score = speech_energy - bass_penalty - high_penalty
        return max(0.0, min(1.0, balance_score * 1.5))  # Scale and clip
    
    def _calculate_spectral_clarity(self, magnitude_spectrum: np.ndarray) -> float:
        """Calculate spectral clarity based on peak definition."""
        if len(magnitude_spectrum) < 10:
            return 0.0
        
        # Find peaks in spectrum
        peaks = signal.find_peaks(magnitude_spectrum, height=np.max(magnitude_spectrum) * 0.1)[0]
        
        if len(peaks) < 2:
            return 0.2  # Very poor clarity
        
        # Calculate peak sharpness (higher peaks relative to surroundings = better clarity)
        peak_heights = magnitude_spectrum[peaks]
        surrounding_avg = []
        
        for peak_idx in peaks:
            # Average of surrounding samples
            start = max(0, peak_idx - 5)
            end = min(len(magnitude_spectrum), peak_idx + 6)
            surrounding = np.concatenate([
                magnitude_spectrum[start:peak_idx],
                magnitude_spectrum[peak_idx+1:end]
            ])
            if len(surrounding) > 0:
                surrounding_avg.append(np.mean(surrounding))
        
        if len(surrounding_avg) == 0:
            return 0.3
        
        # Peak-to-average ratio indicates clarity
        peak_to_avg_ratios = peak_heights / (np.array(surrounding_avg) + 1e-10)
        avg_clarity = np.mean(np.log(peak_to_avg_ratios + 1)) / 3  # Normalize
        
        return max(0.0, min(1.0, avg_clarity))
    
    def _analyze_speech_intelligibility(self, audio_data: np.ndarray) -> float:
        """Analyze speech intelligibility score."""
        try:
            # Apply speech frequency weighting
            speech_weighted = signal.lfilter(*self.vowel_filter, audio_data)
            
            # Energy in speech-critical frequencies
            speech_energy = np.sum(speech_weighted ** 2)
            total_energy = np.sum(audio_data ** 2)
            
            speech_ratio = speech_energy / (total_energy + 1e-10)
            
            # Modulation analysis (speech has characteristic modulation patterns)
            envelope = np.abs(signal.hilbert(speech_weighted))
            envelope_smooth = signal.medfilt(envelope, kernel_size=5)
            
            # Speech modulation typically 2-8 Hz
            if len(envelope_smooth) > self.sample_rate:
                modulation_fft = np.fft.rfft(envelope_smooth - np.mean(envelope_smooth))
                mod_freqs = np.fft.rfftfreq(len(envelope_smooth), 1/self.sample_rate)
                
                speech_mod_mask = (mod_freqs >= 2) & (mod_freqs <= 8)
                if np.any(speech_mod_mask):
                    speech_mod_energy = np.sum(np.abs(modulation_fft[speech_mod_mask]))
                    total_mod_energy = np.sum(np.abs(modulation_fft))
                    modulation_score = speech_mod_energy / (total_mod_energy + 1e-10)
                else:
                    modulation_score = 0.0
            else:
                modulation_score = 0.0
            
            # Combine metrics
            intelligibility = (speech_ratio * 0.7 + modulation_score * 0.3)
            return max(0.0, min(1.0, intelligibility * 1.5))  # Scale up for better dynamic range
            
        except Exception as e:
            logger.error(f"❌ Error analyzing speech intelligibility: {e}")
            return 0.0
    
    def _analyze_vowel_clarity(self, audio_data: np.ndarray) -> float:
        """Analyze vowel clarity."""
        try:
            # Vowels have strong formant structure in 300-3400 Hz range
            vowel_filtered = signal.lfilter(*self.vowel_filter, audio_data)
            
            # Formant analysis using spectral peaks
            windowed = vowel_filtered * np.hanning(len(vowel_filtered))
            fft = np.fft.rfft(windowed)
            magnitude = np.abs(fft)
            frequencies = np.fft.rfftfreq(len(vowel_filtered), 1/self.sample_rate)
            
            # Find formant peaks
            peaks = signal.find_peaks(magnitude, height=np.max(magnitude) * 0.2)[0]
            
            if len(peaks) >= 2:
                # Check for typical F1 and F2 formant structure
                peak_freqs = frequencies[peaks]
                
                # F1 typically 200-1000 Hz, F2 typically 800-2500 Hz
                f1_candidates = peak_freqs[(peak_freqs >= 200) & (peak_freqs <= 1000)]
                f2_candidates = peak_freqs[(peak_freqs >= 800) & (peak_freqs <= 2500)]
                
                if len(f1_candidates) > 0 and len(f2_candidates) > 0:
                    clarity_score = min(1.0, (len(f1_candidates) + len(f2_candidates)) / 4)
                else:
                    clarity_score = 0.3
            else:
                clarity_score = 0.1
            
            return clarity_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing vowel clarity: {e}")
            return 0.0
    
    def _analyze_consonant_clarity(self, audio_data: np.ndarray) -> float:
        """Analyze consonant clarity."""
        try:
            # Consonants have significant high-frequency content
            consonant_filtered = signal.lfilter(*self.consonant_filter, audio_data)
            
            # High-frequency energy indicates good consonant definition
            hf_energy = np.sum(consonant_filtered ** 2)
            total_energy = np.sum(audio_data ** 2)
            
            consonant_ratio = hf_energy / (total_energy + 1e-10)
            
            # Consonants also have rapid amplitude changes (high zero-crossing rate)
            zero_crossings = np.sum(np.diff(np.sign(consonant_filtered)) != 0)
            zcr = zero_crossings / len(consonant_filtered)
            
            # Normalize ZCR (typical speech has ZCR around 0.1-0.3)
            zcr_score = min(1.0, zcr / 0.2) if zcr > 0 else 0.0
            
            # Combine energy ratio and ZCR
            clarity = (consonant_ratio * 3 + zcr_score) / 2  # Weight energy more
            return max(0.0, min(1.0, clarity))
            
        except Exception as e:
            logger.error(f"❌ Error analyzing consonant clarity: {e}")
            return 0.0
    
    def _calculate_level_stability(self) -> float:
        """Calculate level stability over recent history."""
        if len(self.metrics_history) < 10:
            return 0.0
        
        recent_levels = [m.rms_level_db for m in list(self.metrics_history)[-20:]]
        level_variance = np.var(recent_levels)
        
        # Good stability has low variance (less than 6 dB variance is good)
        stability_score = max(0.0, 1.0 - level_variance / 36)  # Normalize by 6^2
        return min(1.0, stability_score)
    
    def _detect_micro_interruptions(self) -> int:
        """Detect micro-interruptions in audio."""
        if len(self.metrics_history) < 5:
            return 0
        
        # Look for sudden drops in energy
        recent_levels = [m.rms_level_db for m in list(self.metrics_history)[-10:]]
        interruptions = 0
        
        for i in range(1, len(recent_levels) - 1):
            if (recent_levels[i] < recent_levels[i-1] - 10 and  # 10dB drop
                recent_levels[i] < recent_levels[i+1] - 10):    # followed by recovery
                interruptions += 1
        
        return interruptions
    
    def _calculate_overall_quality_score(self, metrics: AudioQualityMetrics) -> float:
        """Calculate comprehensive quality score."""
        score_components = []
        
        # Level quality (optimal around -18dB RMS)
        if -25 <= metrics.rms_level_db <= -10:
            level_score = 1.0
        elif -35 <= metrics.rms_level_db <= -5:
            level_score = 0.7
        else:
            level_score = 0.3
        score_components.append(('level', level_score, 0.15))
        
        # SNR quality
        if metrics.snr_db > 25:
            snr_score = 1.0
        elif metrics.snr_db > 15:
            snr_score = 0.8
        elif metrics.snr_db > 10:
            snr_score = 0.6
        elif metrics.snr_db > 5:
            snr_score = 0.4
        else:
            snr_score = 0.2
        score_components.append(('snr', snr_score, 0.25))
        
        # Clipping penalty
        clipping_score = max(0.0, 1.0 - metrics.clipping_percent / 5.0)  # 5% clipping = 0 score
        score_components.append(('clipping', clipping_score, 0.2))
        
        # Spectral quality
        spectral_score = (metrics.spectral_balance + metrics.spectral_clarity) / 2
        score_components.append(('spectral', spectral_score, 0.15))
        
        # Speech quality
        speech_score = (metrics.speech_intelligibility + 
                       metrics.vowel_clarity + 
                       metrics.consonant_clarity) / 3
        score_components.append(('speech', speech_score, 0.2))
        
        # Stability
        score_components.append(('stability', metrics.level_stability, 0.05))
        
        # Weighted average
        weighted_sum = sum(score * weight for _, score, weight in score_components)
        total_weight = sum(weight for _, _, weight in score_components)
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        return max(0.0, min(1.0, overall_score))
    
    def _determine_quality_level(self, score: float) -> AudioQualityLevel:
        """Determine quality level from score."""
        if score >= self.quality_config.excellent_threshold:
            return AudioQualityLevel.EXCELLENT
        elif score >= self.quality_config.good_threshold:
            return AudioQualityLevel.GOOD
        elif score >= self.quality_config.fair_threshold:
            return AudioQualityLevel.FAIR
        elif score >= self.quality_config.poor_threshold:
            return AudioQualityLevel.POOR
        else:
            return AudioQualityLevel.UNACCEPTABLE
    
    def _generate_enhancement_recommendations(self, metrics: AudioQualityMetrics):
        """Generate enhancement recommendations based on quality analysis."""
        # Gain adjustment needed?
        if metrics.rms_level_db < -30 or metrics.rms_level_db > -10:
            metrics.needs_gain_adjustment = True
        
        # Noise reduction needed?
        if metrics.snr_db < 15 or metrics.noise_floor_db > -50:
            metrics.needs_noise_reduction = True
        
        # EQ adjustment needed?
        if metrics.spectral_balance < 0.6:
            metrics.needs_eq_adjustment = True
        
        # Compression needed?
        if metrics.dynamic_range_db > 30 or metrics.crest_factor > 10:
            metrics.needs_compression = True
    
    def process_audio_chunk(self, audio_data: np.ndarray, timestamp: float = None) -> np.ndarray:
        """
        🎧 Process audio chunk with quality monitoring and enhancement.
        
        Args:
            audio_data: Input audio samples
            timestamp: Optional timestamp
            
        Returns:
            Enhanced audio samples
        """
        if timestamp is None:
            timestamp = time.time()
        
        try:
            if len(audio_data) == 0:
                return audio_data
            
            # Analyze quality first
            metrics = self.analyze_quality(audio_data)
            
            # Apply enhancements if enabled and needed
            enhanced_audio = audio_data.copy()
            
            if self.quality_config.enable_real_time_enhancement:
                # Apply AGC
                enhanced_audio = self._apply_agc(enhanced_audio, metrics)
                
                # Apply noise gate
                if metrics.needs_noise_reduction:
                    enhanced_audio = self._apply_noise_gate(enhanced_audio)
                
                # Apply compression if needed
                if metrics.needs_compression:
                    enhanced_audio = self._apply_compression(enhanced_audio)
                
                # Apply limiting to prevent clipping
                enhanced_audio = self._apply_limiter(enhanced_audio)
                
                # Track enhancement statistics
                if not np.array_equal(audio_data, enhanced_audio):
                    self.processing_stats['enhanced_frames'] += 1
                    if metrics.overall_score < 0.7:  # Was poor quality
                        self.processing_stats['quality_improvements'] += 1
            
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"❌ Error processing audio chunk: {e}")
            return audio_data
    
    def _apply_agc(self, audio_data: np.ndarray, metrics: AudioQualityMetrics) -> np.ndarray:
        """Apply Automatic Gain Control."""
        if len(audio_data) == 0:
            return audio_data
        
        # Calculate required gain adjustment
        current_level_db = metrics.rms_level_db
        target_level_db = self.agc_config.target_level_db
        
        if current_level_db > -100:  # Valid measurement
            gain_needed_db = target_level_db - current_level_db
            
            # Limit gain change rate and range
            max_change_db = 3.0  # Max 3dB change per frame
            gain_needed_db = np.clip(gain_needed_db, -max_change_db, max_change_db)
            gain_needed_db = np.clip(gain_needed_db, 
                                   self.agc_config.max_attenuation_db, 
                                   self.agc_config.max_gain_db)
            
            # Smooth gain changes
            adaptation = self.agc_config.adaptation_speed
            self.target_gain_db = (adaptation * gain_needed_db + 
                                 (1 - adaptation) * self.target_gain_db)
            
            # Apply gain smoothing
            if abs(self.target_gain_db - self.current_gain_db) > 0.1:
                # Use attack/release based on gain direction
                if self.target_gain_db > self.current_gain_db:  # Increasing gain
                    coeff = self.release_coeff
                else:  # Decreasing gain (attack)
                    coeff = self.attack_coeff
                
                self.current_gain_db = (coeff * self.current_gain_db + 
                                      (1 - coeff) * self.target_gain_db)
            
            # Apply gain
            if abs(self.current_gain_db) > 0.1:  # Only if significant gain change
                linear_gain = 10 ** (self.current_gain_db / 20)
                enhanced_audio = audio_data * linear_gain
                
                # Prevent clipping after gain application
                peak = np.max(np.abs(enhanced_audio))
                if peak > 0.95:  # Close to clipping
                    enhanced_audio = enhanced_audio * (0.95 / peak)
                    self.processing_stats['clipping_prevented'] += 1
                
                self.processing_stats['agc_adjustments'] += 1
                return enhanced_audio
        
        return audio_data
    
    def _apply_noise_gate(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply noise gate to reduce background noise."""
        gate_threshold_linear = 10 ** (self.agc_config.noise_gate_db / 20)
        
        # Simple gate: attenuate signals below threshold
        gate_mask = np.abs(audio_data) < gate_threshold_linear
        gated_audio = audio_data.copy()
        gated_audio[gate_mask] *= 0.1  # 20dB attenuation
        
        self.noise_gate_active = np.any(gate_mask)
        return gated_audio
    
    def _apply_compression(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply dynamic range compression."""
        # Simple RMS-based compressor
        frame_size = min(256, len(audio_data))
        compressed_audio = audio_data.copy()
        
        for i in range(0, len(audio_data), frame_size):
            end_idx = min(i + frame_size, len(audio_data))
            frame = audio_data[i:end_idx]
            
            rms = np.sqrt(np.mean(frame ** 2))
            
            if rms > 0:
                # Compression ratio 3:1 above -20dB
                threshold_linear = 10 ** (-20 / 20)
                
                if rms > threshold_linear:
                    # Calculate compression
                    ratio = 3.0
                    over_threshold_db = 20 * np.log10(rms / threshold_linear)
                    reduction_db = over_threshold_db * (1 - 1/ratio)
                    gain_reduction = 10 ** (-reduction_db / 20)
                    
                    compressed_audio[i:end_idx] = frame * gain_reduction
                    self.compressor_active = True
        
        return compressed_audio
    
    def _apply_limiter(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply peak limiter to prevent clipping."""
        max_peak_linear = 10 ** (self.agc_config.max_peak_db / 20)
        
        peak = np.max(np.abs(audio_data))
        if peak > max_peak_linear:
            gain_reduction = max_peak_linear / peak
            limited_audio = audio_data * gain_reduction
            self.limiter_active = True
            return limited_audio
        
        self.limiter_active = False
        return audio_data
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Get comprehensive quality report."""
        report = {
            'current_metrics': self.current_metrics.to_dict(),
            'agc_status': {
                'mode': self.agc_config.mode.value,
                'current_gain_db': self.current_gain_db,
                'target_gain_db': self.target_gain_db,
                'noise_gate_active': self.noise_gate_active,
                'compressor_active': self.compressor_active,
                'limiter_active': self.limiter_active
            },
            'processing_statistics': {
                **self.processing_stats,
                'average_processing_time_ms': np.mean(list(self.processing_stats['processing_time_ms'])) if self.processing_stats['processing_time_ms'] else 0,
                'enhancement_rate': self.processing_stats['enhanced_frames'] / max(1, self.processing_stats['total_frames'])
            },
            'quality_trend': {
                'current_quality': self.current_metrics.quality_level.value,
                'trend_direction': self._calculate_quality_trend(),
                'stability_score': np.std(list(self.quality_trend)) if len(self.quality_trend) > 5 else 0
            }
        }
        
        return report
    
    def _calculate_quality_trend(self) -> str:
        """Calculate quality trend direction."""
        if len(self.quality_trend) < 10:
            return 'insufficient_data'
        
        recent_quality = list(self.quality_trend)
        first_half = np.mean(recent_quality[:len(recent_quality)//2])
        second_half = np.mean(recent_quality[len(recent_quality)//2:])
        
        diff = second_half - first_half
        
        if diff > 0.05:
            return 'improving'
        elif diff < -0.05:
            return 'degrading'
        else:
            return 'stable'

# Global audio quality monitor instance
_quality_monitor: Optional[AudioQualityMonitor] = None

def get_audio_quality_monitor() -> Optional[AudioQualityMonitor]:
    """Get the global audio quality monitor."""
    return _quality_monitor

def initialize_audio_quality_monitor(sample_rate: int = 16000,
                                   quality_config: Optional[AudioQualityConfig] = None,
                                   agc_config: Optional[AGCConfig] = None) -> AudioQualityMonitor:
    """Initialize the global audio quality monitor."""
    global _quality_monitor
    _quality_monitor = AudioQualityMonitor(sample_rate, quality_config, agc_config)
    return _quality_monitor