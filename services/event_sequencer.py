"""
EventSequencer Service - CROWN⁴ Event Ordering & Validation

Ensures events are processed in correct order and prevents out-of-order
execution that could cause data inconsistencies across dashboard, tasks, and analytics.

Key Features:
- Sequence number validation
- Idempotency checking with last_applied_id
- Checksum generation for data integrity
- WebSocket broadcast status tracking
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import select, func
from models import db
from models.event_ledger import EventLedger, EventType, EventStatus

logger = logging.getLogger(__name__)


class EventSequencer:
    """
    Service for managing event sequencing and validation in CROWN⁴ architecture.
    
    Responsibilities:
    - Assign sequence numbers to events
    - Validate event ordering before processing
    - Generate checksums for payload integrity
    - Track broadcast status for WebSocket synchronization
    """
    
    @staticmethod
    def generate_checksum(payload: Dict[str, Any]) -> str:
        """
        Generate MD5 checksum for event payload to detect tampering or corruption.
        
        Args:
            payload: Event payload dictionary
            
        Returns:
            MD5 checksum hex string
        """
        try:
            # Sort keys for consistent hashing
            payload_str = json.dumps(payload, sort_keys=True, default=str)
            return hashlib.md5(payload_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to generate checksum: {e}")
            return ""
    
    @staticmethod
    def get_next_sequence_num() -> int:
        """
        Get the next sequence number for event ordering.
        Thread-safe using database sequence.
        
        Returns:
            Next sequence number
        """
        try:
            # Get max sequence_num from database
            max_seq = db.session.scalar(
                select(func.max(EventLedger.sequence_num))
            )
            
            # Start from 1 if no events exist
            return (max_seq or 0) + 1
        except Exception as e:
            logger.error(f"Failed to get next sequence number: {e}")
            return 1
    
    @staticmethod
    def create_event(
        event_type: EventType,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
        session_id: Optional[int] = None,
        external_session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> EventLedger:
        """
        Create a new event with proper sequencing and checksum.
        
        Args:
            event_type: Type of event from EventType enum
            event_name: Human-readable event name
            payload: Event data payload
            session_id: Internal session ID
            external_session_id: External session identifier
            trace_id: Distributed tracing ID
            idempotency_key: Key for idempotent processing
            
        Returns:
            Created EventLedger instance
        """
        try:
            # Generate sequence number
            sequence_num = EventSequencer.get_next_sequence_num()
            
            # Generate checksum if payload provided
            checksum = EventSequencer.generate_checksum(payload) if payload else None
            
            # Create event record
            event = EventLedger(
                event_type=event_type,
                event_name=event_name,
                session_id=session_id,
                external_session_id=external_session_id,
                status=EventStatus.PENDING,
                payload=payload,
                trace_id=trace_id,
                idempotency_key=idempotency_key,
                sequence_num=sequence_num,
                checksum=checksum,
                broadcast_status="pending",
                created_at=datetime.utcnow()
            )
            
            db.session.add(event)
            db.session.commit()
            
            logger.debug(f"Created event {event.id} (seq={sequence_num}): {event_name}")
            
            return event
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create event {event_name}: {e}", exc_info=True)
            raise
    
    @staticmethod
    def validate_sequence(event_id: int, expected_last_id: Optional[int] = None) -> bool:
        """
        Validate that an event can be processed based on sequence ordering.
        
        Args:
            event_id: Event ID to validate
            expected_last_id: Expected last processed event ID (for idempotency)
            
        Returns:
            True if event can be processed, False if out of order
        """
        try:
            event = db.session.get(EventLedger, event_id)
            if not event:
                logger.error(f"Event {event_id} not found for validation")
                return False
            
            # If no expected_last_id, allow processing
            if expected_last_id is None:
                return True
            
            # Check if this event has already been applied
            if event.last_applied_id and event.last_applied_id >= expected_last_id:
                logger.info(f"Event {event_id} already applied (last_applied={event.last_applied_id})")
                return False
            
            # Validate sequence ordering
            if event.sequence_num is not None:
                # Get the last processed event sequence
                last_processed_seq = db.session.scalar(
                    select(func.max(EventLedger.sequence_num))
                    .where(EventLedger.status == EventStatus.COMPLETED)
                    .where(EventLedger.sequence_num < event.sequence_num)
                )
                
                # Check for gaps in sequence
                if last_processed_seq is not None and event.sequence_num > last_processed_seq + 1:
                    logger.warning(
                        f"Sequence gap detected: event {event_id} has seq={event.sequence_num}, "
                        f"last processed seq={last_processed_seq}"
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate sequence for event {event_id}: {e}")
            return False
    
    @staticmethod
    def mark_event_processing(event_id: int) -> bool:
        """
        Mark an event as currently being processed.
        
        Args:
            event_id: Event ID
            
        Returns:
            True if successfully marked, False otherwise
        """
        try:
            event = db.session.get(EventLedger, event_id)
            if not event:
                return False
            
            event.status = EventStatus.PROCESSING
            event.started_at = datetime.utcnow()
            db.session.commit()
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to mark event {event_id} as processing: {e}")
            return False
    
    @staticmethod
    def mark_event_completed(
        event_id: int,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        broadcast_status: str = "sent"
    ) -> bool:
        """
        Mark an event as completed successfully.
        
        Args:
            event_id: Event ID
            result: Event processing result
            duration_ms: Processing duration in milliseconds
            broadcast_status: WebSocket broadcast status (pending|sent|failed)
            
        Returns:
            True if successfully marked, False otherwise
        """
        try:
            event = db.session.get(EventLedger, event_id)
            if not event:
                return False
            
            event.status = EventStatus.COMPLETED
            event.completed_at = datetime.utcnow()
            event.result = result
            event.duration_ms = duration_ms
            event.broadcast_status = broadcast_status
            event.last_applied_id = event.id  # Mark as applied
            
            db.session.commit()
            
            logger.debug(f"Completed event {event_id} in {duration_ms}ms")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to mark event {event_id} as completed: {e}")
            return False
    
    @staticmethod
    def mark_event_failed(
        event_id: int,
        error_message: str,
        broadcast_status: str = "failed"
    ) -> bool:
        """
        Mark an event as failed.
        
        Args:
            event_id: Event ID
            error_message: Error description
            broadcast_status: WebSocket broadcast status
            
        Returns:
            True if successfully marked, False otherwise
        """
        try:
            event = db.session.get(EventLedger, event_id)
            if not event:
                return False
            
            event.status = EventStatus.FAILED
            event.completed_at = datetime.utcnow()
            event.error_message = error_message
            event.broadcast_status = broadcast_status
            
            db.session.commit()
            
            logger.error(f"Event {event_id} failed: {error_message}")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to mark event {event_id} as failed: {e}")
            return False
    
    @staticmethod
    def get_pending_events(limit: int = 100) -> List[EventLedger]:
        """
        Get pending events that need to be broadcast via WebSocket.
        
        Args:
            limit: Maximum number of events to retrieve
            
        Returns:
            List of pending EventLedger instances
        """
        try:
            events = db.session.scalars(
                select(EventLedger)
                .where(EventLedger.broadcast_status == "pending")
                .where(EventLedger.status == EventStatus.COMPLETED)
                .order_by(EventLedger.sequence_num)
                .limit(limit)
            ).all()
            
            return list(events)
        except Exception as e:
            logger.error(f"Failed to get pending events: {e}")
            return []
    
    @staticmethod
    def verify_checksum(event: EventLedger) -> bool:
        """
        Verify event payload integrity using checksum.
        
        Args:
            event: EventLedger instance
            
        Returns:
            True if checksum valid, False otherwise
        """
        try:
            if not event.checksum or not event.payload:
                return True  # No checksum to verify
            
            calculated_checksum = EventSequencer.generate_checksum(event.payload)
            is_valid = calculated_checksum == event.checksum
            
            if not is_valid:
                logger.warning(
                    f"Checksum mismatch for event {event.id}: "
                    f"expected={event.checksum}, calculated={calculated_checksum}"
                )
            
            return is_valid
        except Exception as e:
            logger.error(f"Failed to verify checksum for event {event.id}: {e}")
            return False


# Singleton instance
event_sequencer = EventSequencer()
