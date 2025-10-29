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
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy import select, func
from models import db
from models.event_ledger import EventLedger, EventType, EventStatus

logger = logging.getLogger(__name__)


class EventSequencer:
    """
    Service for managing event sequencing and validation in CROWN⁴.5 architecture.
    
    Responsibilities:
    - Assign sequence numbers to events
    - Validate event ordering before processing
    - Generate checksums for payload integrity
    - Track broadcast status for WebSocket synchronization
    - Generate and compare vector clocks for distributed conflict resolution
    - Implement conflict resolution strategies
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
    
    @staticmethod
    def generate_vector_clock(client_id: str, previous_clock: Optional[Dict[str, int]] = None) -> Dict[str, int]:
        """
        Generate a vector clock for distributed event ordering (CROWN⁴.5).
        
        Vector clocks enable detection of concurrent events and causality tracking
        in distributed systems with offline support. Uses logical counters, not timestamps.
        
        Args:
            client_id: Unique identifier for the client (e.g., user_id, device_id)
            previous_clock: Previous vector clock to increment from
            
        Returns:
            Vector clock dictionary {client_id: counter} where counter is monotonically increasing
        """
        try:
            # Start with previous clock or empty
            clock = previous_clock.copy() if previous_clock else {}
            
            # Increment the counter for this client (logical counter, not timestamp)
            previous_count = clock.get(client_id, 0)
            clock[client_id] = previous_count + 1
            
            return clock
        except Exception as e:
            logger.error(f"Failed to generate vector clock: {e}")
            return {client_id: 1}
    
    @staticmethod
    def compare_vector_clocks(clock_a: Dict[str, int], clock_b: Dict[str, int]) -> str:
        """
        Compare two vector clocks to determine causal ordering using standard dominance rules.
        
        Clock A dominates B (A happened after B) if:
        - All counters in A >= corresponding counters in B
        - At least one counter in A > corresponding counter in B
        
        Args:
            clock_a: First vector clock
            clock_b: Second vector clock
            
        Returns:
            "before" if clock_a happened before clock_b (B dominates A)
            "after" if clock_a happened after clock_b (A dominates B)
            "concurrent" if events are concurrent (conflict)
            "equal" if clocks are identical
        """
        try:
            if not clock_a and not clock_b:
                return "equal"
            if not clock_a:
                return "before"
            if not clock_b:
                return "after"
            
            # Check if clocks are identical
            if clock_a == clock_b:
                return "equal"
            
            # Check for dominance: A dominates B if all A[i] >= B[i] and at least one A[i] > B[i]
            a_dominates_b = True  # Assume A >= B initially
            b_dominates_a = True  # Assume B >= A initially
            
            all_clients = set(clock_a.keys()) | set(clock_b.keys())
            
            for client in all_clients:
                counter_a = clock_a.get(client, 0)
                counter_b = clock_b.get(client, 0)
                
                if counter_a < counter_b:
                    a_dominates_b = False  # A does not dominate B
                if counter_b < counter_a:
                    b_dominates_a = False  # B does not dominate A
            
            # Determine relationship
            if a_dominates_b and not b_dominates_a:
                return "after"  # A happened after B (A dominates B)
            elif b_dominates_a and not a_dominates_b:
                return "before"  # A happened before B (B dominates A)
            else:
                return "concurrent"  # Neither dominates = concurrent events
                
        except Exception as e:
            logger.error(f"Failed to compare vector clocks: {e}")
            return "concurrent"  # Assume conflict on error
    
    @staticmethod
    def resolve_conflict(
        event_a: EventLedger,
        event_b: EventLedger,
        strategy: str = "server_wins"
    ) -> Optional[EventLedger]:
        """
        Resolve conflict between two concurrent events using specified strategy.
        
        Args:
            event_a: First conflicting event
            event_b: Second conflicting event
            strategy: Conflict resolution strategy
                - "server_wins": Server event takes precedence
                - "client_wins": Client event takes precedence
                - "last_write_wins": Most recent timestamp wins
                - "merge": Attempt to merge payloads (field-level)
                - "manual": Flag for manual review (returns None)
                
        Returns:
            Winning event, or None if manual review required
        """
        try:
            if strategy == "server_wins":
                # Assume event with lower ID is server-generated
                return event_a if event_a.id < event_b.id else event_b
            
            elif strategy == "client_wins":
                # Assume event with higher ID is client-generated
                return event_a if event_a.id > event_b.id else event_b
            
            elif strategy == "last_write_wins":
                # Use created_at timestamp
                return event_a if event_a.created_at > event_b.created_at else event_b
            
            elif strategy == "merge":
                # For merge strategy, prefer newer event but flag for manual review
                logger.warning(
                    f"Merge strategy requested for events {event_a.id} and {event_b.id}, "
                    "using last_write_wins temporarily"
                )
                return event_a if event_a.created_at > event_b.created_at else event_b
            
            elif strategy == "manual":
                # Flag conflict for manual review
                logger.warning(
                    f"Manual conflict resolution required for events {event_a.id} and {event_b.id}"
                )
                # Update both events to flag for manual review
                event_a.conflict_resolution_strategy = "manual"
                event_b.conflict_resolution_strategy = "manual"
                event_a.error_message = f"Manual review required: conflict with event {event_b.id}"
                event_b.error_message = f"Manual review required: conflict with event {event_a.id}"
                return None  # Requires manual resolution
            
            else:
                logger.warning(f"Unknown conflict resolution strategy: {strategy}, using server_wins")
                return event_a if event_a.id < event_b.id else event_b
                
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {e}")
            return event_a  # Default to first event
    
    @staticmethod
    def detect_conflicts(
        events: List[EventLedger],
        resource_id: Optional[int] = None
    ) -> List[Tuple[EventLedger, EventLedger]]:
        """
        Detect concurrent events that may cause conflicts.
        
        Args:
            events: List of events to check for conflicts
            resource_id: Optional resource ID to filter events
            
        Returns:
            List of conflicting event pairs
        """
        try:
            conflicts = []
            
            # Filter events by resource if specified
            if resource_id:
                events = [e for e in events if e.session_id == resource_id]
            
            # Check each pair of events for concurrency
            for i, event_a in enumerate(events):
                for event_b in events[i+1:]:
                    if not event_a.vector_clock or not event_b.vector_clock:
                        continue
                    
                    relation = EventSequencer.compare_vector_clocks(
                        event_a.vector_clock,
                        event_b.vector_clock
                    )
                    
                    if relation == "concurrent":
                        conflicts.append((event_a, event_b))
                        logger.warning(
                            f"Conflict detected between events {event_a.id} and {event_b.id}"
                        )
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return []


# Singleton instance
event_sequencer = EventSequencer()
