"""
Advanced resource cleanup service to prevent memory leaks and optimize performance
"""
import gc
import logging
import time
import threading
import weakref
from typing import Dict, Set, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class ResourceCleanupManager:
    """
    Comprehensive resource cleanup manager to prevent memory leaks
    and optimize system performance during high-load operations
    """
    
    def __init__(self):
        self.active_sessions = weakref.WeakValueDictionary()
        self.cleanup_tasks = defaultdict(list)
        self.cleanup_intervals = {
            'websocket_buffers': 300,    # 5 minutes
            'temp_files': 600,           # 10 minutes
            'expired_tokens': 900,       # 15 minutes
            'database_connections': 120, # 2 minutes
            'audio_buffers': 180,        # 3 minutes
            'memory_gc': 60              # 1 minute
        }
        self.last_cleanup = defaultdict(float)
        self.cleanup_stats = defaultdict(int)
        self.running = False
        self.cleanup_thread = None
        self._lock = threading.Lock()
    
    def register_cleanup_task(self, category: str, cleanup_func: Callable, interval: Optional[int] = None):
        """Register a cleanup function to be called periodically"""
        with self._lock:
            self.cleanup_tasks[category].append(cleanup_func)
            if interval:
                self.cleanup_intervals[category] = interval
            logger.info(f"Registered cleanup task for category: {category}")
    
    def register_session_resource(self, session_id: str, resource_obj: Any):
        """Register a session resource for automatic cleanup"""
        with self._lock:
            self.active_sessions[session_id] = resource_obj
            logger.debug(f"Registered resource for session: {session_id}")
    
    def cleanup_session_resources(self, session_id: str):
        """Clean up all resources for a specific session"""
        try:
            with self._lock:
                if session_id in self.active_sessions:
                    resource = self.active_sessions[session_id]
                    
                    # Call cleanup method if it exists
                    if hasattr(resource, 'cleanup'):
                        resource.cleanup()
                    elif hasattr(resource, 'close'):
                        resource.close()
                    elif hasattr(resource, 'terminate'):
                        resource.terminate()
                    
                    # Remove from active sessions
                    del self.active_sessions[session_id]
                    self.cleanup_stats['sessions_cleaned'] += 1
                    logger.info(f"Cleaned up resources for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return statistics"""
        try:
            # Get memory before cleanup - with fallback if psutil unavailable
            memory_before = 0
            try:
                import psutil
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            except ImportError:
                logger.warning("psutil not available - memory tracking disabled")
            
            # Collect garbage in all generations
            collected = [gc.collect(generation) for generation in range(3)]
            total_collected = sum(collected)
            
            # Get memory after cleanup - with fallback if psutil unavailable
            memory_after = 0
            memory_freed = 0
            try:
                if 'process' in locals():
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_freed = memory_before - memory_after
            except (ImportError, NameError):
                # psutil not available - skip memory tracking
                pass
            
            stats = {
                'objects_collected': total_collected,
                'memory_before_mb': round(memory_before, 2),
                'memory_after_mb': round(memory_after, 2),
                'memory_freed_mb': round(memory_freed, 2),
                'generation_0': collected[0],
                'generation_1': collected[1],
                'generation_2': collected[2],
                'timestamp': time.time()
            }
            
            self.cleanup_stats['gc_runs'] += 1
            self.cleanup_stats['total_objects_collected'] += total_collected
            
            if memory_freed > 1:  # Only log if significant memory was freed
                logger.info(f"Garbage collection freed {memory_freed:.2f} MB, collected {total_collected} objects")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to perform garbage collection: {e}")
            return {'error': str(e), 'timestamp': time.time()}
    
    def cleanup_websocket_buffers(self):
        """Clean up orphaned WebSocket buffers"""
        try:
            from services.session_buffer_manager import buffer_registry
            
            # Get buffer metrics
            metrics = buffer_registry.get_all_metrics()
            
            # Clean up expired buffers
            expired_count = 0
            current_time = time.time()
            
            for session_id, session_metrics in metrics.get('sessions', {}).items():
                last_activity = session_metrics.get('last_activity', 0)
                if current_time - last_activity > 1800:  # 30 minutes inactive
                    try:
                        buffer_registry.release(session_id)
                        expired_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to release buffer for session {session_id}: {e}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired WebSocket buffers")
                self.cleanup_stats['websocket_buffers_cleaned'] += expired_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup WebSocket buffers: {e}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files older than threshold"""
        try:
            import os
            import tempfile
            
            temp_dir = tempfile.gettempdir()
            current_time = time.time()
            cutoff_time = current_time - 3600  # 1 hour old
            
            cleaned_count = 0
            freed_bytes = 0
            
            for filename in os.listdir(temp_dir):
                if filename.startswith('mina_') or filename.startswith('audio_'):
                    filepath = os.path.join(temp_dir, filename)
                    try:
                        stat_info = os.stat(filepath)
                        if stat_info.st_mtime < cutoff_time:
                            file_size = stat_info.st_size
                            os.unlink(filepath)
                            cleaned_count += 1
                            freed_bytes += file_size
                    except (OSError, FileNotFoundError):
                        # File already deleted or inaccessible
                        pass
            
            if cleaned_count > 0:
                freed_mb = freed_bytes / 1024 / 1024
                logger.info(f"Cleaned up {cleaned_count} temp files, freed {freed_mb:.2f} MB")
                self.cleanup_stats['temp_files_cleaned'] += cleaned_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
    
    def start_cleanup_service(self):
        """Start the background cleanup service"""
        if self.running:
            logger.warning("Cleanup service is already running")
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("Resource cleanup service started")
    
    def stop_cleanup_service(self):
        """Stop the background cleanup service"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Resource cleanup service stopped")
    
    def _cleanup_loop(self):
        """Main cleanup loop that runs in background thread"""
        while self.running:
            try:
                current_time = time.time()
                
                # Run scheduled cleanup tasks
                for category, cleanup_funcs in self.cleanup_tasks.items():
                    interval = self.cleanup_intervals.get(category, 300)
                    last_run = self.last_cleanup.get(category, 0)
                    
                    if current_time - last_run >= interval:
                        for cleanup_func in cleanup_funcs:
                            try:
                                cleanup_func()
                            except Exception as e:
                                logger.error(f"Cleanup task failed for {category}: {e}")
                        
                        self.last_cleanup[category] = current_time
                
                # Built-in cleanup tasks
                if current_time - self.last_cleanup.get('websocket_buffers', 0) >= self.cleanup_intervals['websocket_buffers']:
                    self.cleanup_websocket_buffers()
                    self.last_cleanup['websocket_buffers'] = current_time
                
                if current_time - self.last_cleanup.get('temp_files', 0) >= self.cleanup_intervals['temp_files']:
                    self.cleanup_temp_files()
                    self.last_cleanup['temp_files'] = current_time
                
                if current_time - self.last_cleanup.get('memory_gc', 0) >= self.cleanup_intervals['memory_gc']:
                    self.force_garbage_collection()
                    self.last_cleanup['memory_gc'] = current_time
                
                # Sleep for a short interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)  # Wait longer if there's an error
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics"""
        return {
            'active_sessions': len(self.active_sessions),
            'cleanup_stats': dict(self.cleanup_stats),
            'last_cleanup_times': dict(self.last_cleanup),
            'cleanup_intervals': dict(self.cleanup_intervals),
            'is_running': self.running,
            'registered_categories': list(self.cleanup_tasks.keys())
        }

# Global instance
resource_cleanup_manager = ResourceCleanupManager()

def cleanup_session_resources(session_id: str):
    """Convenience function to cleanup session resources"""
    resource_cleanup_manager.cleanup_session_resources(session_id)

def register_session_resource(session_id: str, resource: Any):
    """Convenience function to register session resource"""
    resource_cleanup_manager.register_session_resource(session_id, resource)

def force_cleanup():
    """Convenience function to force immediate cleanup"""
    return resource_cleanup_manager.force_garbage_collection()