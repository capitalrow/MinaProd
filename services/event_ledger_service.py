"""
EventLedger Service - Manage event tracking for CROWN+ Event Sequencing

Handles creation, updating, and querying of events for auditability and replay.
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_
from models import db
from models.event_ledger import EventLedger, EventType, EventStatus

logger = logging.getLogger(__name__)


class EventLedgerService:
    """Service for managing event ledger entries"""
    
    @staticmethod
    def log_event(
        event_type: EventType,
        session_id: Optional[int] = None,
        external_session_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        parent_event_id: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> EventLedger:
        """
        Log a new event to the ledger.
        
        Args:
            event_type: Type of event (from EventType enum)
            session_id: Database session ID
            external_session_id: External session identifier (trace_id)
            payload: Event data/context
            trace_id: Distributed tracing ID
            parent_event_id: ID of parent event (for event chains)
            idempotency_key: Key for idempotent operations
            
        Returns:
            Created EventLedger instance
        """
        try:
            # Check for existing event with same idempotency key
            if idempotency_key:
                existing = EventLedgerService.get_by_idempotency_key(idempotency_key)
                if existing:
                    logger.info(f"Event already exists with idempotency_key={idempotency_key}, returning existing")
                    return existing
            
            # Generate trace_id if not provided
            if not trace_id and external_session_id:
                trace_id = external_session_id
            elif not trace_id:
                trace_id = str(uuid.uuid4())
            
            # Create event name from type
            event_name = event_type.value.replace('_', ' ').title()
            
            event = EventLedger(
                event_type=event_type,
                event_name=event_name,
                session_id=session_id,
                external_session_id=external_session_id,
                status=EventStatus.PENDING,
                payload=payload or {},
                trace_id=trace_id,
                parent_event_id=parent_event_id,
                idempotency_key=idempotency_key,
                created_at=datetime.utcnow()
            )
            
            db.session.add(event)
            db.session.commit()
            
            logger.info(f"✅ Event logged: {event_type.value} (id={event.id}, session={external_session_id})")
            return event
            
        except Exception as e:
            logger.error(f"Failed to log event {event_type.value}: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def start_event(event: EventLedger) -> EventLedger:
        """Mark event as processing"""
        try:
            event.status = EventStatus.PROCESSING
            event.started_at = datetime.utcnow()
            db.session.commit()
            return event
        except Exception as e:
            logger.error(f"Failed to start event {event.id}: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def complete_event(
        event: EventLedger,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> EventLedger:
        """Mark event as completed successfully"""
        try:
            event.status = EventStatus.COMPLETED
            event.completed_at = datetime.utcnow()
            event.result = result or {}
            
            # Calculate duration if not provided
            if duration_ms is not None:
                event.duration_ms = duration_ms
            elif event.started_at:
                delta = event.completed_at - event.started_at
                event.duration_ms = delta.total_seconds() * 1000
            
            db.session.commit()
            logger.info(f"✅ Event completed: {event.event_type.value} (duration={event.duration_ms}ms)")
            return event
        except Exception as e:
            logger.error(f"Failed to complete event {event.id}: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def fail_event(
        event: EventLedger,
        error_message: str,
        duration_ms: Optional[float] = None
    ) -> EventLedger:
        """Mark event as failed"""
        try:
            event.status = EventStatus.FAILED
            event.completed_at = datetime.utcnow()
            event.error_message = error_message
            
            # Calculate duration if not provided
            if duration_ms is not None:
                event.duration_ms = duration_ms
            elif event.started_at:
                delta = event.completed_at - event.started_at
                event.duration_ms = delta.total_seconds() * 1000
            
            db.session.commit()
            logger.error(f"❌ Event failed: {event.event_type.value} - {error_message}")
            return event
        except Exception as e:
            logger.error(f"Failed to mark event {event.id} as failed: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def skip_event(event: EventLedger, reason: str) -> EventLedger:
        """Mark event as skipped"""
        try:
            event.status = EventStatus.SKIPPED
            event.completed_at = datetime.utcnow()
            event.error_message = f"Skipped: {reason}"
            db.session.commit()
            logger.info(f"⏭️  Event skipped: {event.event_type.value} - {reason}")
            return event
        except Exception as e:
            logger.error(f"Failed to skip event {event.id}: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_session_events(
        session_id: Optional[int] = None,
        external_session_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        status: Optional[EventStatus] = None
    ) -> List[EventLedger]:
        """Get all events for a session"""
        try:
            stmt = select(EventLedger)
            
            conditions = []
            if session_id:
                conditions.append(EventLedger.session_id == session_id)
            if external_session_id:
                conditions.append(EventLedger.external_session_id == external_session_id)
            if event_type:
                conditions.append(EventLedger.event_type == event_type)
            if status:
                conditions.append(EventLedger.status == status)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(EventLedger.created_at.asc())
            return list(db.session.execute(stmt).scalars().all())
        except Exception as e:
            logger.error(f"Failed to get session events: {e}")
            return []
    
    @staticmethod
    def get_by_idempotency_key(idempotency_key: str) -> Optional[EventLedger]:
        """Get event by idempotency key"""
        try:
            stmt = select(EventLedger).where(EventLedger.idempotency_key == idempotency_key)
            return db.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get event by idempotency key: {e}")
            return None
    
    @staticmethod
    def get_last_event(
        session_id: Optional[int] = None,
        external_session_id: Optional[str] = None,
        event_type: Optional[EventType] = None
    ) -> Optional[EventLedger]:
        """Get the most recent event for a session"""
        try:
            stmt = select(EventLedger)
            
            conditions = []
            if session_id:
                conditions.append(EventLedger.session_id == session_id)
            if external_session_id:
                conditions.append(EventLedger.external_session_id == external_session_id)
            if event_type:
                conditions.append(EventLedger.event_type == event_type)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(EventLedger.created_at.desc()).limit(1)
            return db.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get last event: {e}")
            return None
    
    @staticmethod
    def get_event_timeline(external_session_id: str) -> List[Dict[str, Any]]:
        """
        Get complete event timeline for a session in chronological order.
        Returns user-friendly format for UI display.
        """
        events = EventLedgerService.get_session_events(external_session_id=external_session_id)
        
        timeline = []
        for event in events:
            timeline.append({
                'event_type': event.event_type.value,
                'event_name': event.event_name,
                'status': event.status.value,
                'timestamp': event.created_at.isoformat() if event.created_at else None,
                'duration_ms': event.duration_ms,
                'error': event.error_message if event.is_failed else None
            })
        
        return timeline
    
    @staticmethod
    def get_processing_stats(external_session_id: str) -> Dict[str, Any]:
        """Get processing statistics for a session"""
        events = EventLedgerService.get_session_events(external_session_id=external_session_id)
        
        total_events = len(events)
        completed = sum(1 for e in events if e.status == EventStatus.COMPLETED)
        failed = sum(1 for e in events if e.status == EventStatus.FAILED)
        processing = sum(1 for e in events if e.status == EventStatus.PROCESSING)
        
        total_duration = sum(e.duration_ms for e in events if e.duration_ms)
        
        return {
            'total_events': total_events,
            'completed': completed,
            'failed': failed,
            'processing': processing,
            'total_duration_ms': total_duration,
            'total_duration_seconds': total_duration / 1000 if total_duration else 0
        }
