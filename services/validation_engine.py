"""
ValidationEngine - Multi-layer validation system for AI-generated content
Prevents hallucinations and ensures high-quality task extraction
"""
import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation with score and reasoning"""
    is_valid: bool
    score: float
    reasons: List[str]
    metadata: Optional[Dict] = None


@dataclass
class TaskQualityScore:
    """Quality score breakdown for a task"""
    total_score: float
    has_action_verb: bool
    has_subject: bool
    appropriate_length: bool
    has_evidence: bool
    verb_score: float
    subject_score: float
    length_score: float
    evidence_score: float


class ValidationEngine:
    """Multi-tier validation system for AI outputs"""
    
    # Action verbs that indicate tasks
    ACTION_VERBS = {
        'update', 'create', 'build', 'implement', 'review', 'schedule', 'prepare',
        'send', 'draft', 'complete', 'finish', 'develop', 'design', 'analyze',
        'research', 'investigate', 'test', 'validate', 'deploy', 'configure',
        'setup', 'install', 'verify', 'check', 'confirm', 'approve', 'submit',
        'follow', 'coordinate', 'organize', 'plan', 'define', 'document',
        'refactor', 'optimize', 'improve', 'fix', 'resolve', 'address',
        'discuss', 'meet', 'present', 'share', 'communicate', 'notify'
    }
    
    # Meta-testing keywords that indicate system testing/demo
    META_TESTING_PATTERNS = [
        r'test(?:ing)?\s+(?:the\s+)?(?:application|system|pipeline|extraction)',
        r'check(?:ing)?\s+(?:if|that|whether)\s+(?:the\s+)?(?:task|system)',
        r'verify(?:ing)?\s+(?:that|if)\s+(?:the\s+)?(?:extraction|pipeline)',
        r'demo(?:nstrat(?:e|ing))?',
        r'showing\s+(?:you|how)',
        r'walk(?:ing)?\s+through',
        r'post-?(?:trans)?(?:cription|subscription)\s+(?:activities|pipeline)',
        r'make\s+sure\s+(?:that\s+)?(?:the\s+)?task',
        r'from\s+my\s+side',  # Common filler phrase
        r'here\s+(?:we\s+)?are',  # Narration
        r'(?:this|that)\s+is\s+(?:the|a)\s+showstopper',  # Demo language
        r'i\s+need\s+to\s+check',  # User describing checking
        r'i\s+will\s+go\s+ahead',  # Narration
        r'(?:take|taking)\s+from\s+here',  # Narration
        r'(?:these|those)\s+are\s+the\s+following',  # Listing/narration
        r'let\s+me\s+(?:check|verify|test)',  # User describing their actions
        r'making\s+sure\s+that',  # Verification description
        r'i\s+(?:want|need)\s+to\s+(?:ensure|verify|validate)',  # Testing intent
        r'going\s+to\s+(?:check|test|verify)',  # Future testing
        r'tabs?\s+are\s+relevantly\s+and\s+correctly'  # Specific broken pattern from user's session
    ]
    
    # Quality thresholds
    MIN_TASK_SCORE = 0.70  # Raised from 0.65 for higher quality standards
    MIN_SUMMARY_SIMILARITY = 0.7
    MIN_TASK_LENGTH = 8
    MAX_TASK_LENGTH = 100
    DEDUP_SIMILARITY_THRESHOLD = 0.7  # Lowered from 0.8 to catch more semantic duplicates
    
    def __init__(self):
        """Initialize validation engine"""
        self.meta_patterns_compiled = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.META_TESTING_PATTERNS
        ]
    
    def check_semantic_similarity(
        self, 
        summary: str, 
        transcript: str
    ) -> ValidationResult:
        """
        Check if summary semantically matches the transcript.
        Uses word overlap and sequence matching to detect hallucinations.
        """
        if not summary or not transcript:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reasons=["Empty summary or transcript"]
            )
        
        # Normalize text
        summary_words = set(self._normalize_text(summary).split())
        transcript_words = set(self._normalize_text(transcript).split())
        
        # Calculate word overlap (Jaccard similarity)
        if not transcript_words:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reasons=["Empty transcript after normalization"]
            )
        
        overlap = len(summary_words & transcript_words)
        jaccard = overlap / len(summary_words | transcript_words)
        
        # Calculate sequence similarity
        sequence_sim = SequenceMatcher(None, summary.lower(), transcript.lower()).ratio()
        
        # Combined score (favor Jaccard for detecting hallucinations)
        score = (jaccard * 0.7) + (sequence_sim * 0.3)
        
        is_valid = score >= self.MIN_SUMMARY_SIMILARITY
        
        reasons = []
        if not is_valid:
            reasons.append(f"Low semantic similarity: {score:.2f} < {self.MIN_SUMMARY_SIMILARITY}")
            reasons.append(f"Word overlap: {overlap}/{len(summary_words)} words")
            
            # Detect potential hallucinations
            hallucinated = summary_words - transcript_words
            if len(hallucinated) > len(summary_words) * 0.5:
                sample = list(hallucinated)[:5]
                reasons.append(f"Potential hallucinated content: {', '.join(sample)}...")
        
        return ValidationResult(
            is_valid=is_valid,
            score=score,
            reasons=reasons if not is_valid else [f"Similarity score: {score:.2f}"],
            metadata={
                'jaccard_similarity': jaccard,
                'sequence_similarity': sequence_sim,
                'word_overlap': overlap,
                'summary_words': len(summary_words),
                'transcript_words': len(transcript_words)
            }
        )
    
    def detect_meta_testing(self, transcript: str) -> ValidationResult:
        """
        Detect if transcript is meta-testing/demo commentary vs real meeting.
        Returns high score if meta-testing detected.
        """
        if not transcript:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reasons=["Empty transcript"]
            )
        
        matches = []
        for pattern in self.meta_patterns_compiled:
            found = pattern.findall(transcript)
            if found:
                matches.extend(found)
        
        # Calculate meta-testing score (0-1)
        # Higher score = more likely meta-testing
        meta_score = min(len(matches) / 3.0, 1.0)  # 3+ matches = definitely meta
        
        is_meta_testing = meta_score > 0.3
        
        reasons = []
        if is_meta_testing:
            reasons.append(f"Meta-testing detected (score: {meta_score:.2f})")
            reasons.append(f"Found {len(matches)} meta-testing indicators")
            if matches:
                reasons.append(f"Examples: {matches[:3]}")
        
        return ValidationResult(
            is_valid=is_meta_testing,
            score=meta_score,
            reasons=reasons if is_meta_testing else ["Appears to be real meeting content"],
            metadata={
                'match_count': len(matches),
                'matches': matches[:5]  # Store first 5 for debugging
            }
        )
    
    def validate_evidence_quote(
        self, 
        claim: str, 
        evidence_quote: str, 
        transcript: str
    ) -> ValidationResult:
        """
        Validate that the evidence quote actually exists in transcript
        and supports the claim.
        """
        if not evidence_quote:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reasons=["No evidence quote provided"]
            )
        
        # Check if quote exists in transcript (fuzzy match)
        normalized_transcript = self._normalize_text(transcript)
        normalized_quote = self._normalize_text(evidence_quote)
        
        # Direct substring match
        if normalized_quote in normalized_transcript:
            return ValidationResult(
                is_valid=True,
                score=1.0,
                reasons=["Evidence quote found verbatim in transcript"]
            )
        
        # Fuzzy match (allow minor differences)
        quote_words = normalized_quote.split()
        if len(quote_words) < 3:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reasons=["Evidence quote too short (<3 words)"]
            )
        
        # Check if most words from quote appear in transcript
        transcript_words = set(normalized_transcript.split())
        quote_word_set = set(quote_words)
        overlap = len(quote_word_set & transcript_words)
        overlap_ratio = overlap / len(quote_word_set)
        
        is_valid = overlap_ratio >= 0.7  # 70% of words must appear
        
        return ValidationResult(
            is_valid=is_valid,
            score=overlap_ratio,
            reasons=[
                f"Evidence quote word match: {overlap}/{len(quote_word_set)} words ({overlap_ratio:.0%})"
            ] if is_valid else [
                f"Evidence quote not found in transcript (only {overlap_ratio:.0%} word match)"
            ]
        )
    
    def check_sentence_completeness(self, task_text: str) -> ValidationResult:
        """
        Check if task is a complete, grammatically sound sentence.
        
        Detects:
        - Cut-off mid-sentence (ends with "and", "or", conjunction)
        - Broken grammar ("is then check", "from here is")
        - Incomplete phrases ("relevantly and correctly" with no continuation)
        - Sentence fragments
        """
        if not task_text or not task_text.strip():
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reasons=["Empty task text"]
            )
        
        task_clean = task_text.strip()
        task_lower = task_clean.lower()
        
        # Check 1: Ends mid-thought with conjunction
        incomplete_endings = [
            ' and', ' or', ' but', ' with', ' to', ' from', ' for',
            ' the', ' a', ' an', ' is', ' are', ' will', ' should'
        ]
        for ending in incomplete_endings:
            if task_clean.endswith(ending):
                return ValidationResult(
                    is_valid=False,
                    score=0.2,
                    reasons=[f"Sentence cuts off mid-thought (ends with '{ending}')"]
                )
        
        # Check 2: Contains broken grammar patterns
        broken_patterns = [
            r'\s+is\s+then\s+',  # "from here is then check"
            r'\s+from\s+here\s+is\s+',  # "take from here is"
            r'\s+that\s+all\s+the\s+tabs\s+are\s+relevantly\s+and\s+correctly$',  # cut-off example
        ]
        for pattern in broken_patterns:
            if re.search(pattern, task_lower):
                return ValidationResult(
                    is_valid=False,
                    score=0.3,
                    reasons=[f"Broken grammar detected (pattern: {pattern})"]
                )
        
        # Check 3: Too short to be meaningful (< 3 words)
        word_count = len(task_clean.split())
        if word_count < 3:
            return ValidationResult(
                is_valid=False,
                score=0.4,
                reasons=[f"Too short to be meaningful ({word_count} words)"]
            )
        
        # Check 4: Missing verb (HARD-FAIL - all tasks must have action verbs)
        has_verb = any(verb in task_lower for verb in self.ACTION_VERBS)
        if not has_verb:
            return ValidationResult(
                is_valid=False,
                score=0.3,  # Hard fail - no action verb = not a valid task
                reasons=["Missing action verb - not a valid task (fragments rejected)"]
            )
        
        # Sentence appears complete
        return ValidationResult(
            is_valid=True,
            score=1.0,
            reasons=["Sentence appears grammatically complete with action verb"]
        )
    
    def score_task_quality(
        self, 
        task_text: str, 
        evidence_quote: Optional[str] = None,
        transcript: Optional[str] = None
    ) -> TaskQualityScore:
        """
        Score task quality using rubric:
        - Action verb (0.3): Has clear action verb
        - Subject (0.2): Has clear subject (who/what)
        - Length (0.2): Appropriate length (8-100 words)
        - Evidence (0.3): Has valid evidence quote
        
        ENHANCED: Now includes sentence completeness check, meta-commentary detection, and professional language scoring
        """
        task_lower = task_text.lower()
        words = task_text.split()
        word_count = len(words)
        
        # 0. Completeness check (CRITICAL - rejects broken sentences)
        completeness = self.check_sentence_completeness(task_text)
        if not completeness.is_valid:
            logger.warning(f"Task rejected for incompleteness: {task_text[:50]}... - {completeness.reasons}")
            # Return very low score to trigger rejection
            return TaskQualityScore(
                total_score=0.2,  # Well below 0.70 threshold
                has_action_verb=False,
                has_subject=False,
                appropriate_length=False,
                has_evidence=False,
                verb_score=0.0,
                subject_score=0.0,
                length_score=0.0,
                evidence_score=0.0
            )
        
        # 0.1 Meta-commentary check (REJECT meta-testing descriptions)
        for pattern in self.meta_patterns_compiled:
            if pattern.search(task_lower):
                logger.warning(f"Task rejected as meta-commentary: {task_text[:50]}... (matched pattern: {pattern.pattern})")
                return TaskQualityScore(
                    total_score=0.15,  # Well below threshold
                    has_action_verb=False,
                    has_subject=False,
                    appropriate_length=False,
                    has_evidence=False,
                    verb_score=0.0,
                    subject_score=0.0,
                    length_score=0.0,
                    evidence_score=0.0
                )
        
        # 0.2 Professional language check (DEDUCT for conversational tone)
        professional_penalty = 0.0
        
        # Check for first-person pronouns (unprofessional for tasks)
        first_person_patterns = [
            r'\bi\s+',  # "I will", "I need"
            r'\bi\'ll\s+',  # "I'll"
            r'\bi\'m\s+',  # "I'm"
            r'\bwe\s+',  # "We will"
            r'\bwe\'ll\s+',  # "We'll"
            r'\blet\s+me\s+',  # "Let me"
            r'\blet\'s\s+'  # "Let's"
        ]
        first_person_count = sum(1 for pattern in first_person_patterns if re.search(pattern, task_lower))
        if first_person_count > 0:
            professional_penalty += 0.15 * min(first_person_count, 3)  # Up to -0.45 penalty
            logger.debug(f"Professional penalty: -{professional_penalty:.2f} for first-person language in '{task_text[:40]}'")
        
        # Check for conversational fillers
        filler_patterns = [
            r'\bjust\s+',
            r'\bquickly\s+',
            r'\btry\s+not\s+to\s+',
            r'\bkind\s+of\s+',
            r'\bsort\s+of\s+',
            r'\bbasically\s+',
            r'\bprobably\s+'
        ]
        filler_count = sum(1 for pattern in filler_patterns if re.search(pattern, task_lower))
        if filler_count > 0:
            professional_penalty += 0.1 * min(filler_count, 2)  # Up to -0.2 penalty
            logger.debug(f"Professional penalty: -{professional_penalty:.2f} for conversational fillers in '{task_text[:40]}'")
        
        # If penalty is too high, reject immediately
        if professional_penalty >= 0.3:
            logger.warning(f"Task rejected for unprofessional language (penalty: {professional_penalty:.2f}): {task_text[:50]}...")
            return TaskQualityScore(
                total_score=0.25,  # Below threshold
                has_action_verb=False,
                has_subject=False,
                appropriate_length=False,
                has_evidence=False,
                verb_score=0.0,
                subject_score=0.0,
                length_score=0.0,
                evidence_score=0.0
            )
        
        # 1. Action verb check (0.3 weight)
        has_verb = any(verb in task_lower for verb in self.ACTION_VERBS)
        verb_score = 0.3 if has_verb else 0.0
        
        # 2. Subject check (0.2 weight)
        # Simple heuristic: contains pronouns/names or noun phrases
        subject_indicators = ['we', 'i', 'team', 'sarah', 'john', 'they', 'he', 'she']
        has_subject = (
            any(ind in task_lower for ind in subject_indicators) or
            len([w for w in words if w[0].isupper()]) > 0  # Capitalized words (names)
        )
        subject_score = 0.2 if has_subject else 0.0
        
        # 3. Length check (0.2 weight)
        appropriate_length = self.MIN_TASK_LENGTH <= word_count <= self.MAX_TASK_LENGTH
        length_score = 0.2 if appropriate_length else (
            0.1 if word_count < self.MIN_TASK_LENGTH else 0.0  # Partial credit if too short
        )
        
        # 4. Evidence check (0.3 weight)
        evidence_score = 0.0
        has_evidence = False
        if evidence_quote and transcript:
            validation = self.validate_evidence_quote(task_text, evidence_quote, transcript)
            has_evidence = validation.is_valid
            evidence_score = 0.3 * validation.score
        
        # Calculate total score and apply professional language penalty
        base_score = verb_score + subject_score + length_score + evidence_score
        total_score = max(0.0, base_score - professional_penalty)  # Apply penalty, floor at 0
        
        if professional_penalty > 0:
            logger.debug(f"Task quality: base={base_score:.2f}, penalty={professional_penalty:.2f}, final={total_score:.2f}")
        
        return TaskQualityScore(
            total_score=total_score,
            has_action_verb=has_verb,
            has_subject=has_subject,
            appropriate_length=appropriate_length,
            has_evidence=has_evidence,
            verb_score=verb_score,
            subject_score=subject_score,
            length_score=length_score,
            evidence_score=evidence_score
        )
    
    def deduplicate_tasks(
        self, 
        ai_tasks: List[Dict], 
        pattern_tasks: List[Dict]
    ) -> List[Dict]:
        """
        Deduplicate tasks from AI and pattern matching.
        Merges similar tasks (>0.8 similarity), prefers AI-extracted.
        """
        if not pattern_tasks:
            return ai_tasks
        if not ai_tasks:
            return pattern_tasks
        
        merged_tasks = []
        used_pattern_indices = set()
        
        # For each AI task, find similar pattern tasks
        for ai_task in ai_tasks:
            ai_text = ai_task.get('text', ai_task.get('title', ''))
            best_match = None
            best_similarity = 0.0
            best_pattern_idx = None
            
            for idx, pattern_task in enumerate(pattern_tasks):
                if idx in used_pattern_indices:
                    continue
                
                pattern_text = pattern_task.get('text', pattern_task.get('title', ''))
                similarity = self._calculate_similarity(ai_text, pattern_text)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = pattern_task
                    best_pattern_idx = idx
            
            # Merge if similar enough
            if best_similarity >= self.DEDUP_SIMILARITY_THRESHOLD and best_match:
                merged_task = self._merge_tasks(ai_task, best_match, best_similarity)
                merged_tasks.append(merged_task)
                used_pattern_indices.add(best_pattern_idx)
                logger.info(f"Merged task (similarity: {best_similarity:.2f}): {ai_text[:50]}...")
            else:
                # Keep AI task as-is
                merged_tasks.append(ai_task)
        
        # Add remaining pattern tasks that weren't merged
        for idx, pattern_task in enumerate(pattern_tasks):
            if idx not in used_pattern_indices:
                merged_tasks.append(pattern_task)
        
        logger.info(f"Deduplication: {len(ai_tasks)} AI + {len(pattern_tasks)} pattern → {len(merged_tasks)} merged")
        
        return merged_tasks
    
    def _merge_tasks(
        self, 
        ai_task: Dict, 
        pattern_task: Dict, 
        similarity: float
    ) -> Dict:
        """Merge two similar tasks, preferring AI data"""
        merged = ai_task.copy()
        
        # Combine evidence from both sources
        evidence = merged.get('extraction_context', {})
        if not isinstance(evidence, dict):
            evidence = {}
        
        evidence['merged_from'] = {
            'ai_source': ai_task.get('extraction_context'),
            'pattern_source': pattern_task.get('extraction_context'),
            'similarity': similarity
        }
        merged['extraction_context'] = evidence
        
        # Use highest confidence
        ai_confidence = merged.get('confidence_score', 0.0)
        pattern_confidence = pattern_task.get('confidence_score', 0.0)
        merged['confidence_score'] = max(ai_confidence, pattern_confidence)
        
        return merged
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        # Normalize
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Lowercase, remove punctuation, extra whitespace
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# Singleton instance
_validation_engine = None

def get_validation_engine() -> ValidationEngine:
    """Get singleton validation engine instance"""
    global _validation_engine
    if _validation_engine is None:
        _validation_engine = ValidationEngine()
    return _validation_engine
