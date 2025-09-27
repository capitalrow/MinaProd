# services/real_time_punctuation.py
"""
REAL-TIME PUNCTUATION AND CAPITALIZATION ENGINE
Advanced text processing for intelligent punctuation insertion,
capitalization, and sentence structure optimization.
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)

@dataclass
class PunctuationRule:
    """Rule for punctuation insertion"""
    pattern: str
    replacement: str
    confidence: float
    context_required: bool = False
    position: str = "end"  # "start", "end", "middle"

@dataclass
class TextSegment:
    """Enhanced text segment with punctuation metadata"""
    text: str
    confidence: float
    is_sentence_boundary: bool = False
    needs_capitalization: bool = False
    suggested_punctuation: str = ""
    context_score: float = 0.0
    timestamp: float = 0.0

class AdvancedPunctuationEngine:
    """Advanced real-time punctuation and capitalization engine"""
    
    def __init__(self):
        self.sentence_patterns = self._initialize_sentence_patterns()
        self.question_patterns = self._initialize_question_patterns()
        self.exclamation_patterns = self._initialize_exclamation_patterns()
        self.pause_indicators = self._initialize_pause_indicators()
        self.capitalization_rules = self._initialize_capitalization_rules()
        
        # Context tracking
        self.recent_context = deque(maxlen=10)
        self.sentence_history = deque(maxlen=20)
        
        # Statistics
        self.punctuation_stats = defaultdict(int)
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info("📝 Advanced Punctuation Engine initialized")
    
    def _initialize_sentence_patterns(self) -> List[PunctuationRule]:
        """Initialize patterns for sentence ending detection"""
        return [
            # Strong sentence endings
            PunctuationRule(
                pattern=r'\b(therefore|thus|consequently|in conclusion|finally|lastly)\b.*$',
                replacement=r'\g<0>.',
                confidence=0.9,
                context_required=True
            ),
            PunctuationRule(
                pattern=r'\b(that is|in other words|specifically|namely)\b.*$',
                replacement=r'\g<0>.',
                confidence=0.85
            ),
            # Statement patterns
            PunctuationRule(
                pattern=r'\b(i think|i believe|i know|i understand|it seems|apparently)\b.*$',
                replacement=r'\g<0>.',
                confidence=0.8
            ),
            # Declarative statements
            PunctuationRule(
                pattern=r'\b(this is|that was|here is|there are|we have|they have)\b.*$',
                replacement=r'\g<0>.',
                confidence=0.75
            ),
            # Time/sequence indicators
            PunctuationRule(
                pattern=r'\b(first|second|third|next|then|after that|finally)\b.*$',
                replacement=r'\g<0>.',
                confidence=0.7
            )
        ]
    
    def _initialize_question_patterns(self) -> List[PunctuationRule]:
        """Initialize patterns for question detection"""
        return [
            # Direct question words
            PunctuationRule(
                pattern=r'^(what|when|where|who|why|how|which|whose)\b.*$',
                replacement=r'\g<0>?',
                confidence=0.95
            ),
            # Question phrases
            PunctuationRule(
                pattern=r'^(do you|did you|can you|could you|would you|will you|are you|is it)\b.*$',
                replacement=r'\g<0>?',
                confidence=0.9
            ),
            # Tag questions
            PunctuationRule(
                pattern=r'.*\b(right|correct|isnt it|arent they|dont you|wouldnt you)\s*$',
                replacement=r'\g<0>?',
                confidence=0.85
            ),
            # Indirect questions that should be statements
            PunctuationRule(
                pattern=r'^(i wonder|i was wondering|let me ask|tell me)\b.*$',
                replacement=r'\g<0>.',
                confidence=0.8
            )
        ]
    
    def _initialize_exclamation_patterns(self) -> List[PunctuationRule]:
        """Initialize patterns for exclamation detection"""
        return [
            # Strong emotions
            PunctuationRule(
                pattern=r'\b(wow|amazing|incredible|fantastic|terrible|awful|great|excellent)\b.*$',
                replacement=r'\g<0>!',
                confidence=0.8
            ),
            # Interjections
            PunctuationRule(
                pattern=r'^(oh|ah|hey|hello|hi|goodbye|bye|thanks|thank you)\b.*$',
                replacement=r'\g<0>!',
                confidence=0.75
            ),
            # Emphasis patterns
            PunctuationRule(
                pattern=r'\b(absolutely|definitely|certainly|exactly|precisely)\s*$',
                replacement=r'\g<0>!',
                confidence=0.7
            )
        ]
    
    def _initialize_pause_indicators(self) -> List[PunctuationRule]:
        """Initialize patterns for comma insertion"""
        return [
            # Conjunctions
            PunctuationRule(
                pattern=r'\b(and|but|or|so|yet|for|nor)\s+',
                replacement=r', \g<0>',
                confidence=0.8,
                position="middle"
            ),
            # Introductory phrases
            PunctuationRule(
                pattern=r'^(however|moreover|furthermore|additionally|meanwhile|nevertheless)\b',
                replacement=r'\g<0>,',
                confidence=0.85
            ),
            # Lists
            PunctuationRule(
                pattern=r'\b(first|second|third|also|furthermore|additionally|finally)\b',
                replacement=r'\g<0>,',
                confidence=0.7
            ),
            # Parenthetical expressions
            PunctuationRule(
                pattern=r'\b(of course|by the way|in fact|actually|obviously)\b',
                replacement=r', \g<0>,',
                confidence=0.75,
                position="middle"
            )
        ]
    
    def _initialize_capitalization_rules(self) -> List[PunctuationRule]:
        """Initialize capitalization rules"""
        return [
            # Proper nouns (common ones)
            PunctuationRule(
                pattern=r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                replacement=lambda m: m.group(0).capitalize(),
                confidence=0.95
            ),
            PunctuationRule(
                pattern=r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
                replacement=lambda m: m.group(0).capitalize(),
                confidence=0.95
            ),
            # Personal pronouns
            PunctuationRule(
                pattern=r'\bi\b',
                replacement='I',
                confidence=1.0
            )
        ]
    
    def process_text_segment(
        self, 
        text: str, 
        confidence: float, 
        is_final: bool = False,
        context: Optional[str] = None
    ) -> TextSegment:
        """Process text segment for punctuation and capitalization"""
        
        start_time = time.time()
        
        try:
            with self._lock:
                # Clean and normalize text
                cleaned_text = self._clean_text(text)
                
                if not cleaned_text.strip():
                    return TextSegment(
                        text=cleaned_text,
                        confidence=confidence,
                        timestamp=start_time
                    )
                
                # Apply punctuation rules
                processed_text = self._apply_punctuation_rules(cleaned_text, confidence, is_final)
                
                # Apply capitalization
                processed_text = self._apply_capitalization(processed_text)
                
                # Detect sentence boundaries
                is_sentence_boundary = self._is_sentence_boundary(processed_text)
                
                # Calculate context score
                context_score = self._calculate_context_score(processed_text, context)
                
                # Create enhanced segment
                segment = TextSegment(
                    text=processed_text,
                    confidence=confidence,
                    is_sentence_boundary=is_sentence_boundary,
                    needs_capitalization=self._needs_capitalization(processed_text),
                    suggested_punctuation=self._suggest_punctuation(processed_text, confidence),
                    context_score=context_score,
                    timestamp=start_time
                )
                
                # Update context tracking
                self._update_context_tracking(segment)
                
                # Update statistics
                self._update_statistics(segment)
                
                processing_time = (time.time() - start_time) * 1000
                logger.debug(f"📝 Processed text segment in {processing_time:.1f}ms: '{processed_text[:50]}...'")
                
                return segment
                
        except Exception as e:
            logger.error(f"❌ Text processing failed: {e}")
            return TextSegment(
                text=text,
                confidence=confidence,
                timestamp=start_time
            )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text"""
        try:
            # Remove excessive whitespace
            cleaned = re.sub(r'\s+', ' ', text.strip())
            
            # Remove filler words and sounds (configurable)
            filler_patterns = [
                r'\b(um|uh|er|ah|like|you know|sort of|kind of)\b',
                r'\b(basically|actually|literally|obviously)\b(?=\s)'
            ]
            
            for pattern in filler_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
            # Clean up remaining double spaces
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            return cleaned
            
        except Exception as e:
            logger.warning(f"⚠️ Text cleaning failed: {e}")
            return text
    
    def _apply_punctuation_rules(self, text: str, confidence: float, is_final: bool) -> str:
        """Apply punctuation rules to text"""
        try:
            processed_text = text
            
            # Apply rules in order of confidence
            all_rules = (
                self.sentence_patterns + 
                self.question_patterns + 
                self.exclamation_patterns + 
                self.pause_indicators
            )
            
            # Sort by confidence (highest first)
            sorted_rules = sorted(all_rules, key=lambda r: r.confidence, reverse=True)
            
            for rule in sorted_rules:
                # Only apply high-confidence rules for interim text
                if not is_final and rule.confidence < 0.8:
                    continue
                
                try:
                    # Apply pattern matching
                    if callable(rule.replacement):
                        processed_text = re.sub(
                            rule.pattern, 
                            rule.replacement, 
                            processed_text, 
                            flags=re.IGNORECASE
                        )
                    else:
                        processed_text = re.sub(
                            rule.pattern, 
                            rule.replacement, 
                            processed_text, 
                            flags=re.IGNORECASE
                        )
                        
                except Exception as rule_error:
                    logger.warning(f"⚠️ Rule application failed: {rule_error}")
                    continue
            
            return processed_text
            
        except Exception as e:
            logger.warning(f"⚠️ Punctuation rule application failed: {e}")
            return text
    
    def _apply_capitalization(self, text: str) -> str:
        """Apply capitalization rules"""
        try:
            processed_text = text
            
            # Capitalize first letter of text
            if processed_text and processed_text[0].islower():
                processed_text = processed_text[0].upper() + processed_text[1:]
            
            # Apply capitalization rules
            for rule in self.capitalization_rules:
                try:
                    if callable(rule.replacement):
                        processed_text = re.sub(
                            rule.pattern,
                            rule.replacement,
                            processed_text,
                            flags=re.IGNORECASE
                        )
                    else:
                        processed_text = re.sub(
                            rule.pattern,
                            rule.replacement,
                            processed_text,
                            flags=re.IGNORECASE
                        )
                except Exception:
                    continue
            
            # Capitalize after sentence endings
            processed_text = re.sub(
                r'([.!?]\s+)([a-z])',
                lambda m: m.group(1) + m.group(2).upper(),
                processed_text
            )
            
            return processed_text
            
        except Exception as e:
            logger.warning(f"⚠️ Capitalization failed: {e}")
            return text
    
    def _is_sentence_boundary(self, text: str) -> bool:
        """Determine if text represents a sentence boundary"""
        try:
            # Check for sentence ending punctuation
            if re.search(r'[.!?]\s*$', text.strip()):
                return True
            
            # Check for strong conclusive patterns
            conclusive_patterns = [
                r'\b(that\'s all|the end|in conclusion|finally|to summarize)\b.*$',
                r'\b(thank you|thanks|goodbye|bye)\s*$'
            ]
            
            for pattern in conclusive_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _needs_capitalization(self, text: str) -> bool:
        """Check if text needs capitalization"""
        try:
            # Check if starts with lowercase
            if text and text[0].islower():
                return True
            
            # Check for improper capitalization after punctuation
            if re.search(r'[.!?]\s+[a-z]', text):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _suggest_punctuation(self, text: str, confidence: float) -> str:
        """Suggest appropriate punctuation for text"""
        try:
            # If already has punctuation, return empty
            if re.search(r'[.!?]\s*$', text.strip()):
                return ""
            
            # Analyze text patterns for suggestions
            text_lower = text.lower().strip()
            
            # Question indicators
            question_starts = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose']
            question_phrases = ['do you', 'did you', 'can you', 'could you', 'would you', 'will you', 'are you', 'is it']
            
            if any(text_lower.startswith(word) for word in question_starts):
                return "?"
            if any(phrase in text_lower for phrase in question_phrases):
                return "?"
            
            # Exclamation indicators
            exclamation_words = ['wow', 'amazing', 'incredible', 'great', 'terrible', 'awful']
            if any(word in text_lower for word in exclamation_words):
                return "!"
            
            # Default to period for statements
            if confidence > 0.8:
                return "."
            
            return ""
            
        except Exception:
            return ""
    
    def _calculate_context_score(self, text: str, context: Optional[str]) -> float:
        """Calculate contextual relevance score"""
        try:
            if not context:
                return 0.5
            
            # Simple context scoring based on word overlap
            text_words = set(text.lower().split())
            context_words = set(context.lower().split())
            
            if not text_words or not context_words:
                return 0.5
            
            overlap = len(text_words.intersection(context_words))
            total_words = len(text_words.union(context_words))
            
            score = overlap / total_words if total_words > 0 else 0.5
            return min(1.0, max(0.0, score))
            
        except Exception:
            return 0.5
    
    def _update_context_tracking(self, segment: TextSegment):
        """Update context tracking with new segment"""
        try:
            self.recent_context.append({
                'text': segment.text,
                'timestamp': segment.timestamp,
                'is_boundary': segment.is_sentence_boundary,
                'confidence': segment.confidence
            })
            
            if segment.is_sentence_boundary:
                self.sentence_history.append({
                    'text': segment.text,
                    'timestamp': segment.timestamp,
                    'context_score': segment.context_score
                })
                
        except Exception as e:
            logger.warning(f"⚠️ Context tracking update failed: {e}")
    
    def _update_statistics(self, segment: TextSegment):
        """Update punctuation statistics"""
        try:
            # Count punctuation types
            text = segment.text
            self.punctuation_stats['periods'] += text.count('.')
            self.punctuation_stats['questions'] += text.count('?')
            self.punctuation_stats['exclamations'] += text.count('!')
            self.punctuation_stats['commas'] += text.count(',')
            
            # Count segments processed
            self.punctuation_stats['segments_processed'] += 1
            
            if segment.is_sentence_boundary:
                self.punctuation_stats['sentences_detected'] += 1
                
        except Exception as e:
            logger.warning(f"⚠️ Statistics update failed: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        try:
            with self._lock:
                stats = dict(self.punctuation_stats)
                
                # Calculate derived statistics
                total_segments = stats.get('segments_processed', 0)
                if total_segments > 0:
                    stats['sentence_detection_rate'] = stats.get('sentences_detected', 0) / total_segments
                    stats['punctuation_density'] = (
                        stats.get('periods', 0) + 
                        stats.get('questions', 0) + 
                        stats.get('exclamations', 0)
                    ) / total_segments
                else:
                    stats['sentence_detection_rate'] = 0.0
                    stats['punctuation_density'] = 0.0
                
                # Recent context information
                stats['recent_context_length'] = len(self.recent_context)
                stats['sentence_history_length'] = len(self.sentence_history)
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Statistics retrieval failed: {e}")
            return {}
    
    def format_final_transcript(self, segments: List[TextSegment]) -> str:
        """Format final transcript with proper punctuation and structure"""
        try:
            if not segments:
                return ""
            
            # Combine segments intelligently
            formatted_text = ""
            
            for i, segment in enumerate(segments):
                text = segment.text.strip()
                
                if not text:
                    continue
                
                # Add spacing between segments
                if formatted_text and not formatted_text.endswith((' ', '\n')):
                    formatted_text += " "
                
                # Add the segment text
                formatted_text += text
                
                # Add appropriate spacing after sentence boundaries
                if segment.is_sentence_boundary and i < len(segments) - 1:
                    # Check if next segment starts a new sentence
                    next_segment = segments[i + 1]
                    if next_segment.needs_capitalization:
                        formatted_text += " "
            
            # Final cleanup
            formatted_text = re.sub(r'\s+', ' ', formatted_text).strip()
            
            # Ensure proper capitalization
            if formatted_text and formatted_text[0].islower():
                formatted_text = formatted_text[0].upper() + formatted_text[1:]
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"❌ Final transcript formatting failed: {e}")
            return " ".join(segment.text for segment in segments if segment.text.strip())

# Global punctuation engine instance
_punctuation_engine = None
_punctuation_lock = threading.Lock()

def get_punctuation_engine() -> AdvancedPunctuationEngine:
    """Get global punctuation engine instance"""
    global _punctuation_engine
    
    with _punctuation_lock:
        if _punctuation_engine is None:
            _punctuation_engine = AdvancedPunctuationEngine()
        return _punctuation_engine

logger.info("✅ Real-time Punctuation Engine module initialized")