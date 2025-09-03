"""
Context Correlation Engine - Google Recorder Level Context Management
Implements intelligent inter-chunk context correlation for seamless transcription continuity.
Ensures smooth semantic flow between transcription chunks.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import time
import hashlib
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionChunk:
    """Enhanced transcription chunk with context metadata."""
    chunk_id: int
    session_id: str
    text: str
    timestamp: float
    confidence: float
    audio_hash: str
    overlap_before: Optional[str] = None
    overlap_after: Optional[str] = None
    context_score: float = 0.0
    semantic_fingerprint: str = ""
    word_timings: List[Dict[str, Any]] = field(default_factory=list)
    is_interim: bool = False
    
@dataclass
class ContextCorrelation:
    """Context correlation between chunks."""
    chunk1_id: int
    chunk2_id: int
    correlation_score: float
    overlap_text: str
    semantic_similarity: float
    temporal_gap: float
    confidence: float

class ContextCorrelationEngine:
    """
    🧠 Advanced context correlation engine for Google Recorder-level continuity.
    
    Provides intelligent inter-chunk correlation, semantic continuity analysis,
    and progressive text building for seamless transcription experience.
    """
    
    def __init__(self, max_context_chunks: int = 5):
        self.max_context_chunks = max_context_chunks
        
        # Context management
        self.chunk_history = deque(maxlen=max_context_chunks)
        self.correlation_cache = {}
        self.semantic_memory = {}
        
        # Progressive text building
        self.progressive_text = ""
        self.confirmed_text = ""
        self.interim_text = ""
        
        # Performance tracking
        self.correlation_times = deque(maxlen=100)
        self.context_scores = deque(maxlen=100)
        
        logger.info("🧠 Context Correlation Engine initialized")
    
    def add_transcription_chunk(self, chunk: TranscriptionChunk) -> Dict[str, Any]:
        """
        🔗 Add new transcription chunk and correlate with context.
        
        Args:
            chunk: New transcription chunk to add
            
        Returns:
            Correlation analysis and progressive text update
        """
        start_time = time.time()
        
        try:
            # Generate semantic fingerprint
            chunk.semantic_fingerprint = self._generate_semantic_fingerprint(chunk.text)
            
            # Correlate with previous chunks
            correlations = self._correlate_with_context(chunk)
            
            # Update progressive text
            text_update = self._update_progressive_text(chunk, correlations)
            
            # Add to history
            self.chunk_history.append(chunk)
            
            # Cache correlations
            for correlation in correlations:
                cache_key = f"{correlation.chunk1_id}_{correlation.chunk2_id}"
                self.correlation_cache[cache_key] = correlation
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self.correlation_times.append(processing_time)
            
            if correlations:
                avg_score = np.mean([c.correlation_score for c in correlations])
                self.context_scores.append(avg_score)
            
            logger.debug(f"🔗 Chunk {chunk.chunk_id} correlated with {len(correlations)} previous chunks")
            
            return {
                'correlations': correlations,
                'text_update': text_update,
                'context_score': chunk.context_score,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"❌ Context correlation failed for chunk {chunk.chunk_id}: {e}")
            
            # Fallback: just append text
            fallback_update = self._fallback_text_update(chunk)
            return {
                'correlations': [],
                'text_update': fallback_update,
                'context_score': 0.0,
                'processing_time': time.time() - start_time
            }
    
    def _correlate_with_context(self, new_chunk: TranscriptionChunk) -> List[ContextCorrelation]:
        """🔍 Correlate new chunk with context history."""
        correlations = []
        
        for prev_chunk in reversed(list(self.chunk_history)):
            if prev_chunk.chunk_id >= new_chunk.chunk_id:
                continue
                
            correlation = self._calculate_chunk_correlation(prev_chunk, new_chunk)
            if correlation.correlation_score > 0.1:  # Minimum threshold
                correlations.append(correlation)
        
        # Sort by correlation strength
        correlations.sort(key=lambda x: x.correlation_score, reverse=True)
        
        return correlations[:3]  # Keep top 3 correlations
    
    def _calculate_chunk_correlation(self, chunk1: TranscriptionChunk, 
                                   chunk2: TranscriptionChunk) -> ContextCorrelation:
        """📊 Calculate correlation between two chunks."""
        try:
            # 1. Temporal correlation (chunks close in time are more likely related)
            temporal_gap = chunk2.timestamp - chunk1.timestamp
            temporal_score = max(0, 1 - temporal_gap / 10.0)  # Decay over 10 seconds
            
            # 2. Text overlap correlation
            overlap_score, overlap_text = self._calculate_text_overlap(chunk1.text, chunk2.text)
            
            # 3. Semantic similarity
            semantic_score = self._calculate_semantic_similarity(
                chunk1.semantic_fingerprint, 
                chunk2.semantic_fingerprint
            )
            
            # 4. Audio correlation (if available)
            audio_score = self._calculate_audio_correlation(chunk1.audio_hash, chunk2.audio_hash)
            
            # 5. Confidence-weighted correlation
            confidence_weight = (chunk1.confidence + chunk2.confidence) / 2
            
            # Combined correlation score
            correlation_score = (
                0.25 * temporal_score +
                0.35 * overlap_score +
                0.25 * semantic_score +
                0.15 * audio_score
            ) * confidence_weight
            
            return ContextCorrelation(
                chunk1_id=chunk1.chunk_id,
                chunk2_id=chunk2.chunk_id,
                correlation_score=correlation_score,
                overlap_text=overlap_text,
                semantic_similarity=semantic_score,
                temporal_gap=temporal_gap,
                confidence=confidence_weight
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Correlation calculation failed: {e}")
            return ContextCorrelation(
                chunk1_id=chunk1.chunk_id,
                chunk2_id=chunk2.chunk_id,
                correlation_score=0.0,
                overlap_text="",
                semantic_similarity=0.0,
                temporal_gap=temporal_gap,
                confidence=0.0
            )
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> Tuple[float, str]:
        """📝 Calculate text overlap between chunks."""
        try:
            if not text1 or not text2:
                return 0.0, ""
            
            # Normalize texts
            words1 = text1.lower().split()
            words2 = text2.lower().split()
            
            if not words1 or not words2:
                return 0.0, ""
            
            # Find longest common subsequence
            matcher = SequenceMatcher(None, words1, words2)
            matching_blocks = matcher.get_matching_blocks()
            
            total_overlap = sum(block.size for block in matching_blocks)
            max_possible = max(len(words1), len(words2))
            
            overlap_score = total_overlap / max_possible if max_possible > 0 else 0.0
            
            # Extract overlap text
            overlap_words = []
            for block in matching_blocks:
                if block.size > 0:
                    overlap_words.extend(words1[block.a:block.a + block.size])
            
            overlap_text = " ".join(overlap_words)
            
            return overlap_score, overlap_text
            
        except Exception as e:
            logger.warning(f"⚠️ Text overlap calculation failed: {e}")
            return 0.0, ""
    
    def _calculate_semantic_similarity(self, fingerprint1: str, fingerprint2: str) -> float:
        """🧠 Calculate semantic similarity between fingerprints."""
        try:
            if not fingerprint1 or not fingerprint2:
                return 0.0
            
            # Simple hash-based similarity (can be enhanced with word embeddings)
            common_chars = sum(1 for a, b in zip(fingerprint1, fingerprint2) if a == b)
            total_chars = max(len(fingerprint1), len(fingerprint2))
            
            similarity = common_chars / total_chars if total_chars > 0 else 0.0
            
            return similarity
            
        except Exception:
            return 0.0
    
    def _calculate_audio_correlation(self, hash1: str, hash2: str) -> float:
        """🎵 Calculate audio similarity correlation."""
        try:
            if not hash1 or not hash2:
                return 0.0
            
            # Simple hash similarity (can be enhanced with audio features)
            common_chars = sum(1 for a, b in zip(hash1, hash2) if a == b)
            total_chars = max(len(hash1), len(hash2))
            
            similarity = common_chars / total_chars if total_chars > 0 else 0.0
            
            return similarity
            
        except Exception:
            return 0.0
    
    def _generate_semantic_fingerprint(self, text: str) -> str:
        """🔍 Generate semantic fingerprint for text."""
        try:
            if not text:
                return ""
            
            # Normalize text
            normalized = text.lower().strip()
            words = normalized.split()
            
            if not words:
                return ""
            
            # Create feature vector
            features = {
                'word_count': len(words),
                'avg_word_length': np.mean([len(w) for w in words]),
                'unique_words': len(set(words)),
                'starts_with_capital': text[0].isupper() if text else False,
                'ends_with_punctuation': text[-1] in '.!?' if text else False,
                'contains_question': '?' in text,
                'contains_numbers': any(c.isdigit() for c in text)
            }
            
            # Create fingerprint hash
            feature_string = str(sorted(features.items()))
            fingerprint = hashlib.md5(feature_string.encode()).hexdigest()[:16]
            
            return fingerprint
            
        except Exception:
            return ""
    
    def _update_progressive_text(self, chunk: TranscriptionChunk, 
                                correlations: List[ContextCorrelation]) -> Dict[str, Any]:
        """📝 Update progressive text with intelligent merging."""
        try:
            if chunk.is_interim:
                return self._update_interim_text(chunk, correlations)
            else:
                return self._update_confirmed_text(chunk, correlations)
                
        except Exception as e:
            logger.warning(f"⚠️ Progressive text update failed: {e}")
            return self._fallback_text_update(chunk)
    
    def _update_interim_text(self, chunk: TranscriptionChunk, 
                           correlations: List[ContextCorrelation]) -> Dict[str, Any]:
        """🔄 Update interim text with correlation awareness."""
        try:
            # Check for strong correlations with recent confirmed text
            strong_correlations = [c for c in correlations if c.correlation_score > 0.6]
            
            if strong_correlations:
                # Merge with existing context
                merged_text = self._merge_with_context(chunk.text, strong_correlations)
                self.interim_text = merged_text
            else:
                # Append to interim text
                if self.interim_text:
                    self.interim_text += " " + chunk.text
                else:
                    self.interim_text = chunk.text
            
            # Update display text
            display_text = self.confirmed_text
            if self.interim_text:
                display_text += " " + self.interim_text if display_text else self.interim_text
            
            return {
                'type': 'interim',
                'text': chunk.text,
                'display_text': display_text.strip(),
                'interim_text': self.interim_text,
                'confirmed_text': self.confirmed_text,
                'merged': bool(strong_correlations)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Interim text update failed: {e}")
            return self._fallback_text_update(chunk)
    
    def _update_confirmed_text(self, chunk: TranscriptionChunk, 
                             correlations: List[ContextCorrelation]) -> Dict[str, Any]:
        """✅ Update confirmed text with deduplication."""
        try:
            # Move interim to confirmed if we have a final chunk
            if self.interim_text:
                # Check for overlap between interim and final
                overlap_score, overlap_text = self._calculate_text_overlap(
                    self.interim_text, chunk.text
                )
                
                if overlap_score > 0.5:
                    # High overlap - replace interim with final
                    self.confirmed_text += " " + chunk.text if self.confirmed_text else chunk.text
                else:
                    # Low overlap - append both
                    if self.confirmed_text:
                        self.confirmed_text += " " + self.interim_text + " " + chunk.text
                    else:
                        self.confirmed_text = self.interim_text + " " + chunk.text
                
                self.interim_text = ""
            else:
                # No interim text - direct append
                if self.confirmed_text:
                    self.confirmed_text += " " + chunk.text
                else:
                    self.confirmed_text = chunk.text
            
            # Clean up confirmed text
            self.confirmed_text = self._clean_text(self.confirmed_text)
            
            return {
                'type': 'confirmed',
                'text': chunk.text,
                'display_text': self.confirmed_text,
                'confirmed_text': self.confirmed_text,
                'interim_text': "",
                'total_words': len(self.confirmed_text.split())
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Confirmed text update failed: {e}")
            return self._fallback_text_update(chunk)
    
    def _merge_with_context(self, new_text: str, 
                          correlations: List[ContextCorrelation]) -> str:
        """🔗 Merge new text with correlated context."""
        try:
            # Find best correlation
            best_correlation = max(correlations, key=lambda x: x.correlation_score)
            
            # Get the correlated chunk
            correlated_chunk = None
            for chunk in self.chunk_history:
                if chunk.chunk_id == best_correlation.chunk1_id:
                    correlated_chunk = chunk
                    break
            
            if not correlated_chunk:
                return new_text
            
            # Intelligent merging based on overlap
            if best_correlation.overlap_text:
                # Remove overlap from new text to avoid duplication
                overlap_words = best_correlation.overlap_text.split()
                new_words = new_text.split()
                
                # Find overlap position in new text
                for i in range(len(new_words) - len(overlap_words) + 1):
                    if new_words[i:i+len(overlap_words)] == overlap_words:
                        # Remove overlap from beginning of new text
                        merged_words = new_words[i+len(overlap_words):]
                        return " ".join(merged_words)
            
            return new_text
            
        except Exception as e:
            logger.warning(f"⚠️ Context merging failed: {e}")
            return new_text
    
    def _clean_text(self, text: str) -> str:
        """🧹 Clean and normalize text."""
        try:
            if not text:
                return ""
            
            # Basic cleaning
            cleaned = text.strip()
            
            # Remove excessive whitespace
            import re
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            # Fix common transcription issues
            cleaned = re.sub(r'\b(um|uh|ah)\b', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            return cleaned
            
        except Exception:
            return text
    
    def _fallback_text_update(self, chunk: TranscriptionChunk) -> Dict[str, Any]:
        """🆘 Fallback text update when correlation fails."""
        if chunk.is_interim:
            self.interim_text = chunk.text
            display_text = self.confirmed_text + " " + self.interim_text if self.confirmed_text else self.interim_text
        else:
            if self.confirmed_text:
                self.confirmed_text += " " + chunk.text
            else:
                self.confirmed_text = chunk.text
            display_text = self.confirmed_text
            self.interim_text = ""
        
        return {
            'type': 'interim' if chunk.is_interim else 'confirmed',
            'text': chunk.text,
            'display_text': display_text.strip(),
            'confirmed_text': self.confirmed_text,
            'interim_text': self.interim_text,
            'fallback': True
        }
    
    def get_progressive_text(self) -> Dict[str, str]:
        """📖 Get current progressive text state."""
        display_text = self.confirmed_text
        if self.interim_text:
            display_text += " " + self.interim_text if display_text else self.interim_text
        
        return {
            'confirmed_text': self.confirmed_text,
            'interim_text': self.interim_text,
            'display_text': display_text.strip()
        }
    
    def reset_session(self):
        """🔄 Reset for new session."""
        self.chunk_history.clear()
        self.correlation_cache.clear()
        self.semantic_memory.clear()
        self.progressive_text = ""
        self.confirmed_text = ""
        self.interim_text = ""
        
        logger.info("🧠 Context correlation engine reset for new session")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """📊 Get performance statistics."""
        return {
            'avg_correlation_time': np.mean(self.correlation_times) if self.correlation_times else 0,
            'avg_context_score': np.mean(self.context_scores) if self.context_scores else 0,
            'chunks_in_context': len(self.chunk_history),
            'confirmed_words': len(self.confirmed_text.split()) if self.confirmed_text else 0,
            'interim_words': len(self.interim_text.split()) if self.interim_text else 0,
            'total_correlations': len(self.correlation_cache)
        }