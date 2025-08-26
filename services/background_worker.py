#!/usr/bin/env python3
# 🏭 Production Feature: Background Worker for Non-blocking Transcription
"""
Implements async background worker to prevent Whisper transcription from blocking the main Flask thread.
Addresses: "Blocking Transcription Calls" - Critical production reliability risk.

Key Features:
- Async transcription processing queue
- Memory-efficient chunk handling
- Graceful error recovery
- Backpressure management
- Session state coordination
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from threading import Thread, Event
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionJob:
    """Background transcription job."""
    job_id: str
    session_id: str
    audio_data: bytes
    mime_type: str
    timestamp: float
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BackgroundTranscriptionWorker:
    """
    🏭 Production-grade background worker for non-blocking transcription.
    
    Prevents Whisper from blocking the Flask event loop by processing
    transcription jobs in dedicated worker threads with proper queue management.
    """
    
    def __init__(self, max_workers: int = 2, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # Job queue and processing
        self.job_queue = Queue(maxsize=max_queue_size)
        self.result_callbacks = {}  # {job_id: callback}
        
        # Worker management
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="transcription")
        self.worker_threads = []
        self.shutdown_event = Event()
        
        # Metrics
        self.jobs_processed = 0
        self.jobs_failed = 0
        self.jobs_dropped = 0
        self.avg_processing_time = 0.0
        self.queue_high_watermark = 0
        
        # Start worker threads
        self._start_workers()
        
        logger.info(f"🏭 Background transcription worker initialized: {max_workers} workers, queue size {max_queue_size}")
    
    def _start_workers(self):
        """Start background worker threads."""
        for i in range(self.max_workers):
            worker = Thread(target=self._worker_loop, name=f"transcription-worker-{i}")
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)
        
        logger.info(f"Started {len(self.worker_threads)} background transcription workers")
    
    def _worker_loop(self):
        """Main worker loop for processing transcription jobs."""
        while not self.shutdown_event.is_set():
            try:
                # Get job from queue with timeout
                job = self.job_queue.get(timeout=1.0)
                
                # Process the job
                self._process_job(job)
                
                # Mark job as done
                self.job_queue.task_done()
                
            except Empty:
                # Timeout - continue loop
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                continue
    
    def _process_job(self, job: TranscriptionJob):
        """Process a single transcription job."""
        start_time = time.time()
        
        try:
            logger.debug(f"Processing transcription job {job.job_id} for session {job.session_id}")
            
            # Import transcription service here to avoid circular imports
            from services.whisper_streaming import WhisperStreamingService
            from services.transcription_service import TranscriptionConfig
            
            # Create isolated transcription config
            config = TranscriptionConfig(
                language='en',
                confidence_threshold=0.4,
                max_chunk_duration=30.0,
                min_chunk_duration=0.1
            )
            
            # Create Whisper service instance for this job
            whisper_service = WhisperStreamingService(config)
            
            # Process the audio
            result = whisper_service.transcribe_chunk(job.audio_data, job.mime_type)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update metrics
            self.jobs_processed += 1
            self.avg_processing_time = (
                (self.avg_processing_time * (self.jobs_processed - 1) + processing_time) / 
                self.jobs_processed
            )
            
            # Prepare result with metadata
            enhanced_result = {
                **result,
                'job_id': job.job_id,
                'session_id': job.session_id,
                'processing_time_ms': round(processing_time * 1000, 2),
                'processed_at': datetime.now().isoformat(),
                'worker_thread': Thread.current_thread().name
            }
            
            # Execute callback if provided
            if job.callback:
                try:
                    job.callback(enhanced_result)
                except Exception as e:
                    logger.error(f"Callback error for job {job.job_id}: {e}")
            
            logger.debug(f"✅ Transcription job {job.job_id} completed in {processing_time:.3f}s")
            
        except Exception as e:
            self.jobs_failed += 1
            logger.error(f"❌ Transcription job {job.job_id} failed: {e}")
            
            # Still execute callback with error
            if job.callback:
                try:
                    error_result = {
                        'job_id': job.job_id,
                        'session_id': job.session_id,
                        'error': str(e),
                        'status': 'failed',
                        'processed_at': datetime.now().isoformat()
                    }
                    job.callback(error_result)
                except Exception as callback_error:
                    logger.error(f"Callback error for failed job {job.job_id}: {callback_error}")
    
    def submit_job(self, session_id: str, audio_data: bytes, mime_type: str, 
                   callback: Optional[Callable] = None, metadata: Dict[str, Any] = None) -> str:
        """
        Submit a transcription job to the background worker.
        
        Returns:
            job_id: Unique identifier for the submitted job
            
        Raises:
            RuntimeError: If queue is full (backpressure)
        """
        job_id = f"{session_id}_{int(time.time() * 1000)}"
        
        # Check queue capacity (backpressure management)
        current_queue_size = self.job_queue.qsize()
        self.queue_high_watermark = max(self.queue_high_watermark, current_queue_size)
        
        if current_queue_size >= self.max_queue_size:
            self.jobs_dropped += 1
            raise RuntimeError(f"Transcription queue full ({current_queue_size}/{self.max_queue_size}). Dropping job.")
        
        # Create job
        job = TranscriptionJob(
            job_id=job_id,
            session_id=session_id,
            audio_data=audio_data,
            mime_type=mime_type,
            timestamp=time.time(),
            callback=callback,
            metadata=metadata or {}
        )
        
        # Submit to queue
        try:
            self.job_queue.put_nowait(job)
            logger.debug(f"📤 Submitted transcription job {job_id} (queue: {current_queue_size + 1}/{self.max_queue_size})")
            return job_id
        except Exception as e:
            self.jobs_dropped += 1
            raise RuntimeError(f"Failed to submit transcription job: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        return {
            'workers': len(self.worker_threads),
            'queue_size': self.job_queue.qsize(),
            'queue_capacity': self.max_queue_size,
            'queue_utilization_percent': round((self.job_queue.qsize() / self.max_queue_size) * 100, 1),
            'queue_high_watermark': self.queue_high_watermark,
            'jobs_processed': self.jobs_processed,
            'jobs_failed': self.jobs_failed,
            'jobs_dropped': self.jobs_dropped,
            'avg_processing_time_ms': round(self.avg_processing_time * 1000, 2),
            'success_rate_percent': round(
                (self.jobs_processed / max(1, self.jobs_processed + self.jobs_failed)) * 100, 2
            )
        }
    
    def shutdown(self, timeout: float = 10.0):
        """Gracefully shutdown the worker."""
        logger.info("🛑 Shutting down background transcription worker...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Wait for queue to drain
        try:
            self.job_queue.join()
        except KeyboardInterrupt:
            logger.warning("Interrupted while waiting for queue to drain")
        
        # Shutdown executor
        self.executor.shutdown(wait=True, timeout=timeout)
        
        # Wait for worker threads
        for worker in self.worker_threads:
            worker.join(timeout=1.0)
        
        logger.info("✅ Background transcription worker shutdown complete")

# Global worker instance
_background_worker: Optional[BackgroundTranscriptionWorker] = None

def get_background_worker() -> BackgroundTranscriptionWorker:
    """Get or create the global background worker instance."""
    global _background_worker
    if _background_worker is None:
        _background_worker = BackgroundTranscriptionWorker()
    return _background_worker

def shutdown_background_worker():
    """Shutdown the global background worker."""
    global _background_worker
    if _background_worker is not None:
        _background_worker.shutdown()
        _background_worker = None