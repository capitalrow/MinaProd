"""
Adaptive Quality System - Google Recorder Level Quality Management
Real-time quality adaptation based on audio conditions, performance metrics, and user requirements.
Implements intelligent quality scaling and dynamic parameter adjustment.
"""

import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import threading

logger = logging.getLogger(__name__)

class QualityMode(Enum):
    """Quality operation modes."""
    ECONOMY = "economy"          # Optimized for speed
    BALANCED = "balanced"        # Balance of quality and performance
    HIGH_QUALITY = "high_quality"  # Maximum quality
    ADAPTIVE = "adaptive"        # Dynamic adaptation

@dataclass
class QualityProfile:
    """Quality configuration profile."""
    mode: QualityMode
    audio_enhancement_level: float  # 0.0 to 1.0
    vad_sensitivity: float         # 0.0 to 1.0
    context_window_size: int       # Number of chunks for context
    interim_update_frequency: float # Updates per second
    latency_priority: float        # 0.0 = quality priority, 1.0 = latency priority
    noise_reduction_strength: float # 0.0 to 1.0
    spectral_enhancement: bool
    adaptive_gain_control: bool

@dataclass
class EnvironmentalConditions:
    """Current environmental and performance conditions."""
    noise_level: float
    speech_clarity: float
    background_complexity: float
    device_performance: float
    network_quality: float
    user_movement: float
    audio_quality_score: float

@dataclass
class QualityMetrics:
    """Quality performance metrics."""
    current_latency_ms: float
    confidence_score: float
    word_error_rate: float
    user_satisfaction_score: float
    processing_efficiency: float
    battery_usage: float
    network_usage: float

