# 🔥 INT-LIVE-I3: Interim Throttling and Endpointing Logic
"""
Implements intelligent interim throttling and endpointing for real-time transcription.
- Throttles interims to 300-500ms intervals
- Only emits if token difference ≥ 5
- Finalizes on VAD tail, punctuation boundaries, or explicit signals
- Tracks session-level metrics
"""

import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import re

logger = logging.getLogger(__name__)

@dataclass
class InterimMetrics:
    """Session-level metrics for interim processing."""
    interim_events: int = 0
    final_events: int = 0
    total_interim_intervals: List[float] = None
    dedupe_hits: int = 0
    low_conf_suppressed: int = 0
    punctuation_finals: int = 0
    vad_tail_finals: int = 0
    explicit_finals: int = 0
    
    def __post_init__(self):
        if self.total_interim_intervals is None:
            self.total_interim_intervals = []
    
    @property
    def avg_interim_interval_ms(self) -> float:
        """Calculate average interim interval in milliseconds."""
        if not self.total_interim_intervals:
            return 0.0
        return sum(self.total_interim_intervals) / len(self.total_interim_intervals)

class InterimThrottler:
    """
    🔥 INT-LIVE-I3: Intelligent interim throttling and endpointing.
    
    Handles:
    - 300-500ms throttling with token diff validation
    - Punctuation boundary detection
    - VAD tail endpointing
    - Structured metrics collection
    """
    
    def __init__(self, config):
        self.config = config
        self.session_states = {}  # {session_id: state_dict}
        
        # Compile punctuation regex for efficiency
        punct_chars = re.escape(config.punctuation_boundary_chars)
        self.punctuation_pattern = re.compile(f'[{punct_chars}]\\s*$')
        
        logger.info("🔥 INT-LIVE-I3: Interim throttler initialized")
    
    def should_emit_interim(self, session_id: str, new_text: str, confidence: float) -> bool:
        """
        Determine if interim should be emitted based on throttling rules.
        
        Returns True if:
        - Time since last interim ≥ throttle_ms
        - Token difference ≥ min_token_diff
        - Confidence above threshold
        """
        now_ms = time.time() * 1000
        
        # Get or create session state
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                'last_interim_time': 0,
                'last_interim_text': '',
                'metrics': InterimMetrics()
            }
        
        state = self.session_states[session_id]
        metrics = state['metrics']
        
        # Check confidence threshold
        if confidence < self.config.min_confidence:
            metrics.low_conf_suppressed += 1
            logger.debug(f"Suppressed low confidence interim: {confidence:.2f}")
            return False
        
        # Check time throttling
        time_since_last = now_ms - state['last_interim_time']
        if time_since_last < self.config.interim_throttle_ms:
            return False
        
        # Check token difference
        token_diff = self._calculate_token_diff(state['last_interim_text'], new_text)
        if token_diff < self.config.min_token_diff:
            metrics.dedupe_hits += 1
            return False
        
        # Update state and metrics
        state['last_interim_time'] = now_ms
        state['last_interim_text'] = new_text
        metrics.interim_events += 1
        
        # Track interval if not first interim
        if state['last_interim_time'] > 0:
            metrics.total_interim_intervals.append(time_since_last)
        
        logger.debug(f"✅ Emitting interim: {token_diff} tokens, {time_since_last:.0f}ms interval")
        return True
    
    def should_finalize(self, session_id: str, text: str, vad_silence_duration: float, 
                       is_explicit_final: bool = False) -> tuple[bool, str]:
        """
        Determine if transcription should be finalized.
        
        Returns (should_finalize, reason)
        """
        if session_id not in self.session_states:
            return False, "no_session"
        
        state = self.session_states[session_id]
        metrics = state['metrics']
        
        # Explicit final signal (user stopped recording)
        if is_explicit_final:
            metrics.explicit_finals += 1
            metrics.final_events += 1
            logger.info(f"🔥 Finalizing on explicit signal: session {session_id}")
            return True, "explicit"
        
        # VAD tail silence
        if vad_silence_duration >= self.config.vad_tail_silence_ms:
            metrics.vad_tail_finals += 1
            metrics.final_events += 1
            logger.info(f"🔥 Finalizing on VAD tail: {vad_silence_duration}ms silence")
            return True, "vad_tail"
        
        # Punctuation boundary + minimum tokens
        if self._has_punctuation_boundary(text):
            token_count = len(text.split())
            if token_count >= self.config.min_tokens_for_punctuation_final:
                metrics.punctuation_finals += 1
                metrics.final_events += 1
                logger.info(f"🔥 Finalizing on punctuation: '{text}' ({token_count} tokens)")
                return True, "punctuation"
        
        return False, "no_trigger"
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get structured metrics for a session."""
        if session_id not in self.session_states:
            return {}
        
        metrics = self.session_states[session_id]['metrics']
        return {
            'interim_events': metrics.interim_events,
            'final_events': metrics.final_events,
            'avg_interim_interval_ms': round(metrics.avg_interim_interval_ms, 1),
            'dedupe_hits': metrics.dedupe_hits,
            'low_conf_suppressed': metrics.low_conf_suppressed,
            'punctuation_finals': metrics.punctuation_finals,
            'vad_tail_finals': metrics.vad_tail_finals,
            'explicit_finals': metrics.explicit_finals
        }
    
    def log_session_metrics(self, session_id: str):
        """Log structured session metrics."""
        metrics = self.get_session_metrics(session_id)
        if metrics:
            logger.info({
                "event": "session_metrics",
                "session_id": session_id,
                **metrics
            })
    
    def cleanup_session(self, session_id: str):
        """Clean up session state when session ends."""
        if session_id in self.session_states:
            # Log final metrics before cleanup
            self.log_session_metrics(session_id)
            del self.session_states[session_id]
            logger.debug(f"Cleaned up session state: {session_id}")
    
    def _calculate_token_diff(self, old_text: str, new_text: str) -> int:
        """Calculate token difference between old and new text."""
        old_tokens = set(old_text.split())
        new_tokens = set(new_text.split())
        return len(new_tokens - old_tokens)
    
    def _has_punctuation_boundary(self, text: str) -> bool:
        """Check if text ends with punctuation boundary."""
        return bool(self.punctuation_pattern.search(text.strip()))

# Global instance for use in transcription service
interim_throttler = None

def get_interim_throttler(config):
    """Get or create global interim throttler instance."""
    global interim_throttler
    if interim_throttler is None:
        interim_throttler = InterimThrottler(config)
    return interim_throttler