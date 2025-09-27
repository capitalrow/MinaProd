# services/intelligent_chunk_manager.py
"""
Intelligent Chunk Management System
Advanced chunk management with adaptive sizing, quality-based filtering,
memory-efficient storage, and sophisticated processing optimization.
"""

import asyncio
import logging
import time
import threading
import uuid
import hashlib
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple, Union
from enum import Enum
import numpy as np
import json
from concurrent.futures import ThreadPoolExecutor
import gzip
import pickle

logger = logging.getLogger(__name__)

class ChunkPriority(Enum):
    """Chunk processing priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class ChunkState(Enum):
    """Chunk processing states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    CACHED = "cached"
    MERGED = "merged"
    DISCARDED = "discarded"

@dataclass
class ChunkMetrics:
    """Comprehensive chunk metrics"""
    size_bytes: int = 0
    duration_ms: float = 0.0
    quality_score: float = 0.0
    voice_activity: float = 0.0
    noise_level: float = 0.0
    processing_time_ms: float = 0.0
    confidence_score: float = 0.0
    speaker_count: int = 0
    language_detected: Optional[str] = None
    emotion_intensity: float = 0.0
    compression_ratio: float = 1.0
    
    def calculate_priority_score(self) -> float:
        """Calculate dynamic priority score"""
        score = 0.0
        
        # Quality contribution (40%)
        score += self.quality_score * 0.4
        
        # Voice activity contribution (30%)
        score += self.voice_activity * 0.3
        
        # Low noise bonus (20%)
        score += (1.0 - self.noise_level) * 0.2
        
        # Confidence bonus (10%)
        score += self.confidence_score * 0.1
        
        return min(1.0, score)

@dataclass
class IntelligentChunk:
    """Enhanced audio chunk with intelligence"""
    id: str
    session_id: str
    data: Union[bytes, np.ndarray]
    timestamp: float
    sequence_number: int
    chunk_type: str = "audio"  # audio, text, metadata
    state: ChunkState = ChunkState.QUEUED
    priority: ChunkPriority = ChunkPriority.NORMAL
    metrics: ChunkMetrics = field(default_factory=ChunkMetrics)
    dependencies: List[str] = field(default_factory=list)
    related_chunks: List[str] = field(default_factory=list)
    processing_attempts: int = 0
    max_attempts: int = 3
    created_at: float = field(default_factory=time.time)
    processed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    compression_enabled: bool = True
    cache_key: Optional[str] = None
    
    def __post_init__(self):
        if not self.cache_key:
            self.cache_key = self._generate_cache_key()
    
    def _generate_cache_key(self) -> str:
        """Generate unique cache key for chunk"""
        content = f"{self.session_id}_{self.sequence_number}_{self.timestamp}"
        if isinstance(self.data, bytes):
            content += f"_{hashlib.md5(self.data).hexdigest()[:8]}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def compress_data(self) -> bool:
        """Compress chunk data to save memory"""
        if not self.compression_enabled or self.state == ChunkState.CACHED:
            return False
        
        try:
            if isinstance(self.data, np.ndarray):
                # Convert numpy array to bytes then compress
                data_bytes = self.data.tobytes()
                compressed = gzip.compress(data_bytes)
            elif isinstance(self.data, bytes):
                compressed = gzip.compress(self.data)
            else:
                # Convert other types to pickle then compress
                pickled = pickle.dumps(self.data)
                compressed = gzip.compress(pickled)
            
            original_size = len(self.data) if isinstance(self.data, bytes) else self.data.nbytes if isinstance(self.data, np.ndarray) else len(pickle.dumps(self.data))
            self.metrics.compression_ratio = len(compressed) / original_size
            
            # Store compressed data with metadata
            self.data = {
                'compressed': compressed,
                'original_type': type(self.data).__name__,
                'original_shape': getattr(self.data, 'shape', None),
                'original_dtype': getattr(self.data, 'dtype', None)
            }
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Chunk compression failed: {e}")
            return False
    
    def decompress_data(self) -> bool:
        """Decompress chunk data"""
        if not isinstance(self.data, dict) or 'compressed' not in self.data:
            return True  # Already decompressed
        
        try:
            compressed_data = self.data['compressed']
            decompressed = gzip.decompress(compressed_data)
            
            if self.data['original_type'] == 'ndarray':
                # Reconstruct numpy array
                self.data = np.frombuffer(
                    decompressed, 
                    dtype=self.data['original_dtype']
                ).reshape(self.data['original_shape'])
            elif self.data['original_type'] == 'bytes':
                self.data = decompressed
            else:
                # Unpickle other types
                self.data = pickle.loads(decompressed)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Chunk decompression failed: {e}")
            return False
    
    def calculate_memory_footprint(self) -> int:
        """Calculate memory footprint in bytes"""
        if isinstance(self.data, dict) and 'compressed' in self.data:
            return len(self.data['compressed'])
        elif isinstance(self.data, bytes):
            return len(self.data)
        elif isinstance(self.data, np.ndarray):
            return self.data.nbytes
        else:
            return len(pickle.dumps(self.data))
    
    def is_ready_for_processing(self) -> bool:
        """Check if chunk is ready for processing"""
        return (
            self.state == ChunkState.QUEUED and
            self.processing_attempts < self.max_attempts and
            all(dep in self.metadata.get('resolved_dependencies', []) for dep in self.dependencies)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp,
            'sequence_number': self.sequence_number,
            'chunk_type': self.chunk_type,
            'state': self.state.value,
            'priority': self.priority.value,
            'metrics': {
                'size_bytes': self.metrics.size_bytes,
                'duration_ms': self.metrics.duration_ms,
                'quality_score': self.metrics.quality_score,
                'voice_activity': self.metrics.voice_activity,
                'processing_time_ms': self.metrics.processing_time_ms,
                'compression_ratio': self.metrics.compression_ratio
            },
            'processing_attempts': self.processing_attempts,
            'created_at': self.created_at,
            'processed_at': self.processed_at,
            'memory_footprint': self.calculate_memory_footprint(),
            'cache_key': self.cache_key
        }

