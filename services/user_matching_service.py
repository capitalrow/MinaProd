"""
UserMatchingService - Resolve speaker/owner names to user IDs

Maps names mentioned in transcripts (e.g., "Sarah", "John") to actual user IDs
or stores them as metadata when users don't exist yet.
"""

import logging
import os
from typing import Optional, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UserMatchResult:
    """Result of user matching"""
    success: bool
    user_id: Optional[int]
    user_name: str
    match_confidence: float
    match_method: str


class UserMatchingService:
    """Service for matching names to users"""
    
    def __init__(self):
        """Initialize user matching service"""
        pass
    
    def match_user(self, name_reference: str, session_id: Optional[int] = None) -> UserMatchResult:
        """
        Match a name reference to a user ID.
        
        Args:
            name_reference: Name mentioned in transcript (e.g., "Sarah", "John Smith")
            session_id: Optional session ID for context
            
        Returns:
            UserMatchResult with user_id if found, or None with name stored
        """
        if not name_reference or name_reference.strip().lower() in ['not specified', 'unknown', 'none', '']:
            return UserMatchResult(
                success=False,
                user_id=None,
                user_name="Unassigned",
                match_confidence=0.0,
                match_method="no_name_provided"
            )
        
        name_clean = name_reference.strip()
        
        # For now, return None and store the name in extraction_context
        # Future: Implement actual user lookup from database
        # TODO: Query User table for matching names (fuzzy match)
        # TODO: Consider session participants if available
        # TODO: Allow user to confirm/correct assignments via UI
        
        logger.debug(f"User matching: '{name_clean}' - storing as metadata (no user lookup yet)")
        
        return UserMatchResult(
            success=False,  # No actual user ID match yet
            user_id=None,
            user_name=name_clean,
            match_confidence=0.0,
            match_method="name_stored_only"
        )
    
    def extract_speaker_from_segment(self, segment_text: str) -> Optional[str]:
        """
        Extract speaker name from segment text if present.
        
        Example: "Sarah: Let's review the budget" → "Sarah"
        
        Args:
            segment_text: Transcript segment text
            
        Returns:
            Speaker name if found, None otherwise
        """
        import re
        
        # Pattern: "Name: text" at start of segment
        match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:\s*', segment_text)
        if match:
            return match.group(1)
        
        return None


# Singleton instance
_user_matching_service = None

def get_user_matching_service() -> UserMatchingService:
    """Get singleton user matching service instance"""
    global _user_matching_service
    if _user_matching_service is None:
        _user_matching_service = UserMatchingService()
    return _user_matching_service
