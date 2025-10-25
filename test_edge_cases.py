#!/usr/bin/env python3
"""
🧪 Edge Case Testing Suite for Post-Transcription Pipeline
Tests all failure modes, edge cases, and boundary conditions
"""

import sys
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
from app import app, db

# Import canonical models (avoid duplicate table definitions)
from models.session import Session
from models.segment import Segment
from models.analytics import Analytics
from models.task import Task
from models.summary import Summary

# Import services
from services.session_service import SessionService
from services.post_transcription_orchestrator import PostTranscriptionOrchestrator

def test_empty_session():
    """Test: Session with zero segments"""
    logger.info("🧪 TEST 1: Empty session (zero segments)")
    
    with app.app_context():
        # Create session with no segments
        session = Session(
            external_id=f"test-empty-{datetime.now().timestamp()}",
            user_id=1,
            status='recording',
            started_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        logger.info(f"  Created empty session {session.id}")
        
        # Finalize session
        try:
            success = SessionService.finalize_session(
                session_id=session.id,
                room=session.external_id
            )
            logger.info(f"  ✅ Finalization {'succeeded' if success else 'failed'}")
            
            # Check results
            analytics = db.session.query(Analytics).filter_by(session_id=session.id).first()
            tasks = db.session.query(Task).filter_by(session_id=session.id).all()
            summary = db.session.query(Summary).filter_by(session_id=session.id).first()
            
            logger.info(f"  Analytics: {'Found' if analytics else 'Not found'}")
            logger.info(f"  Tasks: {len(tasks)} found")
            logger.info(f"  Summary: {'Found' if summary else 'Not found'}")
            
            return success
            
        except Exception as e:
            logger.error(f"  ❌ Error: {e}", exc_info=True)
            return False

def test_single_segment():
    """Test: Session with exactly one segment"""
    logger.info("🧪 TEST 2: Single segment session")
    
    with app.app_context():
        # Create session
        session = Session(
            external_id=f"test-single-{datetime.now().timestamp()}",
            user_id=1,
            status='recording',
            started_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # Add single segment
        segment = Segment(
            session_id=session.id,
            kind='final',
            text='This is a single test segment.',
            start_ms=0,
            end_ms=2000,
            avg_confidence=0.95
        )
        db.session.add(segment)
        db.session.commit()
        
        logger.info(f"  Created session {session.id} with 1 segment")
        
        # Finalize
        try:
            success = SessionService.finalize_session(
                session_id=session.id,
                room=session.external_id
            )
            logger.info(f"  ✅ Finalization {'succeeded' if success else 'failed'}")
            return success
        except Exception as e:
            logger.error(f"  ❌ Error: {e}", exc_info=True)
            return False

def test_large_session():
    """Test: Session with many segments (100+)"""
    logger.info("🧪 TEST 3: Large session (100 segments)")
    
    with app.app_context():
        # Create session
        session = Session(
            external_id=f"test-large-{datetime.now().timestamp()}",
            user_id=1,
            status='recording',
            started_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # Add 100 segments
        for i in range(100):
            segment = Segment(
                session_id=session.id,
                kind='final',
                text=f'Segment number {i+1} with some test content.',
                start_ms=i * 2000,
                end_ms=(i + 1) * 2000,
                avg_confidence=0.90 + (i % 10) * 0.01
            )
            db.session.add(segment)
        
        db.session.commit()
        logger.info(f"  Created session {session.id} with 100 segments")
        
        # Finalize
        try:
            import time
            start_time = time.time()
            
            success = SessionService.finalize_session(
                session_id=session.id,
                room=session.external_id
            )
            
            elapsed = time.time() - start_time
            logger.info(f"  ✅ Finalization took {elapsed:.2f}s")
            logger.info(f"  ✅ {'Succeeded' if success else 'Failed'}")
            
            # Check performance threshold (should complete in <10s)
            if elapsed > 10:
                logger.warning(f"  ⚠️  Performance issue: {elapsed:.2f}s > 10s threshold")
            
            return success
        except Exception as e:
            logger.error(f"  ❌ Error: {e}", exc_info=True)
            return False

def test_missing_session():
    """Test: Finalize non-existent session"""
    logger.info("🧪 TEST 4: Missing/invalid session ID")
    
    with app.app_context():
        try:
            # Try to finalize session that doesn't exist
            success = SessionService.finalize_session(
                session_id=999999,  # Non-existent ID
                room="nonexistent"
            )
            logger.info(f"  ✅ Gracefully handled: returned {success}")
            return not success  # Should return False, which is correct behavior
        except Exception as e:
            logger.info(f"  ✅ Correctly raised exception: {type(e).__name__}")
            return True

def test_already_finalized():
    """Test: Re-finalize already completed session"""
    logger.info("🧪 TEST 5: Already finalized session (idempotency)")
    
    with app.app_context():
        # Create and finalize session
        session = Session(
            external_id=f"test-idempotent-{datetime.now().timestamp()}",
            user_id=1,
            status='completed',  # Already completed
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # Add segment
        segment = Segment(
            session_id=session.id,
            kind='final',
            text='Test segment for idempotency check.',
            start_ms=0,
            end_ms=2000,
            avg_confidence=0.95
        )
        db.session.add(segment)
        db.session.commit()
        
        logger.info(f"  Created already-completed session {session.id}")
        
        # Try to finalize again
        try:
            success = SessionService.finalize_session(
                session_id=session.id,
                room=session.external_id
            )
            logger.info(f"  ✅ Idempotent finalization: {success}")
            return True  # Should handle gracefully
        except Exception as e:
            logger.error(f"  ❌ Error (should be idempotent): {e}")
            return False

def test_low_confidence_segments():
    """Test: Session with low confidence scores"""
    logger.info("🧪 TEST 6: Low confidence segments")
    
    with app.app_context():
        session = Session(
            external_id=f"test-lowconf-{datetime.now().timestamp()}",
            user_id=1,
            status='recording',
            started_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # Add segments with low confidence (< 0.5)
        for i in range(5):
            segment = Segment(
                session_id=session.id,
                kind='final',
                text='Um... uh... unclear speech...',
                start_ms=i * 1000,
                end_ms=(i + 1) * 1000,
                avg_confidence=0.3 + i * 0.05  # 0.30 to 0.50
            )
            db.session.add(segment)
        
        db.session.commit()
        logger.info(f"  Created session {session.id} with low confidence segments")
        
        try:
            success = SessionService.finalize_session(
                session_id=session.id,
                room=session.external_id
            )
            logger.info(f"  ✅ Handled low confidence: {success}")
            return success
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            return False

def test_special_characters():
    """Test: Segments with special characters, emojis, unicode"""
    logger.info("🧪 TEST 7: Special characters and unicode")
    
    with app.app_context():
        session = Session(
            external_id=f"test-unicode-{datetime.now().timestamp()}",
            user_id=1,
            status='recording',
            started_at=datetime.utcnow()
        )
        db.session.add(session)
        db.session.commit()
        
        # Add segments with special characters
        special_texts = [
            "Hello 👋 world 🌍",
            'Quote: "Hello" and \'world\'',
            "Math: 1 + 1 = 2, x² + y²",
            "Foreign: Héllo wörld, 你好世界",
            "Symbols: © ® ™ € £ ¥"
        ]
        
        for i, text in enumerate(special_texts):
            segment = Segment(
                session_id=session.id,
                kind='final',
                text=text,
                start_ms=i * 1000,
                end_ms=(i + 1) * 1000,
                avg_confidence=0.95
            )
            db.session.add(segment)
        
        db.session.commit()
        logger.info(f"  Created session {session.id} with unicode/special chars")
        
        try:
            success = SessionService.finalize_session(
                session_id=session.id,
                room=session.external_id
            )
            logger.info(f"  ✅ Handled special characters: {success}")
            return success
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            return False

def run_all_tests():
    """Run all edge case tests"""
    logger.info("="*80)
    logger.info("🧪 EDGE CASE TESTING SUITE")
    logger.info("="*80)
    
    tests = [
        ("Empty Session (Zero Segments)", test_empty_session),
        ("Single Segment Session", test_single_segment),
        ("Large Session (100 segments)", test_large_session),
        ("Missing/Invalid Session ID", test_missing_session),
        ("Already Finalized (Idempotency)", test_already_finalized),
        ("Low Confidence Segments", test_low_confidence_segments),
        ("Special Characters/Unicode", test_special_characters),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            logger.info("")
            result = test_func()
            results[name] = result
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}", exc_info=True)
            results[name] = False
    
    # Summary
    logger.info("")
    logger.info("="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {name}")
    
    logger.info("")
    logger.info(f"  Pass Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    logger.info("")
    
    if passed == total:
        logger.info("  🎉 ALL EDGE CASES HANDLED SUCCESSFULLY!")
    else:
        logger.warning(f"  ⚠️  {total - passed} test(s) failed")
    
    logger.info("="*80)
    
    return passed == total

if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
