"""
DateParserService - Intelligent date parsing for task due dates

Parses temporal references from task context into concrete dates:
- "by Friday" → next Friday's date
- "tomorrow" → tomorrow's date
- "end of week" → this Friday
- "next Monday" → date of next Monday
"""

import logging
import os
from datetime import datetime, timedelta, date
from typing import Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class DateParseResult:
    """Result of date parsing with confidence"""
    success: bool
    date: Optional[date]
    confidence: float
    original_text: str
    interpretation: str
    error: Optional[str] = None


class DateParserService:
    """Service for parsing temporal references into dates"""
    
    # Day name mappings
    DAY_NAMES = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    def __init__(self):
        """Initialize date parser service"""
        # Check feature flag
        self.enabled = os.environ.get('ENABLE_DATE_PARSING', 'true').lower() == 'true'
    
    def parse_due_date(self, due_text: str) -> DateParseResult:
        """
        Parse a due date reference into a concrete date.
        
        Args:
            due_text: Text like "Friday", "tomorrow", "end of week", etc.
            
        Returns:
            DateParseResult with parsed date and confidence
        """
        if not due_text or not due_text.strip():
            return DateParseResult(
                success=False,
                date=None,
                confidence=0.0,
                original_text=due_text,
                interpretation="",
                error="Empty due date text"
            )
        
        if not self.enabled:
            return DateParseResult(
                success=False,
                date=None,
                confidence=0.0,
                original_text=due_text,
                interpretation="Date parsing disabled",
                error="Feature disabled"
            )
        
        due_text_lower = due_text.lower().strip()
        today = date.today()
        
        # Pattern 1: "tomorrow"
        if due_text_lower in ['tomorrow', 'tmr', 'tmrw']:
            result_date = today + timedelta(days=1)
            return DateParseResult(
                success=True,
                date=result_date,
                confidence=0.95,
                original_text=due_text,
                interpretation=f"Tomorrow ({result_date.strftime('%A, %B %d')})"
            )
        
        # Pattern 2: "today"
        if due_text_lower in ['today', 'now', 'asap']:
            return DateParseResult(
                success=True,
                date=today,
                confidence=0.95,
                original_text=due_text,
                interpretation=f"Today ({today.strftime('%A, %B %d')})"
            )
        
        # Pattern 3: Day names (e.g., "Friday", "next Monday")
        result = self._parse_day_name(due_text_lower, today)
        if result:
            return result
        
        # Pattern 4: Relative references (e.g., "end of week", "next week")
        result = self._parse_relative_reference(due_text_lower, today)
        if result:
            return result
        
        # Pattern 5: Specific date formats (e.g., "Dec 15", "12/15", "2024-12-15")
        result = self._parse_specific_date(due_text_lower, today)
        if result:
            return result
        
        # Pattern 6: Relative days (e.g., "in 3 days", "2 weeks from now")
        result = self._parse_relative_days(due_text_lower, today)
        if result:
            return result
        
        # Unable to parse
        return DateParseResult(
            success=False,
            date=None,
            confidence=0.0,
            original_text=due_text,
            interpretation=f"Could not parse: '{due_text}'",
            error="No matching pattern"
        )
    
    def _parse_day_name(self, text: str, today: date) -> Optional[DateParseResult]:
        """Parse day names like 'Friday', 'next Monday'"""
        # Check for "next" prefix
        is_next_week = text.startswith('next ')
        if is_next_week:
            text = text[5:]  # Remove "next "
        
        # Check for "this" prefix
        is_this_week = text.startswith('this ')
        if is_this_week:
            text = text[5:]  # Remove "this "
        
        # Find day name
        day_num = None
        for day_name, day_index in self.DAY_NAMES.items():
            if text == day_name or text.startswith(day_name + ' '):
                day_num = day_index
                break
        
        if day_num is None:
            return None
        
        # Calculate target date
        current_day = today.weekday()
        days_ahead = day_num - current_day
        
        if is_next_week:
            # Force next week
            if days_ahead <= 0:
                days_ahead += 7
            else:
                days_ahead += 7  # Even if it's later this week, go to next week
        elif is_this_week:
            # Force this week
            if days_ahead < 0:
                days_ahead += 7
        else:
            # Default: next occurrence (could be this week or next)
            if days_ahead <= 0:
                days_ahead += 7
        
        result_date = today + timedelta(days=days_ahead)
        
        prefix = "Next" if is_next_week else "This" if is_this_week else "Upcoming"
        
        return DateParseResult(
            success=True,
            date=result_date,
            confidence=0.9,
            original_text=text,
            interpretation=f"{prefix} {result_date.strftime('%A, %B %d')}"
        )
    
    def _parse_relative_reference(self, text: str, today: date) -> Optional[DateParseResult]:
        """Parse references like 'end of week', 'next week', 'end of month'"""
        # End of week (Friday)
        if 'end of week' in text or 'eow' in text or 'end of the week' in text:
            current_day = today.weekday()
            days_to_friday = (4 - current_day) % 7
            if days_to_friday == 0 and text.startswith('next'):
                days_to_friday = 7
            result_date = today + timedelta(days=days_to_friday or 7)
            return DateParseResult(
                success=True,
                date=result_date,
                confidence=0.85,
                original_text=text,
                interpretation=f"End of week ({result_date.strftime('%A, %B %d')})"
            )
        
        # Next week
        if text in ['next week', 'nxt week']:
            result_date = today + timedelta(days=7)
            return DateParseResult(
                success=True,
                date=result_date,
                confidence=0.7,
                original_text=text,
                interpretation=f"Next week ({result_date.strftime('%A, %B %d')})"
            )
        
        # End of month
        if 'end of month' in text or 'eom' in text:
            # Get last day of current month
            next_month = today.replace(day=28) + timedelta(days=4)
            result_date = next_month - timedelta(days=next_month.day)
            return DateParseResult(
                success=True,
                date=result_date,
                confidence=0.85,
                original_text=text,
                interpretation=f"End of month ({result_date.strftime('%B %d')})"
            )
        
        return None
    
    def _parse_specific_date(self, text: str, today: date) -> Optional[DateParseResult]:
        """Parse specific dates like 'Dec 15', '12/15/2024', '2024-12-15'"""
        # ISO format: YYYY-MM-DD
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
        if match:
            try:
                result_date = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                return DateParseResult(
                    success=True,
                    date=result_date,
                    confidence=0.95,
                    original_text=text,
                    interpretation=result_date.strftime('%A, %B %d, %Y')
                )
            except ValueError:
                pass
        
        # US format: MM/DD or MM/DD/YYYY
        match = re.match(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', text)
        if match:
            try:
                year = today.year
                if match.group(3):
                    year = int(match.group(3))
                    if year < 100:
                        year += 2000
                result_date = date(year, int(match.group(1)), int(match.group(2)))
                return DateParseResult(
                    success=True,
                    date=result_date,
                    confidence=0.9,
                    original_text=text,
                    interpretation=result_date.strftime('%A, %B %d, %Y')
                )
            except ValueError:
                pass
        
        return None
    
    def _parse_relative_days(self, text: str, today: date) -> Optional[DateParseResult]:
        """Parse relative days like 'in 3 days', '2 weeks from now'"""
        # Pattern: "in X days"
        match = re.match(r'in (\d+) days?', text)
        if match:
            days = int(match.group(1))
            result_date = today + timedelta(days=days)
            return DateParseResult(
                success=True,
                date=result_date,
                confidence=0.9,
                original_text=text,
                interpretation=f"In {days} days ({result_date.strftime('%A, %B %d')})"
            )
        
        # Pattern: "X weeks from now"
        match = re.match(r'(\d+) weeks? (?:from now|away)', text)
        if match:
            weeks = int(match.group(1))
            result_date = today + timedelta(weeks=weeks)
            return DateParseResult(
                success=True,
                date=result_date,
                confidence=0.85,
                original_text=text,
                interpretation=f"In {weeks} weeks ({result_date.strftime('%A, %B %d')})"
            )
        
        return None


# Singleton instance
_date_parser_service = None

def get_date_parser_service() -> DateParserService:
    """Get singleton date parser service instance"""
    global _date_parser_service
    if _date_parser_service is None:
        _date_parser_service = DateParserService()
    return _date_parser_service