class AdaptiveSizer:
    """Dynamic chunk sizing based on content analysis"""
    
    def __init__(self):
        self.size_history = deque(maxlen=100)
        self.quality_history = deque(maxlen=100)
        self.optimal_size_cache = {}
        self.base_size = 1024  # Base chunk size in samples
        
    def calculate_optimal_size(self, audio: np.ndarray, sample_rate: int = 16000, session_context: Dict[str, Any] = None) -> int:
        """Calculate optimal chunk size based on audio characteristics"""
        try:
            # Analyze audio characteristics
            energy_variance = np.var(audio ** 2)
            zero_crossing_rate = len(np.where(np.diff(np.sign(audio)))[0]) / len(audio)
            
            # Base size adjustment factors
            size_multiplier = 1.0
            
            # Adjust for voice activity
            if energy_variance > 0.01:  # High energy variance suggests speech
                size_multiplier *= 0.8  # Smaller chunks for speech
            
            # Adjust for zero crossing rate (speech indicator)
            if 0.05 < zero_crossing_rate < 0.2:  # Typical speech range
                size_multiplier *= 0.7
            
            # Adjust based on session context
            if session_context:
                noise_level = session_context.get('noise_level', 0.0)
                if noise_level > 0.3:  # High noise
                    size_multiplier *= 1.2  # Larger chunks for better SNR
                
                processing_latency = session_context.get('avg_processing_latency', 0.0)
                if processing_latency > 500:  # High latency
                    size_multiplier *= 0.6  # Smaller chunks to reduce latency
            
            # Apply historical optimization
            if len(self.size_history) > 10:
                recent_performance = np.mean(list(self.quality_history)[-10:])
                if recent_performance < 0.7:  # Poor recent performance
                    size_multiplier *= 1.1  # Try larger chunks
            
            optimal_size = int(self.base_size * size_multiplier)
            
            # Clamp to reasonable bounds
            optimal_size = max(256, min(4096, optimal_size))
            
            return optimal_size
            
        except Exception as e:
            logger.warning(f"⚠️ Optimal size calculation failed: {e}")
            return self.base_size
    
    def update_performance(self, chunk_size: int, quality_score: float):
        """Update performance history"""
        self.size_history.append(chunk_size)
        self.quality_history.append(quality_score)
        
        # Adaptive base size adjustment
        if len(self.quality_history) >= 50:
            recent_quality = np.mean(list(self.quality_history)[-20:])
            if recent_quality > 0.8:
                self.base_size = int(self.base_size * 0.95)  # Reduce base size
            elif recent_quality < 0.6:
                self.base_size = int(self.base_size * 1.05)  # Increase base size

