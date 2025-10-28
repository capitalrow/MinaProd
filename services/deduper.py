"""
Deduper Service - CROWN⁴.5 Duplicate Task Detection & Prevention

Prevents duplicate AI-extracted tasks using content-based origin_hash comparison.
Implements fuzzy matching and semantic similarity for robust deduplication.

Key Features:
- SHA-256 origin_hash generation from task content
- Fuzzy matching for similar task titles
- Duplicate detection before task creation
- Configurable similarity thresholds
- Deduplication workflow integration
"""

import logging
import hashlib
import re
from typing import Optional, Dict, Any, List, Tuple
from difflib import SequenceMatcher
from sqlalchemy import select
from models import db
from models.task import Task

logger = logging.getLogger(__name__)


class Deduper:
    """
    Service for detecting and preventing duplicate AI-extracted tasks.
    
    Responsibilities:
    - Generate origin_hash from task content
    - Detect exact duplicates via origin_hash comparison
    - Detect near-duplicates using fuzzy matching
    - Provide deduplication workflow for task creation
    - Track deduplication metrics
    """
    
    # Similarity thresholds
    EXACT_MATCH_THRESHOLD = 1.0  # Exact hash match
    HIGH_SIMILARITY_THRESHOLD = 0.90  # Very similar (likely duplicate)
    MODERATE_SIMILARITY_THRESHOLD = 0.75  # Possibly duplicate
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for consistent hash generation.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text (lowercase, trimmed, no extra whitespace)
        """
        try:
            # Convert to lowercase
            text = text.lower().strip()
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove common punctuation that doesn't affect meaning
            text = re.sub(r'[.,!?;:]', '', text)
            
            return text
        except Exception as e:
            logger.error(f"Failed to normalize text: {e}")
            return text
    
    @staticmethod
    def generate_origin_hash(
        title: str,
        description: Optional[str] = None,
        assigned_to_id: Optional[int] = None
    ) -> str:
        """
        Generate SHA-256 origin_hash for task deduplication.
        
        The hash is based on normalized title + description + assignee
        to uniquely identify task content regardless of formatting.
        
        Args:
            title: Task title
            description: Task description (optional)
            assigned_to_id: Assigned user ID (optional)
            
        Returns:
            SHA-256 hash hex string (64 characters)
        """
        try:
            # Normalize title
            normalized_title = Deduper.normalize_text(title)
            
            # Normalize description if provided
            normalized_desc = Deduper.normalize_text(description) if description else ""
            
            # Combine components
            hash_input = f"{normalized_title}|{normalized_desc}"
            
            # Include assignee if specified (same task for different people is not a duplicate)
            if assigned_to_id:
                hash_input += f"|{assigned_to_id}"
            
            # Generate SHA-256 hash
            return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to generate origin_hash: {e}")
            # Return hash of raw title as fallback
            return hashlib.sha256(title.encode('utf-8')).hexdigest()
    
    @staticmethod
    def calculate_similarity(text_a: str, text_b: str) -> float:
        """
        Calculate similarity ratio between two text strings.
        
        Uses SequenceMatcher for fuzzy string matching.
        
        Args:
            text_a: First text
            text_b: Second text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        try:
            # Normalize both texts
            norm_a = Deduper.normalize_text(text_a)
            norm_b = Deduper.normalize_text(text_b)
            
            # Calculate similarity using SequenceMatcher
            similarity = SequenceMatcher(None, norm_a, norm_b).ratio()
            
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    @staticmethod
    def find_exact_duplicate(
        origin_hash: str,
        session_id: Optional[int] = None,
        meeting_id: Optional[int] = None
    ) -> Optional[Task]:
        """
        Find exact duplicate task by origin_hash.
        
        Args:
            origin_hash: Origin hash to search for
            session_id: Limit search to specific session (optional)
            meeting_id: Limit search to specific meeting (optional)
            
        Returns:
            Existing Task if found, None otherwise
        """
        try:
            # Build query
            query = select(Task).where(Task.origin_hash == origin_hash)
            
            # Add session filter if provided
            if session_id:
                query = query.where(Task.session_id == session_id)
            
            # Add meeting filter if provided
            if meeting_id:
                query = query.where(Task.meeting_id == meeting_id)
            
            # Execute query
            existing_task = db.session.scalar(query)
            
            if existing_task:
                logger.info(
                    f"Found exact duplicate: task {existing_task.id} "
                    f"(hash={origin_hash[:8]}...)"
                )
            
            return existing_task
            
        except Exception as e:
            logger.error(f"Failed to find exact duplicate: {e}")
            return None
    
    @staticmethod
    def find_similar_tasks(
        title: str,
        description: Optional[str] = None,
        session_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Tuple[Task, float]]:
        """
        Find similar tasks using fuzzy matching.
        
        Args:
            title: Task title to match
            description: Task description (optional)
            session_id: Limit search to specific session (optional)
            meeting_id: Limit search to specific meeting (optional)
            limit: Maximum number of similar tasks to return
            
        Returns:
            List of (Task, similarity_score) tuples, sorted by similarity (highest first)
        """
        try:
            # Build query for candidate tasks
            query = select(Task).where(Task.extracted_by_ai == True)
            
            if session_id:
                query = query.where(Task.session_id == session_id)
            if meeting_id:
                query = query.where(Task.meeting_id == meeting_id)
            
            # Get candidate tasks
            candidates = db.session.scalars(query.limit(100)).all()
            
            # Calculate similarity for each candidate
            similar_tasks = []
            for task in candidates:
                # Calculate title similarity
                title_similarity = Deduper.calculate_similarity(title, task.title)
                
                # Calculate description similarity if both have descriptions
                desc_similarity = 0.0
                if description and task.description:
                    desc_similarity = Deduper.calculate_similarity(description, task.description)
                
                # Combined similarity (weighted: 70% title, 30% description)
                combined_similarity = (title_similarity * 0.7) + (desc_similarity * 0.3)
                
                # Only include if above minimum threshold
                if combined_similarity >= Deduper.MODERATE_SIMILARITY_THRESHOLD:
                    similar_tasks.append((task, combined_similarity))
            
            # Sort by similarity (highest first) and limit results
            similar_tasks.sort(key=lambda x: x[1], reverse=True)
            similar_tasks = similar_tasks[:limit]
            
            if similar_tasks:
                logger.info(
                    f"Found {len(similar_tasks)} similar tasks "
                    f"(best match: {similar_tasks[0][1]:.2f} similarity)"
                )
            
            return similar_tasks
            
        except Exception as e:
            logger.error(f"Failed to find similar tasks: {e}")
            return []
    
    @staticmethod
    def check_duplicate(
        title: str,
        description: Optional[str] = None,
        assigned_to_id: Optional[int] = None,
        session_id: Optional[int] = None,
        meeting_id: Optional[int] = None,
        use_fuzzy_matching: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive duplicate check before task creation.
        
        Performs both exact hash matching and fuzzy similarity matching.
        
        Args:
            title: Task title
            description: Task description (optional)
            assigned_to_id: Assigned user ID (optional)
            session_id: Session ID (optional)
            meeting_id: Meeting ID (optional)
            use_fuzzy_matching: Enable fuzzy matching for near-duplicates
            
        Returns:
            Dictionary with duplicate check results:
            {
                'is_duplicate': bool,
                'duplicate_type': 'exact' | 'similar' | 'none',
                'confidence': float (0.0 to 1.0),
                'existing_task': Task or None,
                'similar_tasks': List[(Task, similarity)],
                'origin_hash': str,
                'recommendation': str
            }
        """
        try:
            # Generate origin hash
            origin_hash = Deduper.generate_origin_hash(title, description, assigned_to_id)
            
            # Check for exact duplicate
            exact_duplicate = Deduper.find_exact_duplicate(
                origin_hash,
                session_id=session_id,
                meeting_id=meeting_id
            )
            
            if exact_duplicate:
                return {
                    'is_duplicate': True,
                    'duplicate_type': 'exact',
                    'confidence': 1.0,
                    'existing_task': exact_duplicate,
                    'similar_tasks': [],
                    'origin_hash': origin_hash,
                    'recommendation': 'Skip creation - exact duplicate exists'
                }
            
            # Check for similar tasks if fuzzy matching enabled
            similar_tasks = []
            if use_fuzzy_matching:
                similar_tasks = Deduper.find_similar_tasks(
                    title,
                    description=description,
                    session_id=session_id,
                    meeting_id=meeting_id
                )
            
            # Determine if we have a high-confidence near-duplicate
            if similar_tasks and similar_tasks[0][1] >= Deduper.HIGH_SIMILARITY_THRESHOLD:
                return {
                    'is_duplicate': True,
                    'duplicate_type': 'similar',
                    'confidence': similar_tasks[0][1],
                    'existing_task': similar_tasks[0][0],
                    'similar_tasks': similar_tasks,
                    'origin_hash': origin_hash,
                    'recommendation': f'Likely duplicate - {similar_tasks[0][1]:.0%} similar to existing task'
                }
            
            # No duplicate found
            return {
                'is_duplicate': False,
                'duplicate_type': 'none',
                'confidence': 0.0,
                'existing_task': None,
                'similar_tasks': similar_tasks,
                'origin_hash': origin_hash,
                'recommendation': 'OK to create - no duplicates detected'
            }
            
        except Exception as e:
            logger.error(f"Failed to check duplicate: {e}")
            # Return safe default (don't block creation on error)
            return {
                'is_duplicate': False,
                'duplicate_type': 'error',
                'confidence': 0.0,
                'existing_task': None,
                'similar_tasks': [],
                'origin_hash': '',
                'recommendation': 'Error during duplicate check - allowing creation'
            }
    
    @staticmethod
    def merge_duplicate_metadata(
        existing_task: Task,
        new_task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge metadata from duplicate detection into existing task.
        
        When a duplicate is detected, this updates the existing task
        with additional context from the new occurrence.
        
        Args:
            existing_task: Existing task
            new_task_data: Data from newly detected duplicate
            
        Returns:
            Updated metadata to append to existing task
        """
        try:
            # Build updated extraction context
            updated_context = existing_task.extraction_context or {}
            
            # Track duplicate occurrences
            if 'duplicate_occurrences' not in updated_context:
                updated_context['duplicate_occurrences'] = []
            
            # Add new occurrence
            updated_context['duplicate_occurrences'].append({
                'timestamp': new_task_data.get('detected_at'),
                'session_id': new_task_data.get('session_id'),
                'transcript_span': new_task_data.get('transcript_span'),
                'confidence_score': new_task_data.get('confidence_score')
            })
            
            # Increment confidence if task mentioned multiple times
            if existing_task.confidence_score and new_task_data.get('confidence_score'):
                # Average confidences with slight boost for reinforcement
                avg_confidence = (existing_task.confidence_score + new_task_data['confidence_score']) / 2
                boosted_confidence = min(1.0, avg_confidence * 1.1)  # 10% boost
                updated_context['boosted_confidence'] = boosted_confidence
            
            logger.info(
                f"Merged duplicate metadata for task {existing_task.id} "
                f"({len(updated_context['duplicate_occurrences'])} occurrences)"
            )
            
            return updated_context
            
        except Exception as e:
            logger.error(f"Failed to merge duplicate metadata: {e}")
            return existing_task.extraction_context or {}


# Singleton instance
deduper = Deduper()
