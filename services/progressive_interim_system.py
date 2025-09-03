"""
Progressive Interim System - Google Recorder Level Text Updates
Implements smooth interim result display with intelligent text building and real-time updates.
Optimized for seamless user experience with progressive text revelation.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
import threading
import queue
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)

@dataclass
class InterimUpdate:
    """Interim transcription update."""
    text: str
    confidence: float
    chunk_id: int
    timestamp: float
    is_final: bool
    word_timings: List[Dict[str, Any]] = field(default_factory=list)
    previous_text: str = ""
    change_type: str = "append"  # append, replace, insert, modify

@dataclass
class TextSegment:
    """Text segment with stability tracking."""
    text: str
    confidence: float
    timestamp: float
    stability_score: float
    confirmed: bool = False
    last_modified: float = 0.0

class ProgressiveInterimSystem:
    """
    📝 Google Recorder-level progressive interim text system.
    
    Provides smooth interim text updates with intelligent text building,
    stability analysis, and seamless final text confirmation.
    """
    
    def __init__(self, stability_threshold: float = 0.8, 
                 confirmation_delay: float = 1.0):
        
        self.stability_threshold = stability_threshold
        self.confirmation_delay = confirmation_delay
        
        # Text management
        self.confirmed_segments: List[TextSegment] = []
        self.interim_segments: List[TextSegment] = []
        self.current_interim_text = ""
        self.last_interim_text = ""
        
        # Update tracking
        self.update_queue = queue.Queue()
        self.update_history = deque(maxlen=100)
        self.text_states = deque(maxlen=50)
        
        # Threading for smooth updates
        self.update_thread = None
        self.running = False
        
        # Performance tracking
        self.update_times = deque(maxlen=100)
        self.stability_scores = deque(maxlen=100)
        
        # Text processing
        self.word_confidence_threshold = 0.7
        self.min_word_length = 2
        
        logger.info("📝 Progressive Interim System initialized")
    
    def start_processing(self):
        """🚀 Start the progressive update processing thread."""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._process_updates_continuously)
            self.update_thread.daemon = True
            self.update_thread.start()
            logger.info("🚀 Progressive interim processing started")
    
    def stop_processing(self):
        """⏹️ Stop the progressive update processing."""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        logger.info("⏹️ Progressive interim processing stopped")
    
    def add_interim_update(self, update: InterimUpdate) -> Dict[str, Any]:
        """
        ➕ Add new interim update for progressive processing.
        
        Args:
            update: New interim transcription update
            
        Returns:
            Immediate processing result and display instructions
        """
        start_time = time.time()
        
        try:
            # Add to processing queue for smooth updates
            self.update_queue.put(update)
            
            # Immediate processing for low-latency response
            immediate_result = self._process_update_immediate(update)
            
            # Track performance
            processing_time = time.time() - start_time
            self.update_times.append(processing_time)
            
            return immediate_result
            
        except Exception as e:
            logger.error(f"❌ Interim update processing failed: {e}")
            return self._create_error_result(update)
    
    def _process_update_immediate(self, update: InterimUpdate) -> Dict[str, Any]:
        """⚡ Process update immediately for low-latency response."""
        try:
            if update.is_final:
                return self._process_final_update(update)
            else:
                return self._process_interim_update(update)
                
        except Exception as e:
            logger.warning(f"⚠️ Immediate update processing failed: {e}")
            return self._create_fallback_result(update)
    
    def _process_interim_update(self, update: InterimUpdate) -> Dict[str, Any]:
        """🔄 Process interim update with stability analysis."""
        try:
            # Analyze text stability
            stability_analysis = self._analyze_text_stability(update)
            
            # Determine update strategy
            update_strategy = self._determine_update_strategy(update, stability_analysis)
            
            # Apply progressive update
            display_result = self._apply_progressive_update(update, update_strategy)
            
            # Update interim state
            self.last_interim_text = self.current_interim_text
            self.current_interim_text = display_result['display_text']
            
            # Track state
            self.text_states.append({
                'text': self.current_interim_text,
                'timestamp': update.timestamp,
                'confidence': update.confidence,
                'stability': stability_analysis['stability_score']
            })
            
            return {
                'type': 'interim',
                'display_text': display_result['display_text'],
                'change_type': update_strategy['change_type'],
                'changed_portion': display_result.get('changed_portion', ''),
                'stability_score': stability_analysis['stability_score'],
                'confidence': update.confidence,
                'smooth_update': display_result.get('smooth_update', False),
                'word_count': len(display_result['display_text'].split()),
                'processing_info': {
                    'strategy': update_strategy,
                    'stability': stability_analysis
                }
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Interim update processing failed: {e}")
            return self._create_fallback_result(update)
    
    def _process_final_update(self, update: InterimUpdate) -> Dict[str, Any]:
        """✅ Process final update with confirmation."""
        try:
            # Confirm interim text as final
            confirmation_result = self._confirm_interim_as_final(update)
            
            # Create final text segment
            final_segment = TextSegment(
                text=update.text,
                confidence=update.confidence,
                timestamp=update.timestamp,
                stability_score=1.0,
                confirmed=True,
                last_modified=time.time()
            )
            
            self.confirmed_segments.append(final_segment)
            
            # Clear interim state
            self.interim_segments.clear()
            self.current_interim_text = ""
            self.last_interim_text = ""
            
            # Build complete confirmed text
            confirmed_text = self._build_complete_confirmed_text()
            
            return {
                'type': 'final',
                'display_text': confirmed_text,
                'final_text': update.text,
                'confidence': update.confidence,
                'word_count': len(confirmed_text.split()),
                'confirmation_info': confirmation_result,
                'total_segments': len(self.confirmed_segments)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Final update processing failed: {e}")
            return self._create_fallback_result(update)
    
    def _analyze_text_stability(self, update: InterimUpdate) -> Dict[str, Any]:
        """📊 Analyze text stability for smooth updates."""
        try:
            stability_factors = {}
            
            # 1. Text similarity with previous interim
            if self.last_interim_text:
                similarity = self._calculate_text_similarity(
                    self.last_interim_text, update.text
                )
                stability_factors['text_similarity'] = similarity
            else:
                stability_factors['text_similarity'] = 1.0
            
            # 2. Confidence stability
            recent_confidences = [state['confidence'] for state in list(self.text_states)[-5:]]
            if recent_confidences:
                confidence_variance = self._calculate_variance(recent_confidences + [update.confidence])
                stability_factors['confidence_stability'] = 1.0 - min(1.0, confidence_variance)
            else:
                stability_factors['confidence_stability'] = update.confidence
            
            # 3. Text length consistency
            if self.text_states:
                recent_lengths = [len(state['text'].split()) for state in list(self.text_states)[-3:]]
                current_length = len(update.text.split())
                length_variance = self._calculate_variance(recent_lengths + [current_length])
                stability_factors['length_consistency'] = 1.0 - min(1.0, length_variance / 10)
            else:
                stability_factors['length_consistency'] = 1.0
            
            # 4. Word-level stability
            word_stability = self._analyze_word_level_stability(update)
            stability_factors['word_stability'] = word_stability
            
            # 5. Temporal consistency
            if self.text_states:
                last_timestamp = self.text_states[-1]['timestamp']
                time_gap = update.timestamp - last_timestamp
                temporal_consistency = max(0.0, 1.0 - time_gap / 5.0)  # Decay over 5 seconds
                stability_factors['temporal_consistency'] = temporal_consistency
            else:
                stability_factors['temporal_consistency'] = 1.0
            
            # Combined stability score
            weights = {
                'text_similarity': 0.3,
                'confidence_stability': 0.2,
                'length_consistency': 0.15,
                'word_stability': 0.25,
                'temporal_consistency': 0.1
            }
            
            stability_score = sum(
                weights[factor] * score 
                for factor, score in stability_factors.items()
            )
            
            return {
                'stability_score': stability_score,
                'factors': stability_factors,
                'is_stable': stability_score >= self.stability_threshold
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Stability analysis failed: {e}")
            return {
                'stability_score': 0.5,
                'factors': {},
                'is_stable': False
            }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """📝 Calculate similarity between two texts."""
        try:
            if not text1 or not text2:
                return 0.0 if text1 != text2 else 1.0
            
            # Use SequenceMatcher for similarity
            matcher = SequenceMatcher(None, text1.split(), text2.split())
            similarity = matcher.ratio()
            
            return float(similarity)
            
        except Exception:
            return 0.0
    
    def _calculate_variance(self, values: List[float]) -> float:
        """📊 Calculate variance of values."""
        try:
            if len(values) < 2:
                return 0.0
            
            import statistics
            return statistics.variance(values)
            
        except Exception:
            return 0.0
    
    def _analyze_word_level_stability(self, update: InterimUpdate) -> float:
        """🔤 Analyze word-level stability."""
        try:
            if not self.last_interim_text:
                return 1.0
            
            current_words = update.text.split()
            previous_words = self.last_interim_text.split()
            
            if not current_words or not previous_words:
                return 0.5
            
            # Calculate word-level changes
            matcher = SequenceMatcher(None, previous_words, current_words)
            matching_blocks = matcher.get_matching_blocks()
            
            total_matching = sum(block.size for block in matching_blocks)
            max_length = max(len(current_words), len(previous_words))
            
            word_stability = total_matching / max_length if max_length > 0 else 1.0
            
            return float(word_stability)
            
        except Exception:
            return 0.5
    
    def _determine_update_strategy(self, update: InterimUpdate, 
                                 stability_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """🎯 Determine optimal update strategy for smooth display."""
        try:
            is_stable = stability_analysis['is_stable']
            stability_score = stability_analysis['stability_score']
            
            # Strategy selection based on stability and content
            if not self.current_interim_text:
                strategy = {
                    'change_type': 'new',
                    'update_mode': 'immediate',
                    'animation': 'fade_in'
                }
            elif is_stable and stability_score > 0.9:
                strategy = {
                    'change_type': 'stable_append',
                    'update_mode': 'smooth',
                    'animation': 'type_effect'
                }
            elif stability_score > 0.6:
                strategy = {
                    'change_type': 'partial_update',
                    'update_mode': 'smooth',
                    'animation': 'highlight_changes'
                }
            else:
                strategy = {
                    'change_type': 'replace',
                    'update_mode': 'immediate',
                    'animation': 'fade_replace'
                }
            
            # Additional strategy parameters
            strategy.update({
                'stability_score': stability_score,
                'confidence_threshold': self.word_confidence_threshold,
                'smooth_transition': stability_score > 0.7,
                'preserve_stable_parts': stability_score > 0.5
            })
            
            return strategy
            
        except Exception as e:
            logger.warning(f"⚠️ Update strategy determination failed: {e}")
            return {
                'change_type': 'replace',
                'update_mode': 'immediate',
                'animation': 'none',
                'stability_score': 0.0
            }
    
    def _apply_progressive_update(self, update: InterimUpdate, 
                                strategy: Dict[str, Any]) -> Dict[str, Any]:
        """🔄 Apply progressive update based on strategy."""
        try:
            change_type = strategy['change_type']
            
            if change_type == 'new':
                return self._apply_new_text_update(update, strategy)
            elif change_type == 'stable_append':
                return self._apply_stable_append_update(update, strategy)
            elif change_type == 'partial_update':
                return self._apply_partial_update(update, strategy)
            else:  # replace
                return self._apply_replace_update(update, strategy)
                
        except Exception as e:
            logger.warning(f"⚠️ Progressive update application failed: {e}")
            return {
                'display_text': update.text,
                'changed_portion': update.text,
                'smooth_update': False
            }
    
    def _apply_new_text_update(self, update: InterimUpdate, 
                             strategy: Dict[str, Any]) -> Dict[str, Any]:
        """🆕 Apply new text update."""
        return {
            'display_text': update.text,
            'changed_portion': update.text,
            'smooth_update': True,
            'animation': strategy.get('animation', 'fade_in')
        }
    
    def _apply_stable_append_update(self, update: InterimUpdate, 
                                  strategy: Dict[str, Any]) -> Dict[str, Any]:
        """➕ Apply stable append update."""
        try:
            # Find the stable portion and new portion
            current_words = self.current_interim_text.split()
            new_words = update.text.split()
            
            # Find common prefix
            common_length = 0
            for i, (curr, new) in enumerate(zip(current_words, new_words)):
                if curr == new:
                    common_length = i + 1
                else:
                    break
            
            # Stable portion
            stable_portion = ' '.join(current_words[:common_length])
            
            # New portion to append
            if common_length < len(new_words):
                new_portion = ' '.join(new_words[common_length:])
                display_text = stable_portion + ' ' + new_portion if stable_portion else new_portion
            else:
                new_portion = ''
                display_text = stable_portion
            
            return {
                'display_text': display_text.strip(),
                'changed_portion': new_portion,
                'stable_portion': stable_portion,
                'smooth_update': True,
                'animation': strategy.get('animation', 'type_effect')
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Stable append update failed: {e}")
            return {
                'display_text': update.text,
                'changed_portion': update.text,
                'smooth_update': False
            }
    
    def _apply_partial_update(self, update: InterimUpdate, 
                            strategy: Dict[str, Any]) -> Dict[str, Any]:
        """🔄 Apply partial update with change highlighting."""
        try:
            # Find differences between current and new text
            current_words = self.current_interim_text.split()
            new_words = update.text.split()
            
            # Use SequenceMatcher to find changes
            matcher = SequenceMatcher(None, current_words, new_words)
            opcodes = matcher.get_opcodes()
            
            changed_portions = []
            display_words = []
            
            for tag, i1, i2, j1, j2 in opcodes:
                if tag == 'equal':
                    # Unchanged portion
                    display_words.extend(current_words[i1:i2])
                elif tag == 'replace':
                    # Changed portion
                    new_portion = new_words[j1:j2]
                    display_words.extend(new_portion)
                    changed_portions.extend(new_portion)
                elif tag == 'insert':
                    # New text inserted
                    new_portion = new_words[j1:j2]
                    display_words.extend(new_portion)
                    changed_portions.extend(new_portion)
                elif tag == 'delete':
                    # Text deleted (skip these words)
                    pass
            
            display_text = ' '.join(display_words)
            changed_text = ' '.join(changed_portions)
            
            return {
                'display_text': display_text,
                'changed_portion': changed_text,
                'smooth_update': True,
                'animation': strategy.get('animation', 'highlight_changes'),
                'change_operations': opcodes
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Partial update failed: {e}")
            return {
                'display_text': update.text,
                'changed_portion': update.text,
                'smooth_update': False
            }
    
    def _apply_replace_update(self, update: InterimUpdate, 
                            strategy: Dict[str, Any]) -> Dict[str, Any]:
        """🔄 Apply replace update."""
        return {
            'display_text': update.text,
            'changed_portion': update.text,
            'smooth_update': strategy.get('smooth_transition', False),
            'animation': strategy.get('animation', 'fade_replace')
        }
    
    def _confirm_interim_as_final(self, update: InterimUpdate) -> Dict[str, Any]:
        """✅ Confirm interim text as final with deduplication."""
        try:
            # Check for overlap with last interim
            overlap_analysis = self._analyze_final_interim_overlap(update)
            
            # Determine confirmation strategy
            if overlap_analysis['high_overlap']:
                confirmation_strategy = 'merge_with_deduplication'
                final_text = overlap_analysis['merged_text']
            else:
                confirmation_strategy = 'direct_confirmation'
                final_text = update.text
            
            return {
                'strategy': confirmation_strategy,
                'final_text': final_text,
                'overlap_analysis': overlap_analysis,
                'interim_text_before': self.current_interim_text
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Final confirmation failed: {e}")
            return {
                'strategy': 'direct_confirmation',
                'final_text': update.text,
                'error': str(e)
            }
    
    def _analyze_final_interim_overlap(self, update: InterimUpdate) -> Dict[str, Any]:
        """🔍 Analyze overlap between final and interim text."""
        try:
            if not self.current_interim_text:
                return {
                    'high_overlap': False,
                    'overlap_score': 0.0,
                    'merged_text': update.text
                }
            
            # Calculate similarity
            similarity = self._calculate_text_similarity(
                self.current_interim_text, update.text
            )
            
            high_overlap = similarity > 0.7
            
            # If high overlap, create merged text
            if high_overlap:
                merged_text = self._merge_final_interim_text(
                    self.current_interim_text, update.text
                )
            else:
                merged_text = update.text
            
            return {
                'high_overlap': high_overlap,
                'overlap_score': similarity,
                'merged_text': merged_text,
                'interim_text': self.current_interim_text,
                'final_text': update.text
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Overlap analysis failed: {e}")
            return {
                'high_overlap': False,
                'overlap_score': 0.0,
                'merged_text': update.text
            }
    
    def _merge_final_interim_text(self, interim_text: str, final_text: str) -> str:
        """🔗 Merge final and interim text intelligently."""
        try:
            # Use the final text as authoritative
            # This prevents duplication while preserving completeness
            return final_text.strip()
            
        except Exception:
            return final_text
    
    def _build_complete_confirmed_text(self) -> str:
        """🏗️ Build complete confirmed text from all segments."""
        try:
            confirmed_texts = [segment.text for segment in self.confirmed_segments]
            complete_text = ' '.join(confirmed_texts)
            
            # Clean up the text
            complete_text = self._clean_final_text(complete_text)
            
            return complete_text
            
        except Exception as e:
            logger.warning(f"⚠️ Complete text building failed: {e}")
            return ""
    
    def _clean_final_text(self, text: str) -> str:
        """🧹 Clean final text."""
        try:
            if not text:
                return ""
            
            # Remove excessive whitespace
            cleaned = re.sub(r'\s+', ' ', text.strip())
            
            # Remove common transcription artifacts
            cleaned = re.sub(r'\b(um|uh|ah)\b', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            return cleaned
            
        except Exception:
            return text
    
    def _process_updates_continuously(self):
        """🔄 Continuously process updates from queue."""
        while self.running:
            try:
                # Get update from queue with timeout
                update = self.update_queue.get(timeout=0.1)
                
                # Process the update
                self._process_queued_update(update)
                
                # Mark task as done
                self.update_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.warning(f"⚠️ Continuous processing error: {e}")
    
    def _process_queued_update(self, update: InterimUpdate):
        """Process update from queue."""
        try:
            # Add to history
            self.update_history.append(update)
            
            # Update stability scores
            if hasattr(update, 'stability_score'):
                self.stability_scores.append(update.stability_score)
            
        except Exception as e:
            logger.warning(f"⚠️ Queued update processing failed: {e}")
    
    def _create_error_result(self, update: InterimUpdate) -> Dict[str, Any]:
        """❌ Create error result."""
        return {
            'type': 'error',
            'display_text': self.current_interim_text,
            'error': 'Processing failed',
            'confidence': 0.0,
            'stability_score': 0.0
        }
    
    def _create_fallback_result(self, update: InterimUpdate) -> Dict[str, Any]:
        """🆘 Create fallback result."""
        return {
            'type': 'interim' if not update.is_final else 'final',
            'display_text': update.text,
            'confidence': update.confidence,
            'stability_score': 0.5,
            'fallback': True
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """📊 Get current system state."""
        return {
            'confirmed_text': self._build_complete_confirmed_text(),
            'interim_text': self.current_interim_text,
            'confirmed_segments': len(self.confirmed_segments),
            'interim_segments': len(self.interim_segments),
            'processing_active': self.running
        }
    
    def reset_session(self):
        """🔄 Reset for new session."""
        self.confirmed_segments.clear()
        self.interim_segments.clear()
        self.current_interim_text = ""
        self.last_interim_text = ""
        self.text_states.clear()
        
        # Clear queues
        while not self.update_queue.empty():
            try:
                self.update_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("🔄 Progressive interim system reset for new session")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """📊 Get performance statistics."""
        try:
            return {
                'avg_update_time': sum(self.update_times) / len(self.update_times) if self.update_times else 0,
                'avg_stability_score': sum(self.stability_scores) / len(self.stability_scores) if self.stability_scores else 0,
                'total_updates_processed': len(self.update_history),
                'confirmed_segments': len(self.confirmed_segments),
                'queue_size': self.update_queue.qsize(),
                'processing_active': self.running
            }
        except Exception:
            return {'status': 'error'}