class ChunkCache:
    """Intelligent caching system for processed chunks"""
    
    def __init__(self, max_size_mb: int = 100):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache: Dict[str, IntelligentChunk] = {}
        self.access_times: Dict[str, float] = {}
        self.current_size = 0
        self.lock = threading.Lock()
        
    def get(self, cache_key: str) -> Optional[IntelligentChunk]:
        """Get chunk from cache"""
        with self.lock:
            if cache_key in self.cache:
                self.access_times[cache_key] = time.time()
                chunk = self.cache[cache_key]
                
                # Decompress if needed
                if isinstance(chunk.data, dict) and 'compressed' in chunk.data:
                    chunk.decompress_data()
                
                return chunk
            return None
    
    def put(self, chunk: IntelligentChunk) -> bool:
        """Put chunk in cache"""
        with self.lock:
            if chunk.cache_key in self.cache:
                return True  # Already cached
            
            # Compress before caching
            if chunk.compression_enabled:
                chunk.compress_data()
            
            chunk_size = chunk.calculate_memory_footprint()
            
            # Evict if necessary
            while self.current_size + chunk_size > self.max_size_bytes and self.cache:
                self._evict_lru()
            
            if self.current_size + chunk_size <= self.max_size_bytes:
                self.cache[chunk.cache_key] = chunk
                self.access_times[chunk.cache_key] = time.time()
                self.current_size += chunk_size
                chunk.state = ChunkState.CACHED
                return True
            
            return False
    
    def _evict_lru(self):
        """Evict least recently used chunk"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        evicted_chunk = self.cache.pop(lru_key, None)
        
        if evicted_chunk:
            self.current_size -= evicted_chunk.calculate_memory_footprint()
            del self.access_times[lru_key]
    
    def clear_session(self, session_id: str):
        """Clear all chunks for a session"""
        with self.lock:
            keys_to_remove = [
                key for key, chunk in self.cache.items()
                if chunk.session_id == session_id
            ]
            
            for key in keys_to_remove:
                chunk = self.cache.pop(key, None)
                if chunk:
                    self.current_size -= chunk.calculate_memory_footprint()
                del self.access_times[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                'total_chunks': len(self.cache),
                'current_size_mb': self.current_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'utilization': self.current_size / self.max_size_bytes,
                'sessions': len(set(chunk.session_id for chunk in self.cache.values()))
            }

class ChunkMerger:
    """Intelligent chunk merging for efficiency"""
    
    def __init__(self):
        self.merge_strategies = {
            'temporal': self._merge_temporal,
            'quality': self._merge_quality,
            'speaker': self._merge_speaker,
            'content': self._merge_content
        }
    
    def can_merge(self, chunk1: IntelligentChunk, chunk2: IntelligentChunk) -> bool:
        """Check if two chunks can be merged"""
        # Basic compatibility checks
        if (chunk1.session_id != chunk2.session_id or
            chunk1.chunk_type != chunk2.chunk_type or
            chunk1.state not in [ChunkState.QUEUED, ChunkState.PROCESSED] or
            chunk2.state not in [ChunkState.QUEUED, ChunkState.PROCESSED]):
            return False
        
        # Temporal proximity check
        time_diff = abs(chunk1.timestamp - chunk2.timestamp)
        if time_diff > 5.0:  # More than 5 seconds apart
            return False
        
        # Quality compatibility
        quality_diff = abs(chunk1.metrics.quality_score - chunk2.metrics.quality_score)
        if quality_diff > 0.3:  # Significantly different quality
            return False
        
        # Size check
        total_size = chunk1.calculate_memory_footprint() + chunk2.calculate_memory_footprint()
        if total_size > 10 * 1024 * 1024:  # Max 10MB merged chunk
            return False
        
        return True
    
    def merge_chunks(self, chunks: List[IntelligentChunk], strategy: str = 'temporal') -> Optional[IntelligentChunk]:
        """Merge multiple chunks using specified strategy"""
        if len(chunks) < 2:
            return chunks[0] if chunks else None
        
        if strategy not in self.merge_strategies:
            strategy = 'temporal'
        
        try:
            return self.merge_strategies[strategy](chunks)
        except Exception as e:
            logger.error(f"❌ Chunk merging failed: {e}")
            return None
    
    def _merge_temporal(self, chunks: List[IntelligentChunk]) -> IntelligentChunk:
        """Merge chunks in temporal order"""
        # Sort by timestamp
        sorted_chunks = sorted(chunks, key=lambda c: c.timestamp)
        
        # Create merged chunk
        merged_id = f"merged_{uuid.uuid4().hex[:8]}"
        base_chunk = sorted_chunks[0]
        
        # Merge data
        merged_data = self._concatenate_data([c.data for c in sorted_chunks])
        
        # Calculate merged metrics
        merged_metrics = self._merge_metrics([c.metrics for c in sorted_chunks])
        
        merged_chunk = IntelligentChunk(
            id=merged_id,
            session_id=base_chunk.session_id,
            data=merged_data,
            timestamp=sorted_chunks[0].timestamp,
            sequence_number=sorted_chunks[0].sequence_number,
            chunk_type=base_chunk.chunk_type,
            state=ChunkState.MERGED,
            priority=max(c.priority for c in chunks),
            metrics=merged_metrics,
            related_chunks=[c.id for c in chunks],
            metadata={
                'merged_from': [c.id for c in chunks],
                'merge_strategy': 'temporal',
                'merge_timestamp': time.time()
            }
        )
        
        return merged_chunk
    
    def _merge_quality(self, chunks: List[IntelligentChunk]) -> IntelligentChunk:
        """Merge chunks prioritizing highest quality"""
        # Sort by quality score
        sorted_chunks = sorted(chunks, key=lambda c: c.metrics.quality_score, reverse=True)
        return self._merge_temporal(sorted_chunks)
    
    def _merge_speaker(self, chunks: List[IntelligentChunk]) -> IntelligentChunk:
        """Merge chunks from same speaker"""
        # Group by speaker if available in metadata
        speaker_groups = defaultdict(list)
        for chunk in chunks:
            speaker = chunk.metadata.get('speaker_id', 'unknown')
            speaker_groups[speaker].append(chunk)
        
        # Use largest speaker group
        largest_group = max(speaker_groups.values(), key=len)
        return self._merge_temporal(largest_group)
    
    def _merge_content(self, chunks: List[IntelligentChunk]) -> IntelligentChunk:
        """Merge chunks with similar content characteristics"""
        # For now, use temporal merging
        # Could be enhanced with content similarity analysis
        return self._merge_temporal(chunks)
    
    def _concatenate_data(self, data_list: List[Union[bytes, np.ndarray]]) -> Union[bytes, np.ndarray]:
        """Concatenate chunk data"""
        if not data_list:
            return b''
        
        # Handle different data types
        first_data = data_list[0]
        
        if isinstance(first_data, bytes):
            return b''.join(data_list)
        elif isinstance(first_data, np.ndarray):
            return np.concatenate(data_list)
        else:
            # For other types, convert to bytes and concatenate
            byte_data = []
            for data in data_list:
                if isinstance(data, bytes):
                    byte_data.append(data)
                else:
                    byte_data.append(pickle.dumps(data))
            return b''.join(byte_data)
    
    def _merge_metrics(self, metrics_list: List[ChunkMetrics]) -> ChunkMetrics:
        """Merge chunk metrics"""
        if not metrics_list:
            return ChunkMetrics()
        
        merged = ChunkMetrics()
        
        # Sum additive metrics
        merged.size_bytes = sum(m.size_bytes for m in metrics_list)
        merged.duration_ms = sum(m.duration_ms for m in metrics_list)
        
        # Average other metrics
        n = len(metrics_list)
        merged.quality_score = sum(m.quality_score for m in metrics_list) / n
        merged.voice_activity = sum(m.voice_activity for m in metrics_list) / n
        merged.noise_level = sum(m.noise_level for m in metrics_list) / n
        merged.confidence_score = sum(m.confidence_score for m in metrics_list) / n
        merged.emotion_intensity = sum(m.emotion_intensity for m in metrics_list) / n
        
        # Take max for some metrics
        merged.speaker_count = max(m.speaker_count for m in metrics_list)
        
        return merged

class IntelligentChunkManager:
    """Main intelligent chunk management system"""
    
    def __init__(self, max_cache_size_mb: int = 100, worker_threads: int = 4):
        self.adaptive_sizer = AdaptiveSizer()
        self.chunk_cache = ChunkCache(max_cache_size_mb)
        self.chunk_merger = ChunkMerger()
        
        # Chunk storage
        self.active_chunks: Dict[str, IntelligentChunk] = {}
        self.processing_queue = deque()
        self.completed_chunks: Dict[str, IntelligentChunk] = {}
        
        # Processing infrastructure
        self.executor = ThreadPoolExecutor(max_workers=worker_threads)
        self.processing_callbacks: List[Callable] = []
        self.quality_filters: List[Callable] = []
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.performance_metrics = {
            'chunks_processed': 0,
            'chunks_merged': 0,
            'chunks_cached': 0,
            'avg_processing_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        self.lock = threading.Lock()
        
        # Start background processors
        self._start_background_workers()
        
        logger.info("🧠 Intelligent Chunk Manager initialized with advanced features")
    
    def _start_background_workers(self):
        """Start background processing workers"""
        # Chunk processor worker
        self.processor_thread = threading.Thread(target=self._process_queue_worker, daemon=True)
        self.processor_thread.start()
        
        # Merge optimizer worker
        self.merger_thread = threading.Thread(target=self._merge_optimizer_worker, daemon=True)
        self.merger_thread.start()
        
        # Cache maintenance worker
        self.maintenance_thread = threading.Thread(target=self._cache_maintenance_worker, daemon=True)
        self.maintenance_thread.start()
    
    def create_session(self, session_id: str, **config) -> Dict[str, Any]:
        """Create new chunk management session"""
        with self.lock:
            session_info = {
                'id': session_id,
                'created_at': time.time(),
                'config': config,
                'chunk_count': 0,
                'total_size': 0,
                'processing_stats': {
                    'queued': 0,
                    'processing': 0,
                    'processed': 0,
                    'failed': 0,
                    'cached': 0,
                    'merged': 0
                }
            }
            
            self.sessions[session_id] = session_info
            self.session_stats[session_id] = {}
            
            logger.info(f"📝 Created intelligent chunk session: {session_id}")
            return session_info
    
    def add_chunk(self, chunk: IntelligentChunk) -> bool:
        """Add chunk to management system"""
        try:
            # Check cache first
            cached_chunk = self.chunk_cache.get(chunk.cache_key)
            if cached_chunk:
                self._update_session_stats(chunk.session_id, 'cache_hit')
                return True
            
            # Calculate optimal size if needed
            if hasattr(chunk.data, 'shape') and isinstance(chunk.data, np.ndarray):
                session_context = self.sessions.get(chunk.session_id, {}).get('config', {})
                optimal_size = self.adaptive_sizer.calculate_optimal_size(
                    chunk.data, 16000, session_context
                )
                chunk.metadata['optimal_size'] = optimal_size
            
            # Apply quality filters
            if not self._passes_quality_filters(chunk):
                chunk.state = ChunkState.DISCARDED
                return False
            
            # Add to active chunks
            with self.lock:
                self.active_chunks[chunk.id] = chunk
                self.processing_queue.append(chunk.id)
                
                # Update session stats
                self._update_session_stats(chunk.session_id, 'chunk_added')
            
            logger.debug(f"✅ Added chunk to management: {chunk.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add chunk: {e}")
            return False
    
    def _passes_quality_filters(self, chunk: IntelligentChunk) -> bool:
        """Check if chunk passes quality filters"""
        for quality_filter in self.quality_filters:
            try:
                if not quality_filter(chunk):
                    return False
            except Exception as e:
                logger.warning(f"⚠️ Quality filter failed: {e}")
                continue
        
        # Default quality checks
        if chunk.metrics.quality_score < 0.3:
            return False
        
        if chunk.metrics.voice_activity < 0.1:
            return False
        
        return True
    
    def _process_queue_worker(self):
        """Background worker for processing chunks"""
        while True:
            try:
                if not self.processing_queue:
                    time.sleep(0.1)
                    continue
                
                with self.lock:
                    if self.processing_queue:
                        chunk_id = self.processing_queue.popleft()
                    else:
                        continue
                
                chunk = self.active_chunks.get(chunk_id)
                if not chunk or not chunk.is_ready_for_processing():
                    continue
                
                # Process chunk
                self._process_chunk(chunk)
                
            except Exception as e:
                logger.error(f"❌ Chunk processing worker error: {e}")
                time.sleep(1)
    
    def _process_chunk(self, chunk: IntelligentChunk):
        """Process individual chunk"""
        try:
            start_time = time.time()
            chunk.state = ChunkState.PROCESSING
            chunk.processing_attempts += 1
            
            # Call processing callbacks
            for callback in self.processing_callbacks:
                try:
                    callback(chunk)
                except Exception as e:
                    logger.warning(f"⚠️ Processing callback failed: {e}")
            
            # Calculate processing metrics
            processing_time = (time.time() - start_time) * 1000
            chunk.metrics.processing_time_ms = processing_time
            chunk.processed_at = time.time()
            chunk.state = ChunkState.PROCESSED
            
            # Cache successful processing
            self.chunk_cache.put(chunk)
            
            # Move to completed
            with self.lock:
                self.completed_chunks[chunk.id] = chunk
                if chunk.id in self.active_chunks:
                    del self.active_chunks[chunk.id]
            
            # Update adaptive sizer
            self.adaptive_sizer.update_performance(
                chunk.calculate_memory_footprint(),
                chunk.metrics.quality_score
            )
            
            # Update performance metrics
            self._update_performance_metrics(processing_time)
            self._update_session_stats(chunk.session_id, 'processed')
            
            logger.debug(f"✅ Processed chunk: {chunk.id} ({processing_time:.1f}ms)")
            
        except Exception as e:
            logger.error(f"❌ Chunk processing failed: {e}")
            chunk.state = ChunkState.FAILED
            self._update_session_stats(chunk.session_id, 'failed')
    
    def _merge_optimizer_worker(self):
        """Background worker for chunk merging optimization"""
        while True:
            try:
                time.sleep(5)  # Check every 5 seconds
                
                # Find mergeable chunks for each session
                for session_id in list(self.sessions.keys()):
                    session_chunks = [
                        chunk for chunk in self.completed_chunks.values()
                        if chunk.session_id == session_id and chunk.state == ChunkState.PROCESSED
                    ]
                    
                    if len(session_chunks) >= 2:
                        self._optimize_session_chunks(session_id, session_chunks)
                
            except Exception as e:
                logger.error(f"❌ Merge optimizer error: {e}")
    
    def _optimize_session_chunks(self, session_id: str, chunks: List[IntelligentChunk]):
        """Optimize chunks for a session through merging"""
        try:
            # Group mergeable chunks
            merge_groups = []
            remaining_chunks = chunks.copy()
            
            while len(remaining_chunks) >= 2:
                current_chunk = remaining_chunks.pop(0)
                merge_group = [current_chunk]
                
                # Find compatible chunks
                compatible = []
                for chunk in remaining_chunks[:]:
                    if self.chunk_merger.can_merge(current_chunk, chunk):
                        compatible.append(chunk)
                        remaining_chunks.remove(chunk)
                        
                        if len(compatible) >= 3:  # Limit merge group size
                            break
                
                if compatible:
                    merge_group.extend(compatible)
                    merge_groups.append(merge_group)
            
            # Perform merges
            for merge_group in merge_groups:
                if len(merge_group) >= 2:
                    merged_chunk = self.chunk_merger.merge_chunks(merge_group)
                    if merged_chunk:
                        self._handle_merged_chunk(merged_chunk, merge_group)
            
        except Exception as e:
            logger.error(f"❌ Session chunk optimization failed: {e}")
    
    def _handle_merged_chunk(self, merged_chunk: IntelligentChunk, original_chunks: List[IntelligentChunk]):
        """Handle successful chunk merge"""
        with self.lock:
            # Add merged chunk
            self.completed_chunks[merged_chunk.id] = merged_chunk
            
            # Remove original chunks
            for chunk in original_chunks:
                self.completed_chunks.pop(chunk.id, None)
                self.active_chunks.pop(chunk.id, None)
            
            # Update stats
            self.performance_metrics['chunks_merged'] += 1
            self._update_session_stats(merged_chunk.session_id, 'merged')
        
        logger.info(f"🔗 Merged {len(original_chunks)} chunks into {merged_chunk.id}")
    
    def _cache_maintenance_worker(self):
        """Background worker for cache maintenance"""
        while True:
            try:
                time.sleep(30)  # Maintenance every 30 seconds
                
                # Clean up old completed chunks
                cutoff_time = time.time() - 3600  # 1 hour old
                old_chunks = [
                    chunk_id for chunk_id, chunk in self.completed_chunks.items()
                    if chunk.processed_at and chunk.processed_at < cutoff_time
                ]
                
                with self.lock:
                    for chunk_id in old_chunks:
                        self.completed_chunks.pop(chunk_id, None)
                
                if old_chunks:
                    logger.info(f"🧹 Cleaned up {len(old_chunks)} old chunks")
                
            except Exception as e:
                logger.error(f"❌ Cache maintenance error: {e}")
    
    def _update_session_stats(self, session_id: str, event_type: str):
        """Update session statistics"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        if event_type == 'chunk_added':
            session['chunk_count'] += 1
        elif event_type in session['processing_stats']:
            session['processing_stats'][event_type] += 1
    
    def _update_performance_metrics(self, processing_time: float):
        """Update global performance metrics"""
        self.performance_metrics['chunks_processed'] += 1
        
        # Update average processing time
        total = self.performance_metrics['chunks_processed']
        current_avg = self.performance_metrics['avg_processing_time']
        self.performance_metrics['avg_processing_time'] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def add_processing_callback(self, callback: Callable[[IntelligentChunk], None]):
        """Add processing callback"""
        self.processing_callbacks.append(callback)
    
    def add_quality_filter(self, filter_func: Callable[[IntelligentChunk], bool]):
        """Add quality filter"""
        self.quality_filters.append(filter_func)
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session analytics"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        session_chunks = [
            chunk for chunk in list(self.active_chunks.values()) + list(self.completed_chunks.values())
            if chunk.session_id == session_id
        ]
        
        if not session_chunks:
            return session
        
        # Calculate analytics
        analytics = {
            **session,
            'analytics': {
                'total_chunks': len(session_chunks),
                'avg_quality': np.mean([c.metrics.quality_score for c in session_chunks]),
                'avg_processing_time': np.mean([c.metrics.processing_time_ms for c in session_chunks if c.metrics.processing_time_ms > 0]),
                'total_size_mb': sum(c.calculate_memory_footprint() for c in session_chunks) / (1024 * 1024),
                'compression_ratio': np.mean([c.metrics.compression_ratio for c in session_chunks]),
                'cache_stats': self.chunk_cache.get_stats()
            }
        }
        
        return analytics
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        cache_stats = self.chunk_cache.get_stats()
        
        return {
            'performance_metrics': self.performance_metrics,
            'cache_stats': cache_stats,
            'active_chunks': len(self.active_chunks),
            'completed_chunks': len(self.completed_chunks),
            'processing_queue_size': len(self.processing_queue),
            'active_sessions': len(self.sessions)
        }
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End session and cleanup"""
        final_analytics = self.get_session_analytics(session_id)
        
        # Cleanup session chunks
        with self.lock:
            session_chunk_ids = [
                chunk_id for chunk_id, chunk in {**self.active_chunks, **self.completed_chunks}.items()
                if chunk.session_id == session_id
            ]
            
            for chunk_id in session_chunk_ids:
                self.active_chunks.pop(chunk_id, None)
                self.completed_chunks.pop(chunk_id, None)
            
            # Clear cache
            self.chunk_cache.clear_session(session_id)
            
            # Remove session
            self.sessions.pop(session_id, None)
            self.session_stats.pop(session_id, None)
        
        logger.info(f"🏁 Ended intelligent chunk session: {session_id}")
        return final_analytics

# Global manager instance
_chunk_manager = None
_manager_lock = threading.Lock()

def get_intelligent_chunk_manager(**config) -> IntelligentChunkManager:
    """Get global intelligent chunk manager instance"""
    global _chunk_manager
    
    with _manager_lock:
        if _chunk_manager is None:
            _chunk_manager = IntelligentChunkManager(**config)
        return _chunk_manager

logger.info("✅ Intelligent Chunk Manager module initialized")