class AdaptiveQualitySystem:
    """
    🎛️ Google Recorder-level adaptive quality management.
    
    Implements intelligent quality adaptation based on:
    - Environmental audio conditions (noise, clarity, complexity)
    - Device performance and resource constraints
    - Network conditions and bandwidth availability
    - User preferences and satisfaction metrics
    - Real-time performance feedback
    """
    
    def __init__(self, initial_mode: QualityMode = QualityMode.ADAPTIVE):
        self.current_mode = initial_mode
        
        # Quality profiles for different modes
        self.quality_profiles = {
            QualityMode.ECONOMY: QualityProfile(
                mode=QualityMode.ECONOMY,
                audio_enhancement_level=0.3,
                vad_sensitivity=0.4,
                context_window_size=2,
                interim_update_frequency=2.0,
                latency_priority=0.8,
                noise_reduction_strength=0.3,
                spectral_enhancement=False,
                adaptive_gain_control=True
            ),
            QualityMode.BALANCED: QualityProfile(
                mode=QualityMode.BALANCED,
                audio_enhancement_level=0.6,
                vad_sensitivity=0.6,
                context_window_size=3,
                interim_update_frequency=4.0,
                latency_priority=0.5,
                noise_reduction_strength=0.6,
                spectral_enhancement=True,
                adaptive_gain_control=True
            ),
            QualityMode.HIGH_QUALITY: QualityProfile(
                mode=QualityMode.HIGH_QUALITY,
                audio_enhancement_level=1.0,
                vad_sensitivity=0.8,
                context_window_size=5,
                interim_update_frequency=8.0,
                latency_priority=0.2,
                noise_reduction_strength=1.0,
                spectral_enhancement=True,
                adaptive_gain_control=True
            ),
            QualityMode.ADAPTIVE: QualityProfile(
                mode=QualityMode.ADAPTIVE,
                audio_enhancement_level=0.7,
                vad_sensitivity=0.6,
                context_window_size=3,
                interim_update_frequency=5.0,
                latency_priority=0.4,
                noise_reduction_strength=0.7,
                spectral_enhancement=True,
                adaptive_gain_control=True
            )
        }
        
        # Current state
        self.current_profile = self.quality_profiles[initial_mode]
        self.environmental_conditions = EnvironmentalConditions(
            noise_level=0.1, speech_clarity=0.8, background_complexity=0.2,
            device_performance=0.8, network_quality=0.9, user_movement=0.1,
            audio_quality_score=0.8
        )
        
        # Adaptation state
        self.adaptation_history = deque(maxlen=100)
        self.quality_metrics_history = deque(maxlen=50)
        self.environmental_history = deque(maxlen=30)
        
        # Adaptation parameters
        self.adaptation_sensitivity = 0.1
        self.stability_threshold = 0.15
        self.min_adaptation_interval = 2.0  # seconds
        self.last_adaptation_time = 0.0
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        logger.info(f"🎛️ Adaptive Quality System initialized in {initial_mode.value} mode")
    
    def start_monitoring(self):
        """🚀 Start continuous quality monitoring and adaptation."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitor_and_adapt_continuously,
                daemon=True
            )
            self.monitoring_thread.start()
            logger.info("🚀 Quality monitoring started")
    
    def stop_monitoring(self):
        """⏹️ Stop quality monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=1.0)
        logger.info("⏹️ Quality monitoring stopped")
    
    def update_environmental_conditions(self, conditions: Dict[str, float]):
        """🌍 Update environmental conditions for adaptation."""
        try:
            # Update environmental conditions
            for key, value in conditions.items():
                if hasattr(self.environmental_conditions, key):
                    setattr(self.environmental_conditions, key, value)
            
            # Add to history
            self.environmental_history.append(self.environmental_conditions)
            
            # Trigger adaptation if in adaptive mode
            if self.current_mode == QualityMode.ADAPTIVE:
                self._trigger_adaptive_optimization()
            
        except Exception as e:
            logger.warning(f"⚠️ Environmental conditions update failed: {e}")
    
    def update_quality_metrics(self, metrics: Dict[str, float]):
        """📊 Update quality performance metrics."""
        try:
            quality_metrics = QualityMetrics(
                current_latency_ms=metrics.get('latency_ms', 0.0),
                confidence_score=metrics.get('confidence', 0.0),
                word_error_rate=metrics.get('wer', 0.0),
                user_satisfaction_score=metrics.get('user_satisfaction', 0.8),
                processing_efficiency=metrics.get('efficiency', 0.8),
                battery_usage=metrics.get('battery_usage', 0.5),
                network_usage=metrics.get('network_usage', 0.5)
            )
            
            self.quality_metrics_history.append(quality_metrics)
            
            # Trigger adaptation if needed
            if self.current_mode == QualityMode.ADAPTIVE:
                self._trigger_adaptive_optimization()
            
        except Exception as e:
            logger.warning(f"⚠️ Quality metrics update failed: {e}")
    
    def _trigger_adaptive_optimization(self):
        """🎯 Trigger adaptive quality optimization."""
        try:
            current_time = time.time()
            
            # Check minimum adaptation interval
            if current_time - self.last_adaptation_time < self.min_adaptation_interval:
                return
            
            # Analyze current performance and conditions
            optimization_needed = self._analyze_optimization_need()
            
            if optimization_needed['should_adapt']:
                new_profile = self._calculate_optimal_profile(optimization_needed)
                
                if self._should_apply_profile_change(new_profile):
                    self._apply_profile_change(new_profile, optimization_needed['reason'])
                    self.last_adaptation_time = current_time
            
        except Exception as e:
            logger.warning(f"⚠️ Adaptive optimization failed: {e}")
    
    def _analyze_optimization_need(self) -> Dict[str, Any]:
        """🔍 Analyze if optimization is needed."""
        try:
            if not self.quality_metrics_history or not self.environmental_history:
                return {'should_adapt': False, 'reason': 'insufficient_data'}
            
            recent_metrics = list(self.quality_metrics_history)[-5:]  # Last 5 measurements
            recent_environment = list(self.environmental_history)[-3:]  # Last 3 measurements
            
            # Check various adaptation triggers
            adaptation_triggers = []
            
            # 1. Latency performance
            avg_latency = np.mean([m.current_latency_ms for m in recent_metrics])
            if avg_latency > 500:  # Above 500ms
                adaptation_triggers.append({
                    'type': 'high_latency',
                    'severity': min(1.0, (avg_latency - 500) / 500),
                    'action': 'reduce_quality_for_speed'
                })
            elif avg_latency < 200:  # Below 200ms - room for quality improvement
                adaptation_triggers.append({
                    'type': 'low_latency',
                    'severity': (200 - avg_latency) / 200,
                    'action': 'increase_quality'
                })
            
            # 2. Confidence degradation
            avg_confidence = np.mean([m.confidence_score for m in recent_metrics])
            if avg_confidence < 0.7:
                adaptation_triggers.append({
                    'type': 'low_confidence',
                    'severity': (0.7 - avg_confidence) / 0.7,
                    'action': 'increase_audio_enhancement'
                })
            
            # 3. Environmental noise increase
            avg_noise = np.mean([e.noise_level for e in recent_environment])
            if avg_noise > 0.3:
                adaptation_triggers.append({
                    'type': 'high_noise',
                    'severity': min(1.0, (avg_noise - 0.3) / 0.7),
                    'action': 'increase_noise_reduction'
                })
            
            # 4. Device performance degradation
            avg_device_perf = np.mean([e.device_performance for e in recent_environment])
            if avg_device_perf < 0.5:
                adaptation_triggers.append({
                    'type': 'poor_device_performance',
                    'severity': (0.5 - avg_device_perf) / 0.5,
                    'action': 'reduce_processing_load'
                })
            
            # 5. Network quality issues
            avg_network = np.mean([e.network_quality for e in recent_environment])
            if avg_network < 0.6:
                adaptation_triggers.append({
                    'type': 'poor_network',
                    'severity': (0.6 - avg_network) / 0.6,
                    'action': 'reduce_data_usage'
                })
            
            # Determine if adaptation is needed
            if adaptation_triggers:
                # Find the most severe trigger
                primary_trigger = max(adaptation_triggers, key=lambda x: x['severity'])
                
                return {
                    'should_adapt': primary_trigger['severity'] > self.stability_threshold,
                    'reason': primary_trigger['type'],
                    'action': primary_trigger['action'],
                    'severity': primary_trigger['severity'],
                    'all_triggers': adaptation_triggers
                }
            
            return {'should_adapt': False, 'reason': 'conditions_stable'}
            
        except Exception as e:
            logger.warning(f"⚠️ Optimization analysis failed: {e}")
            return {'should_adapt': False, 'reason': 'analysis_error'}
    
    def _calculate_optimal_profile(self, optimization_info: Dict[str, Any]) -> QualityProfile:
        """🧮 Calculate optimal quality profile based on current conditions."""
        try:
            # Start with current profile
            new_profile = QualityProfile(**vars(self.current_profile))
            
            action = optimization_info.get('action', '')
            severity = optimization_info.get('severity', 0.0)
            
            # Apply adaptations based on the primary issue
            if action == 'reduce_quality_for_speed':
                # Reduce quality settings to improve speed
                new_profile.audio_enhancement_level *= (1 - severity * 0.3)
                new_profile.context_window_size = max(1, int(new_profile.context_window_size * (1 - severity * 0.4)))
                new_profile.interim_update_frequency *= (1 - severity * 0.2)
                new_profile.latency_priority = min(1.0, new_profile.latency_priority + severity * 0.3)
                new_profile.spectral_enhancement = severity < 0.5
                
            elif action == 'increase_quality':
                # Increase quality settings when performance allows
                new_profile.audio_enhancement_level = min(1.0, new_profile.audio_enhancement_level + severity * 0.2)
                new_profile.context_window_size = min(5, new_profile.context_window_size + 1)
                new_profile.interim_update_frequency = min(10.0, new_profile.interim_update_frequency + severity * 2.0)
                new_profile.latency_priority = max(0.0, new_profile.latency_priority - severity * 0.2)
                new_profile.spectral_enhancement = True
                
            elif action == 'increase_audio_enhancement':
                # Focus on audio quality improvements
                new_profile.audio_enhancement_level = min(1.0, new_profile.audio_enhancement_level + severity * 0.4)
                new_profile.noise_reduction_strength = min(1.0, new_profile.noise_reduction_strength + severity * 0.3)
                new_profile.vad_sensitivity = min(1.0, new_profile.vad_sensitivity + severity * 0.2)
                new_profile.spectral_enhancement = True
                new_profile.adaptive_gain_control = True
                
            elif action == 'increase_noise_reduction':
                # Focus on noise handling
                new_profile.noise_reduction_strength = min(1.0, new_profile.noise_reduction_strength + severity * 0.5)
                new_profile.audio_enhancement_level = min(1.0, new_profile.audio_enhancement_level + severity * 0.3)
                new_profile.vad_sensitivity = max(0.2, new_profile.vad_sensitivity - severity * 0.1)  # Reduce false positives
                
            elif action == 'reduce_processing_load':
                # Minimize processing requirements
                new_profile.audio_enhancement_level *= (1 - severity * 0.4)
                new_profile.context_window_size = max(1, int(new_profile.context_window_size * (1 - severity * 0.5)))
                new_profile.interim_update_frequency *= (1 - severity * 0.3)
                new_profile.spectral_enhancement = severity < 0.3
                new_profile.noise_reduction_strength *= (1 - severity * 0.2)
                
            elif action == 'reduce_data_usage':
                # Optimize for limited bandwidth
                new_profile.interim_update_frequency *= (1 - severity * 0.4)
                new_profile.context_window_size = max(1, int(new_profile.context_window_size * (1 - severity * 0.3)))
            
            # Ensure values are within valid ranges
            new_profile = self._clamp_profile_values(new_profile)
            
            return new_profile
            
        except Exception as e:
            logger.warning(f"⚠️ Profile calculation failed: {e}")
            return self.current_profile
    
    def _clamp_profile_values(self, profile: QualityProfile) -> QualityProfile:
        """🔒 Ensure profile values are within valid ranges."""
        try:
            profile.audio_enhancement_level = max(0.0, min(1.0, profile.audio_enhancement_level))
            profile.vad_sensitivity = max(0.1, min(1.0, profile.vad_sensitivity))
            profile.context_window_size = max(1, min(5, profile.context_window_size))
            profile.interim_update_frequency = max(1.0, min(10.0, profile.interim_update_frequency))
            profile.latency_priority = max(0.0, min(1.0, profile.latency_priority))
            profile.noise_reduction_strength = max(0.0, min(1.0, profile.noise_reduction_strength))
            
            return profile
            
        except Exception as e:
            logger.warning(f"⚠️ Profile clamping failed: {e}")
            return profile
    
    def _should_apply_profile_change(self, new_profile: QualityProfile) -> bool:
        """🤔 Determine if profile change should be applied."""
        try:
            # Calculate difference between current and new profile
            changes = {
                'audio_enhancement': abs(new_profile.audio_enhancement_level - self.current_profile.audio_enhancement_level),
                'vad_sensitivity': abs(new_profile.vad_sensitivity - self.current_profile.vad_sensitivity),
                'context_window': abs(new_profile.context_window_size - self.current_profile.context_window_size),
                'update_frequency': abs(new_profile.interim_update_frequency - self.current_profile.interim_update_frequency),
                'latency_priority': abs(new_profile.latency_priority - self.current_profile.latency_priority),
                'noise_reduction': abs(new_profile.noise_reduction_strength - self.current_profile.noise_reduction_strength)
            }
            
            # Check if changes are significant enough
            significant_changes = sum(1 for change in changes.values() if change > 0.1)
            total_change_magnitude = sum(changes.values())
            
            # Apply change if there are multiple significant changes or large total change
            should_apply = significant_changes >= 2 or total_change_magnitude > 0.3
            
            return should_apply
            
        except Exception as e:
            logger.warning(f"⚠️ Profile change decision failed: {e}")
            return False
    
    def _apply_profile_change(self, new_profile: QualityProfile, reason: str):
        """✅ Apply new quality profile."""
        try:
            old_profile = self.current_profile
            self.current_profile = new_profile
            
            # Log the adaptation
            adaptation_record = {
                'timestamp': time.time(),
                'reason': reason,
                'old_profile': vars(old_profile),
                'new_profile': vars(new_profile),
                'environmental_conditions': vars(self.environmental_conditions)
            }
            
            self.adaptation_history.append(adaptation_record)
            
            logger.info(f"🎛️ Quality profile adapted: {reason}")
            logger.debug(f"Profile changes: enhancement={new_profile.audio_enhancement_level:.2f}, "
                        f"vad={new_profile.vad_sensitivity:.2f}, "
                        f"context={new_profile.context_window_size}, "
                        f"frequency={new_profile.interim_update_frequency:.1f}")
            
        except Exception as e:
            logger.error(f"❌ Profile application failed: {e}")
    
    def _monitor_and_adapt_continuously(self):
        """🔄 Continuously monitor and adapt quality settings."""
        while self.monitoring_active:
            try:
                time.sleep(5.0)  # Check every 5 seconds
                
                if self.current_mode == QualityMode.ADAPTIVE:
                    self._trigger_adaptive_optimization()
                
            except Exception as e:
                logger.warning(f"⚠️ Continuous monitoring error: {e}")
    
    def get_current_quality_config(self) -> Dict[str, Any]:
        """📋 Get current quality configuration for other services."""
        return {
            'mode': self.current_mode.value,
            'profile': vars(self.current_profile),
            'environmental_conditions': vars(self.environmental_conditions),
            'adaptation_active': self.monitoring_active
        }
    
    def set_quality_mode(self, mode: QualityMode):
        """🎛️ Manually set quality mode."""
        try:
            if mode in self.quality_profiles:
                self.current_mode = mode
                self.current_profile = self.quality_profiles[mode]
                
                logger.info(f"🎛️ Quality mode set to {mode.value}")
            else:
                logger.warning(f"⚠️ Invalid quality mode: {mode}")
                
        except Exception as e:
            logger.error(f"❌ Quality mode setting failed: {e}")
    
    def get_adaptation_history(self) -> List[Dict[str, Any]]:
        """📚 Get adaptation history for analysis."""
        return list(self.adaptation_history)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """📊 Get comprehensive quality performance report."""
        try:
            recent_metrics = list(self.quality_metrics_history)[-10:]
            recent_adaptations = list(self.adaptation_history)[-5:]
            
            if recent_metrics:
                avg_latency = np.mean([m.current_latency_ms for m in recent_metrics])
                avg_confidence = np.mean([m.confidence_score for m in recent_metrics])
                avg_efficiency = np.mean([m.processing_efficiency for m in recent_metrics])
            else:
                avg_latency = avg_confidence = avg_efficiency = 0.0
            
            return {
                'current_mode': self.current_mode.value,
                'current_profile': vars(self.current_profile),
                'environmental_conditions': vars(self.environmental_conditions),
                'performance_metrics': {
                    'avg_latency_ms': avg_latency,
                    'avg_confidence': avg_confidence,
                    'avg_efficiency': avg_efficiency,
                    'metrics_count': len(recent_metrics)
                },
                'adaptation_stats': {
                    'total_adaptations': len(self.adaptation_history),
                    'recent_adaptations': len(recent_adaptations),
                    'adaptation_reasons': [a['reason'] for a in recent_adaptations],
                    'monitoring_active': self.monitoring_active
                },
                'quality_compliance': {
                    'latency_target_met': avg_latency <= 400.0,
                    'confidence_target_met': avg_confidence >= 0.8,
                    'efficiency_target_met': avg_efficiency >= 0.7
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Performance report generation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def reset_adaptation_history(self):
        """🔄 Reset adaptation history."""
        self.adaptation_history.clear()
        self.quality_metrics_history.clear()
        self.environmental_history.clear()
        logger.info("🔄 Adaptation history reset")