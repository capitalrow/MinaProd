"""
Latency Optimization Engine - Google Recorder Level Performance
Advanced pipeline optimization for <400ms end-to-end transcription latency.
Implements parallel processing, intelligent buffering, and performance monitoring.
"""

import logging
import time
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class LatencyMeasurement:
    """Latency measurement for pipeline stages."""
    stage_name: str
    start_time: float
    end_time: float
    duration: float
    chunk_id: int
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PipelineStage:
    """Pipeline processing stage configuration."""
    name: str
    processor: Callable
    parallel: bool = True
    max_workers: int = 2
    queue_size: int = 10
    timeout: float = 1.0
    priority: int = 0

class LatencyOptimizationEngine:
    """
    ⚡ Google Recorder-level latency optimization engine.
    
    Implements advanced pipeline parallelization, intelligent buffering,
    and real-time performance monitoring for <400ms transcription latency.
    """
    
    def __init__(self, target_latency_ms: float = 400.0):
        self.target_latency_ms = target_latency_ms
        self.target_latency_s = target_latency_ms / 1000.0
        
        # Pipeline configuration
        self.pipeline_stages: List[PipelineStage] = []
        self.stage_executors: Dict[str, ThreadPoolExecutor] = {}
        self.stage_queues: Dict[str, queue.Queue] = {}
        
        # Performance tracking
        self.latency_measurements = deque(maxlen=1000)
        self.stage_performance = {}
        self.bottleneck_analysis = {}
        
        # Optimization state
        self.optimization_active = False
        self.performance_thread = None
        self.adaptive_scaling = True
        
        # Buffering and batching
        self.input_buffer = queue.Queue(maxsize=50)
        self.output_buffer = queue.Queue(maxsize=50)
        self.batch_size = 1
        self.max_batch_size = 3
        
        # Real-time monitoring
        self.latency_history = deque(maxlen=100)
        self.throughput_history = deque(maxlen=100)
        
        logger.info(f"⚡ Latency Optimization Engine initialized (target: {target_latency_ms}ms)")
    
    def initialize_pipeline(self, stages: List[PipelineStage]):
        """🔧 Initialize optimized processing pipeline."""
        try:
            self.pipeline_stages = sorted(stages, key=lambda x: x.priority)
            
            # Create executors and queues for each stage
            for stage in self.pipeline_stages:
                if stage.parallel:
                    self.stage_executors[stage.name] = ThreadPoolExecutor(
                        max_workers=stage.max_workers,
                        thread_name_prefix=f"stage_{stage.name}"
                    )
                
                self.stage_queues[stage.name] = queue.Queue(maxsize=stage.queue_size)
                
                # Initialize performance tracking
                self.stage_performance[stage.name] = {
                    'total_time': 0.0,
                    'total_chunks': 0,
                    'avg_latency': 0.0,
                    'error_count': 0,
                    'queue_overflows': 0
                }
            
            logger.info(f"🔧 Pipeline initialized with {len(stages)} stages")
            
        except Exception as e:
            logger.error(f"❌ Pipeline initialization failed: {e}")
            raise
    
    def start_optimization(self):
        """🚀 Start latency optimization and monitoring."""
        if not self.optimization_active:
            self.optimization_active = True
            
            # Start performance monitoring thread
            self.performance_thread = threading.Thread(
                target=self._monitor_performance_continuously,
                daemon=True
            )
            self.performance_thread.start()
            
            logger.info("🚀 Latency optimization started")
    
    def stop_optimization(self):
        """⏹️ Stop latency optimization."""
        self.optimization_active = False
        
        if self.performance_thread and self.performance_thread.is_alive():
            self.performance_thread.join(timeout=1.0)
        
        # Shutdown executors
        for executor in self.stage_executors.values():
            executor.shutdown(wait=False)
        
        logger.info("⏹️ Latency optimization stopped")
    
    async def process_chunk_optimized(self, audio_chunk: Any, 
                                    session_id: str, 
                                    chunk_id: int) -> Dict[str, Any]:
        """
        ⚡ Process audio chunk with optimized latency pipeline.
        
        Args:
            audio_chunk: Audio data to process
            session_id: Session identifier
            chunk_id: Chunk sequence number
            
        Returns:
            Processing result with latency metrics
        """
        start_time = time.time()
        
        try:
            # === PARALLEL PIPELINE EXECUTION ===
            
            # Create processing context
            context = {
                'audio_chunk': audio_chunk,
                'session_id': session_id,
                'chunk_id': chunk_id,
                'start_time': start_time,
                'stage_results': {},
                'latency_breakdown': {}
            }
            
            # Execute pipeline stages with optimization
            result = await self._execute_optimized_pipeline(context)
            
            # Calculate total latency
            total_latency = time.time() - start_time
            
            # Record performance metrics
            self._record_latency_measurement(
                total_latency, session_id, chunk_id, result
            )
            
            # Check if we're meeting target latency
            latency_ms = total_latency * 1000
            meets_target = latency_ms <= self.target_latency_ms
            
            # Trigger adaptive optimization if needed
            if not meets_target and self.adaptive_scaling:
                await self._trigger_adaptive_optimization(latency_ms, context)
            
            return {
                'success': True,
                'result': result,
                'latency_ms': latency_ms,
                'meets_target': meets_target,
                'stage_latencies': context['latency_breakdown'],
                'optimization_applied': self.adaptive_scaling
            }
            
        except Exception as e:
            logger.error(f"❌ Optimized processing failed for chunk {chunk_id}: {e}")
            
            fallback_latency = (time.time() - start_time) * 1000
            return {
                'success': False,
                'error': str(e),
                'latency_ms': fallback_latency,
                'meets_target': False,
                'fallback': True
            }
    
    async def _execute_optimized_pipeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🔄 Execute pipeline with latency optimization."""
        try:
            # Check if we can use parallel execution
            if len(self.pipeline_stages) > 1 and self._can_parallelize():
                return await self._execute_parallel_pipeline(context)
            else:
                return await self._execute_sequential_pipeline(context)
                
        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}")
            raise
    
    async def _execute_parallel_pipeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """⚡ Execute pipeline with parallel stage processing."""
        try:
            # Group stages that can run in parallel
            parallel_groups = self._group_parallel_stages()
            
            results = {}
            
            for group in parallel_groups:
                if len(group) == 1:
                    # Single stage - execute directly
                    stage = group[0]
                    stage_result = await self._execute_single_stage(stage, context)
                    results[stage.name] = stage_result
                    context['stage_results'][stage.name] = stage_result
                else:
                    # Multiple stages - execute in parallel
                    group_results = await self._execute_stage_group_parallel(group, context)
                    results.update(group_results)
                    context['stage_results'].update(group_results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Parallel pipeline execution failed: {e}")
            raise
    
    async def _execute_sequential_pipeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🔄 Execute pipeline sequentially with optimization."""
        try:
            results = {}
            
            for stage in self.pipeline_stages:
                stage_result = await self._execute_single_stage(stage, context)
                results[stage.name] = stage_result
                context['stage_results'][stage.name] = stage_result
                
                # Pass result to next stage
                if 'output' in stage_result:
                    context['audio_chunk'] = stage_result['output']
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Sequential pipeline execution failed: {e}")
            raise
    
    async def _execute_single_stage(self, stage: PipelineStage, 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """🎯 Execute single pipeline stage with latency tracking."""
        stage_start = time.time()
        
        try:
            if stage.parallel and stage.name in self.stage_executors:
                # Execute in thread pool
                executor = self.stage_executors[stage.name]
                loop = asyncio.get_event_loop()
                
                # Submit to executor with timeout
                future = loop.run_in_executor(
                    executor, 
                    self._execute_stage_with_timeout,
                    stage, context
                )
                
                result = await asyncio.wait_for(future, timeout=stage.timeout)
            else:
                # Execute directly
                result = stage.processor(context)
            
            # Record stage latency
            stage_latency = time.time() - stage_start
            context['latency_breakdown'][stage.name] = stage_latency * 1000
            
            # Update stage performance
            self._update_stage_performance(stage.name, stage_latency, True)
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Stage {stage.name} timed out after {stage.timeout}s")
            
            # Update error count
            self._update_stage_performance(stage.name, stage.timeout, False)
            
            return {
                'success': False,
                'error': 'timeout',
                'stage': stage.name
            }
            
        except Exception as e:
            stage_latency = time.time() - stage_start
            logger.error(f"❌ Stage {stage.name} failed: {e}")
            
            # Update error count
            self._update_stage_performance(stage.name, stage_latency, False)
            
            return {
                'success': False,
                'error': str(e),
                'stage': stage.name
            }
    
    def _execute_stage_with_timeout(self, stage: PipelineStage, 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute stage with timeout handling."""
        try:
            return stage.processor(context)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': stage.name
            }
    
    async def _execute_stage_group_parallel(self, stages: List[PipelineStage], 
                                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute group of stages in parallel."""
        try:
            # Create tasks for parallel execution
            tasks = []
            for stage in stages:
                task = self._execute_single_stage(stage, context.copy())
                tasks.append((stage.name, task))
            
            # Wait for all tasks to complete
            results = {}
            for stage_name, task in tasks:
                try:
                    result = await task
                    results[stage_name] = result
                except Exception as e:
                    logger.error(f"❌ Parallel stage {stage_name} failed: {e}")
                    results[stage_name] = {
                        'success': False,
                        'error': str(e),
                        'stage': stage_name
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Parallel stage group execution failed: {e}")
            raise
    
    def _can_parallelize(self) -> bool:
        """🔍 Check if pipeline can be parallelized."""
        try:
            # Simple check - at least 2 stages and some are marked as parallel
            parallel_stages = [s for s in self.pipeline_stages if s.parallel]
            return len(parallel_stages) >= 2
            
        except Exception:
            return False
    
    def _group_parallel_stages(self) -> List[List[PipelineStage]]:
        """📊 Group stages that can run in parallel."""
        try:
            # Simple grouping by priority
            groups = []
            current_group = []
            current_priority = None
            
            for stage in self.pipeline_stages:
                if current_priority is None or stage.priority == current_priority:
                    current_group.append(stage)
                    current_priority = stage.priority
                else:
                    if current_group:
                        groups.append(current_group)
                    current_group = [stage]
                    current_priority = stage.priority
            
            if current_group:
                groups.append(current_group)
            
            return groups
            
        except Exception as e:
            logger.error(f"❌ Stage grouping failed: {e}")
            return [[stage] for stage in self.pipeline_stages]
    
    async def _trigger_adaptive_optimization(self, latency_ms: float, 
                                           context: Dict[str, Any]):
        """🎯 Trigger adaptive optimization based on performance."""
        try:
            # Analyze bottlenecks
            bottlenecks = self._analyze_pipeline_bottlenecks(context)
            
            # Apply optimizations
            optimizations_applied = []
            
            for bottleneck in bottlenecks:
                optimization = await self._apply_stage_optimization(bottleneck)
                if optimization['applied']:
                    optimizations_applied.append(optimization)
            
            # Adjust batch size if needed
            if latency_ms > self.target_latency_ms * 1.5:  # 50% over target
                await self._optimize_batch_processing()
                optimizations_applied.append({'type': 'batch_optimization'})
            
            if optimizations_applied:
                logger.info(f"🎯 Applied {len(optimizations_applied)} optimizations for latency {latency_ms:.1f}ms")
            
        except Exception as e:
            logger.warning(f"⚠️ Adaptive optimization failed: {e}")
    
    def _analyze_pipeline_bottlenecks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """🔍 Analyze pipeline bottlenecks."""
        try:
            bottlenecks = []
            latency_breakdown = context.get('latency_breakdown', {})
            
            # Find stages taking more than 30% of target latency
            threshold_ms = self.target_latency_ms * 0.3
            
            for stage_name, stage_latency_ms in latency_breakdown.items():
                if stage_latency_ms > threshold_ms:
                    bottleneck_severity = stage_latency_ms / threshold_ms
                    
                    bottlenecks.append({
                        'stage': stage_name,
                        'latency_ms': stage_latency_ms,
                        'severity': bottleneck_severity,
                        'threshold_ratio': stage_latency_ms / self.target_latency_ms
                    })
            
            # Sort by severity
            bottlenecks.sort(key=lambda x: x['severity'], reverse=True)
            
            return bottlenecks
            
        except Exception as e:
            logger.warning(f"⚠️ Bottleneck analysis failed: {e}")
            return []
    
    async def _apply_stage_optimization(self, bottleneck: Dict[str, Any]) -> Dict[str, Any]:
        """🔧 Apply optimization to bottleneck stage."""
        try:
            stage_name = bottleneck['stage']
            optimization_applied = False
            
            # Find the stage
            stage = next((s for s in self.pipeline_stages if s.name == stage_name), None)
            if not stage:
                return {'applied': False, 'reason': 'stage_not_found'}
            
            # Optimization strategies
            if stage.parallel and stage_name in self.stage_executors:
                # Increase thread pool size
                current_workers = self.stage_executors[stage_name]._max_workers
                if current_workers < 4:  # Max 4 workers per stage
                    self.stage_executors[stage_name]._max_workers = min(4, current_workers + 1)
                    optimization_applied = True
                    logger.info(f"🔧 Increased workers for {stage_name} to {current_workers + 1}")
            
            # Reduce timeout for faster failure
            if stage.timeout > 0.5:
                stage.timeout = max(0.5, stage.timeout * 0.8)
                optimization_applied = True
                logger.info(f"🔧 Reduced timeout for {stage_name} to {stage.timeout:.2f}s")
            
            return {
                'applied': optimization_applied,
                'stage': stage_name,
                'optimizations': ['worker_scaling', 'timeout_reduction']
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Stage optimization failed: {e}")
            return {'applied': False, 'error': str(e)}
    
    async def _optimize_batch_processing(self):
        """📦 Optimize batch processing parameters."""
        try:
            # Reduce batch size for lower latency
            if self.batch_size > 1:
                self.batch_size = max(1, self.batch_size - 1)
                logger.info(f"📦 Reduced batch size to {self.batch_size}")
            
        except Exception as e:
            logger.warning(f"⚠️ Batch optimization failed: {e}")
    
    def _record_latency_measurement(self, latency: float, session_id: str, 
                                  chunk_id: int, result: Dict[str, Any]):
        """📊 Record latency measurement."""
        try:
            measurement = LatencyMeasurement(
                stage_name='total_pipeline',
                start_time=time.time() - latency,
                end_time=time.time(),
                duration=latency,
                chunk_id=chunk_id,
                session_id=session_id,
                metadata={
                    'latency_ms': latency * 1000,
                    'meets_target': latency <= self.target_latency_s,
                    'stage_count': len(self.pipeline_stages)
                }
            )
            
            self.latency_measurements.append(measurement)
            self.latency_history.append(latency * 1000)
            
            # Update throughput
            throughput = 1.0 / latency if latency > 0 else 0
            self.throughput_history.append(throughput)
            
        except Exception as e:
            logger.warning(f"⚠️ Latency recording failed: {e}")
    
    def _update_stage_performance(self, stage_name: str, latency: float, success: bool):
        """📈 Update stage performance metrics."""
        try:
            if stage_name not in self.stage_performance:
                self.stage_performance[stage_name] = {
                    'total_time': 0.0,
                    'total_chunks': 0,
                    'avg_latency': 0.0,
                    'error_count': 0,
                    'queue_overflows': 0
                }
            
            stats = self.stage_performance[stage_name]
            
            if success:
                stats['total_time'] += latency
                stats['total_chunks'] += 1
                stats['avg_latency'] = stats['total_time'] / stats['total_chunks']
            else:
                stats['error_count'] += 1
                
        except Exception as e:
            logger.warning(f"⚠️ Stage performance update failed: {e}")
    
    def _monitor_performance_continuously(self):
        """📊 Continuously monitor and analyze performance."""
        while self.optimization_active:
            try:
                time.sleep(1.0)  # Check every second
                
                # Analyze recent performance
                recent_latencies = list(self.latency_history)[-10:]  # Last 10 measurements
                
                if len(recent_latencies) >= 5:
                    avg_latency = np.mean(recent_latencies)
                    
                    # Check if we're consistently over target
                    over_target_ratio = sum(1 for l in recent_latencies if l > self.target_latency_ms) / len(recent_latencies)
                    
                    if over_target_ratio > 0.6:  # More than 60% over target
                        logger.warning(f"⚠️ Performance degradation detected: {avg_latency:.1f}ms avg latency")
                        # Could trigger automatic optimization here
                
            except Exception as e:
                logger.warning(f"⚠️ Performance monitoring error: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """📊 Get comprehensive performance report."""
        try:
            recent_latencies = list(self.latency_history)[-50:]  # Last 50 measurements
            
            if not recent_latencies:
                return {'status': 'no_data'}
            
            # Calculate statistics
            avg_latency = np.mean(recent_latencies)
            p50_latency = np.percentile(recent_latencies, 50)
            p95_latency = np.percentile(recent_latencies, 95)
            p99_latency = np.percentile(recent_latencies, 99)
            
            # Performance metrics
            meets_target_ratio = sum(1 for l in recent_latencies if l <= self.target_latency_ms) / len(recent_latencies)
            
            # Stage performance
            stage_stats = {}
            for stage_name, stats in self.stage_performance.items():
                if stats['total_chunks'] > 0:
                    stage_stats[stage_name] = {
                        'avg_latency_ms': stats['avg_latency'] * 1000,
                        'total_chunks': stats['total_chunks'],
                        'error_rate': stats['error_count'] / (stats['total_chunks'] + stats['error_count']),
                        'success_rate': stats['total_chunks'] / (stats['total_chunks'] + stats['error_count'])
                    }
            
            return {
                'overall_performance': {
                    'avg_latency_ms': avg_latency,
                    'p50_latency_ms': p50_latency,
                    'p95_latency_ms': p95_latency,
                    'p99_latency_ms': p99_latency,
                    'target_latency_ms': self.target_latency_ms,
                    'meets_target_ratio': meets_target_ratio,
                    'measurements_count': len(recent_latencies)
                },
                'stage_performance': stage_stats,
                'optimization_status': {
                    'adaptive_scaling': self.adaptive_scaling,
                    'current_batch_size': self.batch_size,
                    'active_stages': len(self.pipeline_stages),
                    'parallel_executors': len(self.stage_executors)
                },
                'system_health': {
                    'input_buffer_size': self.input_buffer.qsize(),
                    'output_buffer_size': self.output_buffer.qsize(),
                    'optimization_active': self.optimization_active
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Performance report generation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def reset_performance_data(self):
        """🔄 Reset performance tracking data."""
        self.latency_measurements.clear()
        self.latency_history.clear()
        self.throughput_history.clear()
        
        for stage_name in self.stage_performance:
            self.stage_performance[stage_name] = {
                'total_time': 0.0,
                'total_chunks': 0,
                'avg_latency': 0.0,
                'error_count': 0,
                'queue_overflows': 0
            }
        
        logger.info("🔄 Performance data reset")