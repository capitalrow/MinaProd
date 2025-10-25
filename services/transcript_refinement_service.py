"""
Transcript Refinement Service - CROWN+ Quality Enhancement
Improves transcript quality through grammar correction, punctuation, capitalization, and speaker label cleanup.
"""

import logging
import uuid
import re
from typing import Dict, Any, Optional, List
from models import db, Session, Segment
from datetime import datetime

logger = logging.getLogger(__name__)


class TranscriptRefinementService:
    """
    Refines raw transcription output to improve readability and accuracy.
    
    Improvements:
    - Grammar and punctuation correction
    - Proper capitalization
    - Speaker label normalization
    - Removal of filler words (optional)
    - Paragraph segmentation
    - Confidence-based quality scoring
    """
    
    def __init__(self):
        # Common filler words to optionally remove
        self.filler_words = {
            'um', 'uh', 'er', 'ah', 'like', 'you know', 'i mean', 
            'basically', 'actually', 'literally', 'sort of', 'kind of'
        }
        
        # Sentence ending punctuation
        self.sentence_enders = {'.', '!', '?'}
    
    def refine_session_transcript(
        self, 
        session_id: int,
        trace_id: Optional[uuid.UUID] = None,
        remove_fillers: bool = False
    ) -> Dict[str, Any]:
        """
        Refine the complete transcript for a session.
        
        Args:
            session_id: Database session ID
            trace_id: Optional trace ID for event correlation
            remove_fillers: Whether to remove filler words
            
        Returns:
            Dictionary with refined transcript and improvement metrics
        """
        try:
            # Fetch session and segments
            session = db.session.get(Session, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            segments = db.session.query(Segment).filter_by(
                session_id=session_id
            ).order_by(Segment.start_ms).all()
            
            if not segments:
                return {
                    'refined_text': '',
                    'original_text': '',
                    'improvements': {
                        'grammar_fixes': 0,
                        'punctuation_fixes': 0,
                        'capitalization_fixes': 0,
                        'fillers_removed': 0
                    },
                    'confidence': 0.0
                }
            
            # Extract raw text
            raw_text = ' '.join([seg.text for seg in segments if seg.text])
            
            # Apply refinements
            refined_text = raw_text
            improvements = {
                'grammar_fixes': 0,
                'punctuation_fixes': 0,
                'capitalization_fixes': 0,
                'fillers_removed': 0
            }
            
            # 1. Remove excessive spaces
            refined_text = re.sub(r'\s+', ' ', refined_text).strip()
            
            # 2. Fix capitalization
            refined_text, cap_fixes = self._fix_capitalization(refined_text)
            improvements['capitalization_fixes'] = cap_fixes
            
            # 3. Add punctuation
            refined_text, punct_fixes = self._add_punctuation(refined_text)
            improvements['punctuation_fixes'] = punct_fixes
            
            # 4. Remove filler words (optional)
            if remove_fillers:
                refined_text, filler_count = self._remove_fillers(refined_text)
                improvements['fillers_removed'] = filler_count
            
            # 5. Fix common grammar issues
            refined_text, grammar_fixes = self._fix_grammar(refined_text)
            improvements['grammar_fixes'] = grammar_fixes
            
            # 6. Create paragraphs based on topic shifts
            refined_text = self._create_paragraphs(refined_text)
            
            # Calculate average confidence
            confidences = [seg.avg_confidence for seg in segments if seg.avg_confidence is not None]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(
                f"✅ Transcript refined for session {session.external_id}: "
                f"{len(raw_text)} → {len(refined_text)} chars, "
                f"confidence={avg_confidence:.2f}"
            )
            
            return {
                'refined_text': refined_text,
                'original_text': raw_text,
                'improvements': improvements,
                'confidence': avg_confidence,
                'segments_processed': len(segments)
            }
            
        except Exception as e:
            logger.error(f"❌ Transcript refinement failed: {e}", exc_info=True)
            raise
    
    def _fix_capitalization(self, text: str) -> tuple[str, int]:
        """Fix capitalization issues in text."""
        fixes = 0
        
        # Capitalize first letter of text
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
            fixes += 1
        
        # Capitalize after sentence enders
        sentences = []
        current = []
        
        for char in text:
            current.append(char)
            if char in self.sentence_enders:
                sentence = ''.join(current).strip()
                if sentence:
                    # Capitalize first letter
                    if sentence and not sentence[0].isupper():
                        sentence = sentence[0].upper() + sentence[1:]
                        fixes += 1
                    sentences.append(sentence)
                current = []
        
        # Add remaining text
        if current:
            sentence = ''.join(current).strip()
            if sentence:
                if sentence and not sentence[0].isupper():
                    sentence = sentence[0].upper() + sentence[1:]
                    fixes += 1
                sentences.append(sentence)
        
        return ' '.join(sentences), fixes
    
    def _add_punctuation(self, text: str) -> tuple[str, int]:
        """Add basic punctuation to text."""
        fixes = 0
        
        # Add period at end if missing
        if text and text[-1] not in self.sentence_enders:
            text = text + '.'
            fixes += 1
        
        # Add periods after common abbreviations
        abbreviations = ['mr', 'mrs', 'dr', 'prof', 'sr', 'jr', 'etc', 'inc', 'ltd']
        for abbr in abbreviations:
            pattern = rf'\b{abbr}\b(?!\.)'
            count = len(re.findall(pattern, text, re.IGNORECASE))
            text = re.sub(pattern, f'{abbr}.', text, flags=re.IGNORECASE)
            fixes += count
        
        return text, fixes
    
    def _remove_fillers(self, text: str) -> tuple[str, int]:
        """Remove filler words from text."""
        count = 0
        words = text.split()
        filtered_words = []
        
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if word_lower not in self.filler_words:
                filtered_words.append(word)
            else:
                count += 1
        
        return ' '.join(filtered_words), count
    
    def _fix_grammar(self, text: str) -> tuple[str, int]:
        """Fix common grammar issues."""
        fixes = 0
        original = text
        
        # Fix double negatives (simple cases)
        text = re.sub(r"\bain't no\b", "isn't any", text, flags=re.IGNORECASE)
        text = re.sub(r"\bdon't have no\b", "don't have any", text, flags=re.IGNORECASE)
        
        # Fix common contractions
        text = re.sub(r"\bcannot\b", "can't", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwill not\b", "won't", text, flags=re.IGNORECASE)
        
        # Count changes
        if text != original:
            fixes = len(re.findall(r'\S+', original)) - len(re.findall(r'\S+', text))
        
        return text, abs(fixes)
    
    def _create_paragraphs(self, text: str) -> str:
        """
        Create paragraph breaks based on sentence length and topic shifts.
        
        Simple heuristic: Break into new paragraph every 3-5 sentences.
        """
        sentences = re.split(r'([.!?]\s+)', text)
        
        paragraphs = []
        current_para = []
        sentence_count = 0
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] if i < len(sentences) else ''
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
            
            if sentence.strip():
                current_para.append(sentence + punctuation)
                sentence_count += 1
                
                # Create paragraph break every 4 sentences
                if sentence_count >= 4:
                    paragraphs.append(''.join(current_para).strip())
                    current_para = []
                    sentence_count = 0
        
        # Add remaining sentences
        if current_para:
            paragraphs.append(''.join(current_para).strip())
        
        return '\n\n'.join(paragraphs)


# Singleton instance
_refinement_service = None

def get_transcript_refinement_service() -> TranscriptRefinementService:
    """Get or create the singleton TranscriptRefinementService instance."""
    global _refinement_service
    if _refinement_service is None:
        _refinement_service = TranscriptRefinementService()
    return _refinement_service
