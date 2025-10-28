#!/usr/bin/env python3
"""
Backfill script to create Meeting records for completed Sessions without meetings.
This fixes the broken data pipeline and ensures all sessions appear on the dashboard.
"""

import logging
from sqlalchemy import select
from app import app, db
from models.session import Session
from services.meeting_lifecycle_service import MeetingLifecycleService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backfill_orphaned_sessions():
    """
    Find all completed sessions without meetings and create meetings for them.
    """
    with app.app_context():
        try:
            orphaned_sessions = db.session.scalars(
                select(Session).where(
                    Session.status == 'completed',
                    Session.meeting_id.is_(None)
                )
            ).all()
            
            logger.info(f"Found {len(orphaned_sessions)} completed sessions without meetings")
            
            created_count = 0
            failed_count = 0
            
            for session in orphaned_sessions:
                try:
                    logger.info(f"Creating meeting for Session {session.id} ({session.external_id})")
                    meeting = MeetingLifecycleService.create_meeting_from_session(session.id)
                    
                    if meeting:
                        created_count += 1
                        logger.info(f"✅ Created Meeting {meeting.id} from Session {session.id}")
                    else:
                        failed_count += 1
                        logger.warning(f"❌ Failed to create meeting for Session {session.id}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error creating meeting for Session {session.id}: {e}", exc_info=True)
            
            logger.info("=" * 60)
            logger.info(f"Backfill Complete:")
            logger.info(f"  - Total orphaned sessions: {len(orphaned_sessions)}")
            logger.info(f"  - Meetings created: {created_count}")
            logger.info(f"  - Failed: {failed_count}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Backfill script failed: {e}", exc_info=True)


if __name__ == '__main__':
    backfill_orphaned_sessions()
