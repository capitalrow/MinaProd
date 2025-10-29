"""
QuietStateManager Service - CROWN⁴.5 Emotional Calm Architecture

Limits concurrent animations to ≤3 for emotional calm. Implements animation queue
with priority system and emotional calm scoring.

Key Features:
- Animation concurrency limiting (max 3 simultaneous)
- Priority-based animation queue
- Emotional calm scoring
- Animation timing coordination
- Prevents overwhelming visual feedback
"""

import logging
import time
from typing import Optional, Dict, Any, List
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class AnimationPriority(Enum):
    """Priority levels for animations."""
    CRITICAL = 1  # User-initiated actions (task complete, create)
    HIGH = 2      # Real-time updates (sync success, new task)
    MEDIUM = 3    # Secondary feedback (counters, filters)
    LOW = 4       # Ambient effects (empty state pulse)


class Animation:
    """Represents a queued animation."""
    
    def __init__(
        self,
        animation_id: str,
        animation_type: str,
        target_element: str,
        duration_ms: int,
        priority: AnimationPriority = AnimationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.animation_id = animation_id
        self.animation_type = animation_type
        self.target_element = target_element
        self.duration_ms = duration_ms
        self.priority = priority
        self.metadata = metadata or {}
        self.queued_at = time.time() * 1000  # milliseconds
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert animation to dictionary."""
        return {
            'animation_id': self.animation_id,
            'animation_type': self.animation_type,
            'target_element': self.target_element,
            'duration_ms': self.duration_ms,
            'priority': self.priority.value,
            'metadata': self.metadata,
            'queued_at': self.queued_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }


class QuietStateManager:
    """
    Service for managing animation concurrency and emotional calm.
    
    Responsibilities:
    - Limit concurrent animations to ≤3
    - Queue animations with priority ordering
    - Calculate emotional calm score
    - Coordinate animation timing
    - Prevent overwhelming user with too many simultaneous animations
    """
    
    # Configuration constants
    MAX_CONCURRENT_ANIMATIONS = 3  # CROWN⁴.5 requirement
    CALM_SCORE_THRESHOLD = 0.75  # Target calm score (0-1)
    ANIMATION_COOLDOWN_MS = 100  # Minimum time between animation starts
    
    def __init__(self):
        """Initialize QuietStateManager with empty queues."""
        # Active animations (currently playing)
        self.active_animations: List[Animation] = []
        
        # Queued animations (waiting to play)
        self.animation_queue: deque[Animation] = deque()
        
        # Animation history for calm score calculation
        self.animation_history: List[Animation] = []
        
        # Timing control
        self.last_animation_start_time: float = 0
        
        # Metrics
        self.metrics = {
            'total_animations': 0,
            'queued_count': 0,
            'skipped_count': 0,
            'calm_violations': 0
        }
    
    def _should_cooldown(self) -> bool:
        """
        Check if we're in cooldown period after last animation start.
        
        Returns:
            True if in cooldown, False otherwise
        """
        current_time = time.time() * 1000
        time_since_last = current_time - self.last_animation_start_time
        
        return time_since_last < self.ANIMATION_COOLDOWN_MS
    
    def _can_start_animation(self) -> bool:
        """
        Check if we can start a new animation.
        
        Returns:
            True if can start, False if at capacity
        """
        # Check concurrency limit
        if len(self.active_animations) >= self.MAX_CONCURRENT_ANIMATIONS:
            return False
        
        # Check cooldown
        if self._should_cooldown():
            return False
        
        return True
    
    def _cleanup_completed_animations(self):
        """Remove completed animations from active list."""
        current_time = time.time() * 1000
        
        # Find completed animations
        completed = []
        for anim in self.active_animations:
            if anim.started_at is not None:
                elapsed = current_time - anim.started_at
                if elapsed >= anim.duration_ms:
                    anim.completed_at = current_time
                    completed.append(anim)
        
        # Move to history
        for anim in completed:
            self.active_animations.remove(anim)
            self.animation_history.append(anim)
            
            # Keep history bounded (last 100 animations)
            if len(self.animation_history) > 100:
                self.animation_history.pop(0)
        
        return len(completed)
    
    def queue_animation(
        self,
        animation_type: str,
        target_element: str,
        duration_ms: int = 300,
        priority: AnimationPriority = AnimationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        force_immediate: bool = False
    ) -> Dict[str, Any]:
        """
        Queue an animation for playback.
        
        Args:
            animation_type: Type of animation (e.g., 'pop_in', 'fade', 'pulse')
            target_element: DOM element ID or selector
            duration_ms: Animation duration in milliseconds
            priority: Animation priority
            metadata: Additional animation metadata
            force_immediate: Skip queue and start immediately if possible
            
        Returns:
            Response with animation ID and status
        """
        try:
            # Generate animation ID
            animation_id = f"{animation_type}_{int(time.time() * 1000)}"
            
            # Create animation object
            animation = Animation(
                animation_id=animation_id,
                animation_type=animation_type,
                target_element=target_element,
                duration_ms=duration_ms,
                priority=priority,
                metadata=metadata
            )
            
            # Update metrics
            self.metrics['total_animations'] += 1
            
            # Cleanup completed animations first
            self._cleanup_completed_animations()
            
            # Check if we can start immediately
            if force_immediate or (self._can_start_animation() and len(self.animation_queue) == 0):
                return self._start_animation(animation)
            else:
                # Add to queue with priority ordering
                return self._enqueue_animation(animation)
                
        except Exception as e:
            logger.error(f"Failed to queue animation: {e}")
            return {
                'animation_id': None,
                'status': 'error',
                'error': str(e)
            }
    
    def _start_animation(self, animation: Animation) -> Dict[str, Any]:
        """
        Start an animation immediately.
        
        Args:
            animation: Animation to start
            
        Returns:
            Response with animation details
        """
        animation.started_at = time.time() * 1000
        self.active_animations.append(animation)
        self.last_animation_start_time = animation.started_at
        
        logger.debug(
            f"Started animation {animation.animation_id} "
            f"(active: {len(self.active_animations)}/{self.MAX_CONCURRENT_ANIMATIONS})"
        )
        
        return {
            'animation_id': animation.animation_id,
            'status': 'started',
            'animation': animation.to_dict(),
            'active_count': len(self.active_animations),
            'queued_count': len(self.animation_queue)
        }
    
    def _enqueue_animation(self, animation: Animation) -> Dict[str, Any]:
        """
        Add animation to priority queue.
        
        Args:
            animation: Animation to queue
            
        Returns:
            Response with queue position
        """
        # Find insertion position based on priority
        inserted = False
        for i, queued_anim in enumerate(self.animation_queue):
            if animation.priority.value < queued_anim.priority.value:
                # Insert before this animation (higher priority)
                self.animation_queue.insert(i, animation)
                inserted = True
                break
        
        if not inserted:
            # Add to end of queue
            self.animation_queue.append(animation)
        
        self.metrics['queued_count'] += 1
        
        logger.debug(
            f"Queued animation {animation.animation_id} "
            f"(priority: {animation.priority.name}, queue size: {len(self.animation_queue)})"
        )
        
        return {
            'animation_id': animation.animation_id,
            'status': 'queued',
            'queue_position': list(self.animation_queue).index(animation),
            'queue_size': len(self.animation_queue),
            'estimated_wait_ms': self._estimate_wait_time(animation)
        }
    
    def _estimate_wait_time(self, animation: Animation) -> int:
        """
        Estimate how long until this animation will play.
        
        Args:
            animation: Queued animation
            
        Returns:
            Estimated wait time in milliseconds
        """
        # Find position in queue
        try:
            position = list(self.animation_queue).index(animation)
        except ValueError:
            return 0
        
        # Estimate based on active animations finishing + queue position
        estimated_wait = 0
        
        # Time until current animations complete
        current_time = time.time() * 1000
        for active in self.active_animations:
            if active.started_at:
                remaining = active.duration_ms - (current_time - active.started_at)
                estimated_wait = max(estimated_wait, remaining)
        
        # Add time for animations ahead in queue
        for i in range(position):
            estimated_wait += self.animation_queue[i].duration_ms
        
        return int(estimated_wait)
    
    def process_queue(self) -> List[Dict[str, Any]]:
        """
        Process animation queue and start animations if possible.
        
        Returns:
            List of started animations
        """
        started_animations = []
        
        # Cleanup completed animations
        self._cleanup_completed_animations()
        
        # Start queued animations if slots available
        while self._can_start_animation() and len(self.animation_queue) > 0:
            animation = self.animation_queue.popleft()
            result = self._start_animation(animation)
            started_animations.append(result)
        
        return started_animations
    
    def cancel_animation(self, animation_id: str) -> bool:
        """
        Cancel a queued or active animation.
        
        Args:
            animation_id: Animation ID to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        # Check active animations
        for anim in self.active_animations:
            if anim.animation_id == animation_id:
                self.active_animations.remove(anim)
                logger.info(f"Cancelled active animation {animation_id}")
                return True
        
        # Check queue
        for anim in self.animation_queue:
            if anim.animation_id == animation_id:
                self.animation_queue.remove(anim)
                logger.info(f"Cancelled queued animation {animation_id}")
                return True
        
        return False
    
    def calculate_calm_score(self, time_window_ms: int = 5000) -> float:
        """
        Calculate emotional calm score based on recent animation activity.
        
        Calm score is 1.0 (perfect calm) when no animations running,
        decreases with more concurrent/frequent animations.
        
        Args:
            time_window_ms: Time window for history analysis (default 5s)
            
        Returns:
            Calm score (0.0 to 1.0, higher is calmer)
        """
        try:
            current_time = time.time() * 1000
            
            # Count recent animations
            recent_animations = [
                anim for anim in self.animation_history
                if anim.completed_at and (current_time - anim.completed_at) < time_window_ms
            ]
            
            # Factors affecting calm score
            active_count = len(self.active_animations)
            queued_count = len(self.animation_queue)
            recent_count = len(recent_animations)
            
            # Calculate score components
            active_penalty = (active_count / self.MAX_CONCURRENT_ANIMATIONS) * 0.4
            queued_penalty = min(queued_count / 10, 1.0) * 0.3
            frequency_penalty = min(recent_count / 20, 1.0) * 0.3
            
            # Calm score = 1.0 - total penalty
            calm_score = max(0.0, 1.0 - (active_penalty + queued_penalty + frequency_penalty))
            
            # Track violations
            if calm_score < self.CALM_SCORE_THRESHOLD:
                self.metrics['calm_violations'] += 1
            
            return calm_score
            
        except Exception as e:
            logger.error(f"Failed to calculate calm score: {e}")
            return 0.5  # Return neutral score on error
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current QuietStateManager state.
        
        Returns:
            Dictionary with current state
        """
        # Cleanup first
        self._cleanup_completed_animations()
        
        return {
            'active_animations': [anim.to_dict() for anim in self.active_animations],
            'queued_animations': [anim.to_dict() for anim in self.animation_queue],
            'active_count': len(self.active_animations),
            'queued_count': len(self.animation_queue),
            'max_concurrent': self.MAX_CONCURRENT_ANIMATIONS,
            'calm_score': self.calculate_calm_score(),
            'metrics': self.metrics
        }
    
    def clear_queue(self):
        """Clear all queued animations."""
        cleared_count = len(self.animation_queue)
        self.animation_queue.clear()
        logger.info(f"Cleared {cleared_count} queued animations")


# Singleton instance
quiet_state_manager = QuietStateManager()
