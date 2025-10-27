"""
Background Task Service with Automatic Retry and Error Handling

Provides robust background task execution with:
- Automatic retry with exponential backoff
- Dead letter queue for failed tasks
- Task status tracking
- Error notification
- Flask app context support for database operations
"""

import time
import logging
import traceback
from typing import Callable, Any, Dict, Optional
from functools import wraps
from datetime import datetime, timedelta
import threading
from queue import Queue, Empty

logger = logging.getLogger(__name__)

# Flask app will be imported lazily to avoid circular import
# CRITICAL: This enables database operations in background threads
flask_app = None


class TaskStatus:
    """Task execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRY = 'retry'
    DEAD = 'dead_letter'


class BackgroundTask:
    """Represents a background task with retry capability"""
    
    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        backoff_multiplier: float = 2.0
    ):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
        
        self.status = TaskStatus.PENDING
        self.attempts = 0
        self.last_error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.next_retry_at = None
    
    def execute(self) -> bool:
        """
        Execute the task with retry logic.
        Wraps execution in Flask app context for database operations.
        
        Returns:
            bool: True if successful, False if failed
        """
        self.attempts += 1
        self.started_at = datetime.utcnow()
        self.status = TaskStatus.RUNNING
        
        try:
            logger.info(f"Executing task {self.task_id} (attempt {self.attempts}/{self.max_retries})")
            
            # 🔥 CRITICAL FIX: Lazy import to avoid circular dependency
            # Import Flask app only when needed
            global flask_app
            if flask_app is None:
                from app import app as _flask_app
                flask_app = _flask_app
            
            # Wrap execution in Flask app context for database operations
            with flask_app.app_context():
                result = self.func(*self.args, **self.kwargs)
            
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            logger.info(f"Task {self.task_id} completed successfully")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            error_trace = traceback.format_exc()
            
            if self.attempts < self.max_retries:
                # Calculate next retry time with exponential backoff
                delay = self.retry_delay * (self.backoff_multiplier ** (self.attempts - 1))
                self.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
                self.status = TaskStatus.RETRY
                
                logger.warning(
                    f"Task {self.task_id} failed (attempt {self.attempts}/{self.max_retries}). "
                    f"Retry in {delay}s. Error: {e}"
                )
            else:
                # Max retries exceeded - move to dead letter queue
                self.status = TaskStatus.DEAD
                logger.error(
                    f"Task {self.task_id} failed after {self.max_retries} attempts. "
                    f"Moving to dead letter queue. Error: {e}\n{error_trace}"
                )
            
            return False


class BackgroundTaskManager:
    """
    Manages background task execution with retry and error handling
    
    Features:
    - Automatic retry with exponential backoff
    - Dead letter queue for failed tasks
    - Task status tracking
    - Worker thread pool
    """
    
    def __init__(self, num_workers: int = 2):
        self.num_workers = num_workers
        self.task_queue = Queue()
        self.retry_queue = Queue()
        self.dead_letter_queue = []
        self.active_tasks: Dict[str, BackgroundTask] = {}
        self.completed_tasks: Dict[str, BackgroundTask] = {}
        self.workers = []
        self.running = False
        self._lock = threading.Lock()
    
    def start(self):
        """Start worker threads"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"BackgroundWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        # Start retry scheduler thread
        retry_thread = threading.Thread(
            target=self._retry_scheduler,
            name="RetryScheduler",
            daemon=True
        )
        retry_thread.start()
        
        logger.info(f"BackgroundTaskManager started with {self.num_workers} workers")
    
    def stop(self):
        """Stop all workers"""
        self.running = False
        logger.info("BackgroundTaskManager stopping...")
    
    def submit_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        max_retries: int = 3,
        retry_delay: int = 5,
        **kwargs
    ) -> str:
        """
        Submit a task for background execution
        
        Args:
            task_id: Unique task identifier
            func: Function to execute
            *args: Positional arguments for func
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            **kwargs: Keyword arguments for func
        
        Returns:
            str: Task ID
        """
        task = BackgroundTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        with self._lock:
            self.active_tasks[task_id] = task
        
        self.task_queue.put(task)
        logger.info(f"Task {task_id} submitted to queue")
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
            elif task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
            else:
                return None
        
        return {
            'task_id': task.task_id,
            'status': task.status,
            'attempts': task.attempts,
            'max_retries': task.max_retries,
            'last_error': task.last_error,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'next_retry_at': task.next_retry_at.isoformat() if task.next_retry_at else None
        }
    
    def get_dead_letter_queue(self) -> list:
        """Get all failed tasks in dead letter queue"""
        return [
            {
                'task_id': task.task_id,
                'attempts': task.attempts,
                'last_error': task.last_error,
                'created_at': task.created_at.isoformat()
            }
            for task in self.dead_letter_queue
        ]
    
    def retry_dead_letter_task(self, task_id: str) -> bool:
        """Manually retry a task from dead letter queue"""
        for i, task in enumerate(self.dead_letter_queue):
            if task.task_id == task_id:
                task.attempts = 0
                task.status = TaskStatus.PENDING
                task.last_error = None
                self.task_queue.put(task)
                self.dead_letter_queue.pop(i)
                logger.info(f"Task {task_id} resubmitted from dead letter queue")
                return True
        return False
    
    def _worker_loop(self):
        """Worker thread main loop"""
        while self.running:
            try:
                # Get task from queue (non-blocking with timeout)
                task = self.task_queue.get(timeout=1)
                
                # Execute task
                success = task.execute()
                
                if success:
                    # Move to completed
                    with self._lock:
                        self.completed_tasks[task.task_id] = task
                        if task.task_id in self.active_tasks:
                            del self.active_tasks[task.task_id]
                
                elif task.status == TaskStatus.RETRY:
                    # Add to retry queue
                    self.retry_queue.put(task)
                
                elif task.status == TaskStatus.DEAD:
                    # Move to dead letter queue
                    with self._lock:
                        self.dead_letter_queue.append(task)
                        if task.task_id in self.active_tasks:
                            del self.active_tasks[task.task_id]
                
                self.task_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}\n{traceback.format_exc()}")
    
    def _retry_scheduler(self):
        """Retry scheduler thread - checks for tasks ready to retry"""
        while self.running:
            try:
                # Check retry queue for tasks ready to retry
                retry_list = []
                
                # Collect all tasks from retry queue
                while not self.retry_queue.empty():
                    try:
                        task = self.retry_queue.get_nowait()
                        retry_list.append(task)
                    except Empty:
                        break
                
                # Check which tasks are ready to retry
                now = datetime.utcnow()
                for task in retry_list:
                    if task.next_retry_at and now >= task.next_retry_at:
                        # Ready to retry
                        self.task_queue.put(task)
                        logger.info(f"Task {task.task_id} ready for retry")
                    else:
                        # Put back in retry queue
                        self.retry_queue.put(task)
                
                # Sleep before next check
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Retry scheduler error: {e}\n{traceback.format_exc()}")
                time.sleep(5)


