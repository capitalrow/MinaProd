"""
PrefetchController Service - CROWN⁴.5 Zero-Lag Pagination

Implements intelligent preloading for task lists to eliminate pagination lag.
Triggers prefetch at 70% scroll position with adaptive throttling.

Key Features:
- Scroll position detection and 70% threshold triggering
- Adaptive throttling to keep CPU overhead ≤5%
- Batch prefetching with configurable page sizes
- LRU cache integration for prefetched data
- Performance monitoring and telemetry
"""

import logging
import time
import psutil
from typing import Optional, Dict, Any, List
from collections import OrderedDict
from sqlalchemy import select, func
from models import db
from models.task import Task

logger = logging.getLogger(__name__)


class PrefetchController:
    """
    Service for intelligent task list prefetching.
    
    Responsibilities:
    - Detect scroll position approaching end of current page
    - Prefetch next page of tasks before user reaches end
    - Adaptive throttling based on CPU and network conditions
    - Cache management with LRU eviction
    - Track prefetch hit rate for optimization
    """
    
    # Configuration constants
    SCROLL_THRESHOLD = 0.70  # Trigger prefetch at 70% scroll
    DEFAULT_PAGE_SIZE = 50  # Default tasks per page
    MAX_PREFETCH_PAGES = 3  # Maximum pages to prefetch ahead
    MIN_THROTTLE_MS = 100  # Minimum time between prefetch requests (ms)
    MAX_THROTTLE_MS = 1000  # Maximum throttle when CPU high
    MAX_CPU_OVERHEAD = 0.05  # Maximum CPU overhead (5%)
    CPU_CHECK_INTERVAL_MS = 500  # Check CPU every 500ms
    
    # LRU cache for prefetched pages
    MAX_CACHE_SIZE = 10  # Keep up to 10 pages in cache
    
    def __init__(self):
        """Initialize PrefetchController with empty cache."""
        # LRU cache for prefetched pages
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # Throttling state
        self.last_prefetch_time: Dict[int, float] = {}
        self.current_throttle_ms = self.MIN_THROTTLE_MS
        self.last_cpu_check_time = 0.0
        
        # Performance metrics
        self.metrics = {
            'prefetch_count': 0,
            'cache_hit_count': 0,
            'cache_miss_count': 0,
            'throttle_skip_count': 0,
            'cpu_throttle_adjustments': 0
        }
    
    def _generate_cache_key(
        self,
        user_id: int,
        page: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate cache key for prefetched page.
        
        Args:
            user_id: User ID
            page: Page number
            filters: Applied filters (optional)
            
        Returns:
            Cache key string
        """
        # Base key from user and page
        key = f"user_{user_id}_page_{page}"
        
        # Add filter hash if filters applied
        if filters:
            # Create deterministic string from filters
            filter_str = '_'.join(f"{k}:{v}" for k, v in sorted(filters.items()))
            key += f"_filters_{hash(filter_str)}"
        
        return key
    
    def _adjust_throttle_based_on_cpu(self):
        """
        Adjust throttle timing based on current CPU usage.
        Implements adaptive throttling to keep CPU overhead ≤5%.
        """
        current_time = time.time() * 1000
        
        # Only check CPU periodically (not every call)
        if current_time - self.last_cpu_check_time < self.CPU_CHECK_INTERVAL_MS:
            return
        
        self.last_cpu_check_time = current_time
        
        try:
            # Get current CPU percentage
            cpu_percent = psutil.cpu_percent(interval=0.1) / 100.0
            
            # Adjust throttle based on CPU usage
            if cpu_percent > self.MAX_CPU_OVERHEAD:
                # CPU too high - increase throttle
                self.current_throttle_ms = min(
                    self.current_throttle_ms * 1.5,
                    self.MAX_THROTTLE_MS
                )
                self.metrics['cpu_throttle_adjustments'] += 1
                logger.debug(f"Increased throttle to {self.current_throttle_ms:.0f}ms due to CPU: {cpu_percent:.1%}")
            else:
                # CPU OK - decrease throttle
                self.current_throttle_ms = max(
                    self.current_throttle_ms * 0.9,
                    self.MIN_THROTTLE_MS
                )
        except Exception as e:
            logger.error(f"Failed to check CPU: {e}")
    
    def _should_throttle(self, user_id: int) -> bool:
        """
        Check if prefetch should be throttled based on adaptive timing and CPU.
        
        Args:
            user_id: User ID
            
        Returns:
            True if should throttle, False otherwise
        """
        # Adjust throttle based on current CPU
        self._adjust_throttle_based_on_cpu()
        
        current_time = time.time() * 1000  # Convert to ms
        last_time = self.last_prefetch_time.get(user_id, 0)
        
        time_since_last = current_time - last_time
        
        if time_since_last < self.current_throttle_ms:
            self.metrics['throttle_skip_count'] += 1
            logger.debug(
                f"Throttling prefetch for user {user_id} "
                f"({time_since_last:.0f}ms since last, throttle={self.current_throttle_ms:.0f}ms)"
            )
            return True
        
        return False
    
    def _add_to_cache(self, key: str, data: Dict[str, Any]):
        """
        Add prefetched data to LRU cache.
        
        Args:
            key: Cache key
            data: Prefetched data to cache
        """
        # Remove key if it exists (to update position)
        if key in self.cache:
            del self.cache[key]
        
        # Add to cache (at end)
        self.cache[key] = data
        
        # Evict oldest if cache too large
        while len(self.cache) > self.MAX_CACHE_SIZE:
            self.cache.popitem(last=False)  # Remove oldest (first) item
            logger.debug(f"Evicted oldest cache entry (cache size: {len(self.cache)})")
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache and move to end (most recently used).
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None
        """
        if key not in self.cache:
            self.metrics['cache_miss_count'] += 1
            return None
        
        # Move to end (mark as recently used)
        data = self.cache.pop(key)
        self.cache[key] = data
        
        self.metrics['cache_hit_count'] += 1
        logger.debug(f"Cache hit for key: {key}")
        
        return data
    
    def fetch_page(
        self,
        user_id: int,
        page: int,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch a page of tasks for a user with optional filters.
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of tasks per page
            filters: Filter criteria (status, priority, etc.)
            
        Returns:
            Dictionary with tasks and pagination metadata
        """
        try:
            # Build base query
            query = select(Task).where(
                (Task.assigned_to_id == user_id) | (Task.created_by_id == user_id)
            )
            
            # Apply filters if provided
            if filters:
                if 'status' in filters:
                    query = query.where(Task.status == filters['status'])
                if 'priority' in filters:
                    query = query.where(Task.priority == filters['priority'])
                if 'completed' in filters:
                    if filters['completed']:
                        query = query.where(Task.status == 'completed')
                    else:
                        query = query.where(Task.status != 'completed')
            
            # Get total count for pagination
            count_query = select(func.count()).select_from(query.subquery())
            total_count = db.session.scalar(count_query) or 0
            
            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            
            # Fetch page of tasks
            query = query.order_by(Task.due_date.asc(), Task.priority.desc(), Task.created_at.desc())
            query = query.limit(page_size).offset(offset)
            
            tasks = db.session.scalars(query).all()
            
            # Build response
            return {
                'tasks': [task.to_dict() for task in tasks],
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch page {page} for user {user_id}: {e}")
            return {
                'tasks': [],
                'page': page,
                'page_size': page_size,
                'total_count': 0,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False,
                'error': str(e)
            }
    
    def prefetch_next_page(
        self,
        user_id: int,
        current_page: int,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> bool:
        """
        Prefetch the next page of tasks.
        
        Args:
            user_id: User ID
            current_page: Current page number
            page_size: Number of tasks per page
            filters: Filter criteria
            force: Force prefetch even if throttled
            
        Returns:
            True if prefetch successful, False otherwise
        """
        try:
            # Check throttling (unless forced)
            if not force and self._should_throttle(user_id):
                return False
            
            # Calculate next page
            next_page = current_page + 1
            
            # Generate cache key
            cache_key = self._generate_cache_key(user_id, next_page, filters)
            
            # Check if already cached
            if cache_key in self.cache:
                logger.debug(f"Page {next_page} already cached for user {user_id}")
                return True
            
            # Fetch next page
            page_data = self.fetch_page(user_id, next_page, page_size, filters)
            
            # Only cache if page has data
            if page_data.get('tasks'):
                self._add_to_cache(cache_key, page_data)
                
                # Update throttle timestamp
                self.last_prefetch_time[user_id] = time.time() * 1000
                
                # Update metrics
                self.metrics['prefetch_count'] += 1
                
                logger.info(
                    f"Prefetched page {next_page} for user {user_id} "
                    f"({len(page_data['tasks'])} tasks)"
                )
                
                return True
            else:
                logger.debug(f"No more tasks to prefetch for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to prefetch next page for user {user_id}: {e}")
            return False
    
    def get_cached_page(
        self,
        user_id: int,
        page: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached page if available.
        
        Args:
            user_id: User ID
            page: Page number
            filters: Filter criteria
            
        Returns:
            Cached page data or None
        """
        cache_key = self._generate_cache_key(user_id, page, filters)
        return self._get_from_cache(cache_key)
    
    def handle_scroll_event(
        self,
        user_id: int,
        scroll_position: float,
        total_height: float,
        current_page: int,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle scroll event and trigger prefetch if needed.
        
        Args:
            scroll_position: Current scroll position (pixels)
            total_height: Total scrollable height (pixels)
            current_page: Current page number
            page_size: Tasks per page
            filters: Active filters
            
        Returns:
            Response with prefetch status
        """
        try:
            # Calculate scroll percentage
            scroll_percentage = scroll_position / total_height if total_height > 0 else 0
            
            # Check if we've reached prefetch threshold
            if scroll_percentage >= self.SCROLL_THRESHOLD:
                # Trigger prefetch
                prefetched = self.prefetch_next_page(
                    user_id,
                    current_page,
                    page_size,
                    filters
                )
                
                return {
                    'prefetch_triggered': True,
                    'prefetch_success': prefetched,
                    'scroll_percentage': scroll_percentage,
                    'next_page': current_page + 1
                }
            
            return {
                'prefetch_triggered': False,
                'scroll_percentage': scroll_percentage
            }
            
        except Exception as e:
            logger.error(f"Failed to handle scroll event: {e}")
            return {
                'prefetch_triggered': False,
                'error': str(e)
            }
    
    def clear_user_cache(self, user_id: int):
        """
        Clear all cached pages for a specific user.
        
        Args:
            user_id: User ID
        """
        # Find and remove all cache entries for this user
        keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"user_{user_id}_")]
        
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.info(f"Cleared {len(keys_to_remove)} cached pages for user {user_id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get prefetch controller performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        total_requests = self.metrics['cache_hit_count'] + self.metrics['cache_miss_count']
        cache_hit_rate = (
            self.metrics['cache_hit_count'] / total_requests
            if total_requests > 0 else 0
        )
        
        return {
            'prefetch_count': self.metrics['prefetch_count'],
            'cache_hit_count': self.metrics['cache_hit_count'],
            'cache_miss_count': self.metrics['cache_miss_count'],
            'cache_hit_rate': cache_hit_rate,
            'throttle_skip_count': self.metrics['throttle_skip_count'],
            'cache_size': len(self.cache),
            'max_cache_size': self.MAX_CACHE_SIZE
        }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = {
            'prefetch_count': 0,
            'cache_hit_count': 0,
            'cache_miss_count': 0,
            'throttle_skip_count': 0
        }
        logger.info("Reset prefetch controller metrics")


# Singleton instance
prefetch_controller = PrefetchController()