# Global task manager instance
background_task_manager = BackgroundTaskManager(num_workers=2)


def background_task(max_retries: int = 3, retry_delay: int = 5):
    """
    Decorator for functions that should run as background tasks
    
    Usage:
        @background_task(max_retries=3, retry_delay=5)
        def process_transcription(session_id):
            # Task logic here
            pass
        
        # Submit task
        task_id = process_transcription(session_id="abc123")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate task ID
            task_id = f"{func.__name__}_{int(time.time() * 1000)}"
            
            # Submit to background task manager
            return background_task_manager.submit_task(
                task_id=task_id,
                func=func,
                *args,
                max_retries=max_retries,
                retry_delay=retry_delay,
                **kwargs
            )
        
        return wrapper
    return decorator


# Example usage:
if __name__ == "__main__":
    # Start the manager
    background_task_manager.start()
    
    # Example task
    @background_task(max_retries=3, retry_delay=2)
    def example_task(value: int):
        """Example task that may fail"""
        if value < 5:
            raise ValueError(f"Value too low: {value}")
        return f"Processed {value}"
    
    # Submit tasks
    task1 = example_task(3)  # Will retry
    task2 = example_task(10)  # Will succeed
    
    # Check status
    time.sleep(1)
    print("Task 1 status:", background_task_manager.get_task_status(task1))
    print("Task 2 status:", background_task_manager.get_task_status(task2))
    
    # Wait for completion
    time.sleep(10)
    print("\nDead letter queue:", background_task_manager.get_dead_letter_queue())
