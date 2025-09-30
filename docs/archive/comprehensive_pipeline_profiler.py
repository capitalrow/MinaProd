#!/usr/bin/env python3
"""
Comprehensive Live Transcription Pipeline Profiler
End-to-end performance monitoring, QA metrics, and system analysis
"""

import json
import time
import requests
import base64
import logging
import threading
import queue
import statistics
import psutil
import os
import wave
import struct
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import concurrent.futures
import hashlib

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_profiler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PipelineProfiler')

@dataclass
class ChunkMetrics:
    """Metrics for individual audio chunks"""
    chunk_id: str
    session_id: str
    timestamp: datetime
    audio_size_bytes: int
    processing_latency_ms: float
    api_latency_ms: float
    total_latency_ms: float
    success: bool
    transcribed_text: str = ""
    confidence_score: float = 0.0
    word_count: int = 0
    error_message: str = ""
    is_duplicate: bool = False
    is_filtered: bool = False

@dataclass
class SessionMetrics:
    """End-to-end session performance metrics"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_chunks: int = 0
    successful_chunks: int = 0
    dropped_chunks: int = 0
    duplicate_chunks: int = 0
    filtered_chunks: int = 0
    total_words: int = 0
    cumulative_text: str = ""
    final_transcript: str = ""
    
    # Performance metrics
    avg_chunk_latency_ms: float = 0.0
    p95_chunk_latency_ms: float = 0.0
    max_chunk_latency_ms: float = 0.0
    min_chunk_latency_ms: float = float('inf')
    
    # Quality metrics
    avg_confidence: float = 0.0
    word_error_rate: float = 0.0
    text_stability_score: float = 0.0
    
    # System metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    @property
    def success_rate(self) -> float:
        return (self.successful_chunks / self.total_chunks * 100) if self.total_chunks > 0 else 0.0
    
    @property
    def duration_seconds(self) -> float:
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def words_per_minute(self) -> float:
        if self.duration_seconds == 0:
            return 0.0
        return (self.total_words / self.duration_seconds) * 60

class AudioGenerator:
    """Generate test audio in various formats for pipeline testing"""
    
    @staticmethod
    def generate_sine_wave_wav(frequency: float = 440.0, duration: float = 1.0, 
                              sample_rate: int = 16000) -> bytes:
        """Generate a sine wave WAV file"""
        samples = []
        for i in range(int(sample_rate * duration)):
            t = float(i) / sample_rate
            sample = int(32767 * math.sin(2 * math.pi * frequency * t))
            samples.append(sample)

        # Create WAV file data
        wav_data = b'RIFF'
        wav_data += struct.pack('<I', 36 + len(samples) * 2)  # File size
        wav_data += b'WAVE'
        wav_data += b'fmt '
        wav_data += struct.pack('<I', 16)  # Subchunk size
        wav_data += struct.pack('<H', 1)   # Audio format (PCM)
        wav_data += struct.pack('<H', 1)   # Number of channels
        wav_data += struct.pack('<I', sample_rate)  # Sample rate
        wav_data += struct.pack('<I', sample_rate * 2)  # Byte rate
        wav_data += struct.pack('<H', 2)   # Block align
        wav_data += struct.pack('<H', 16)  # Bits per sample
        wav_data += b'data'
        wav_data += struct.pack('<I', len(samples) * 2)  # Data size

        for sample in samples:
            wav_data += struct.pack('<h', sample)

        return wav_data
    
    @staticmethod
    def generate_speech_pattern_wav(words: List[str], sample_rate: int = 16000) -> bytes:
        """Generate audio pattern that simulates speech cadence"""
        total_duration = len(words) * 0.8  # 0.8 seconds per word
        samples = []
        
        for i, word in enumerate(words):
            word_start = i * 0.8
            word_duration = 0.5  # Active speech
            silence_duration = 0.3  # Pause between words
            
            # Generate word audio (multiple frequencies for complexity)
            for j in range(int(sample_rate * word_duration)):
                t = (word_start + float(j) / sample_rate)
                # Combine multiple frequencies to simulate speech
                fundamental = 150 + (i * 20)  # Varying fundamental frequency
                harmonic1 = fundamental * 2
                harmonic2 = fundamental * 3
                
                sample = int(16000 * (
                    0.5 * math.sin(2 * math.pi * fundamental * t) +
                    0.3 * math.sin(2 * math.pi * harmonic1 * t) +
                    0.2 * math.sin(2 * math.pi * harmonic2 * t)
                ))
                samples.append(max(-32767, min(32767, sample)))
            
            # Add silence
            for j in range(int(sample_rate * silence_duration)):
                samples.append(0)
        
        # Create WAV file
        wav_data = b'RIFF'
        wav_data += struct.pack('<I', 36 + len(samples) * 2)
        wav_data += b'WAVE'
        wav_data += b'fmt '
        wav_data += struct.pack('<I', 16)
        wav_data += struct.pack('<H', 1)   # PCM
        wav_data += struct.pack('<H', 1)   # Mono
        wav_data += struct.pack('<I', sample_rate)
        wav_data += struct.pack('<I', sample_rate * 2)
        wav_data += struct.pack('<H', 2)
        wav_data += struct.pack('<H', 16)
        wav_data += b'data'
        wav_data += struct.pack('<I', len(samples) * 2)

        for sample in samples:
            wav_data += struct.pack('<h', sample)

        return wav_data

class PipelineProfiler:
    """Comprehensive pipeline profiler with real-time monitoring"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.transcription_url = f"{base_url}/api/transcribe-audio"
        
        # Data structures
        self.sessions: Dict[str, SessionMetrics] = {}
        self.chunk_history: deque = deque(maxlen=10000)
        self.latency_measurements: deque = deque(maxlen=1000)
        self.error_patterns: defaultdict = defaultdict(int)
        
        # Performance tracking
        self.system_metrics_history: deque = deque(maxlen=100)
        self.duplicate_detector = {}  # chunk_hash -> timestamp
        
        # Quality assessment
        self.reference_transcripts = {}  # session_id -> expected_text
        
        logger.info("🚀 Pipeline Profiler initialized")
    
    def create_session(self, session_id: str, reference_text: str = "") -> SessionMetrics:
        """Create a new session for tracking"""
        session = SessionMetrics(
            session_id=session_id,
            start_time=datetime.now()
        )
        self.sessions[session_id] = session
        
        if reference_text:
            self.reference_transcripts[session_id] = reference_text
        
        logger.info(f"📋 Created session {session_id}")
        return session
    
    def process_chunk(self, session_id: str, audio_data: bytes, 
                     chunk_number: int, expected_text: str = "") -> ChunkMetrics:
        """Process a single audio chunk and collect comprehensive metrics"""
        chunk_id = f"{session_id}_{chunk_number}_{int(time.time())}"
        start_time = time.time()
        
        # Check for duplicates
        chunk_hash = hashlib.md5(audio_data).hexdigest()
        is_duplicate = chunk_hash in self.duplicate_detector
        if is_duplicate:
            self.duplicate_detector[chunk_hash].append(datetime.now())
        else:
            self.duplicate_detector[chunk_hash] = [datetime.now()]
        
        # Encode audio
        b64_audio = base64.b64encode(audio_data).decode('utf-8')
        
        # Prepare request
        payload = {
            'session_id': session_id,
            'audio_data': b64_audio,
            'chunk_number': chunk_number,
            'is_final': False
        }
        
        # Send request and measure latency
        api_start = time.time()
        try:
            response = requests.post(
                self.transcription_url,
                json=payload,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            api_latency = (time.time() - api_start) * 1000
            processing_latency = api_latency  # For now, same as API latency
            
        except requests.exceptions.Timeout:
            api_latency = (time.time() - api_start) * 1000
            processing_latency = api_latency
            response = None
        except Exception as e:
            api_latency = (time.time() - api_start) * 1000
            processing_latency = api_latency
            response = None
        
        total_latency = (time.time() - start_time) * 1000
        
        # Parse response
        success = False
        transcribed_text = ""
        confidence_score = 0.0
        word_count = 0
        error_message = ""
        is_filtered = False
        
        if response and response.status_code == 200:
            try:
                result = response.json()
                success = result.get('status') == 'success'
                transcribed_text = result.get('text', '')
                confidence_score = result.get('confidence', 0.0)
                word_count = result.get('word_count', 0)
                
                # Check if filtered
                if transcribed_text.startswith('[') and transcribed_text.endswith(']'):
                    is_filtered = True
                    
            except Exception as e:
                error_message = f"JSON parse error: {e}"
        elif response:
            error_message = f"HTTP {response.status_code}: {response.text[:200]}"
        else:
            error_message = "Request failed"
        
        # Create chunk metrics
        chunk_metrics = ChunkMetrics(
            chunk_id=chunk_id,
            session_id=session_id,
            timestamp=datetime.now(),
            audio_size_bytes=len(audio_data),
            processing_latency_ms=processing_latency,
            api_latency_ms=api_latency,
            total_latency_ms=total_latency,
            success=success,
            transcribed_text=transcribed_text,
            confidence_score=confidence_score,
            word_count=word_count,
            error_message=error_message,
            is_duplicate=is_duplicate,
            is_filtered=is_filtered
        )
        
        # Update session metrics
        self._update_session_metrics(session_id, chunk_metrics)
        
        # Store chunk
        self.chunk_history.append(chunk_metrics)
        self.latency_measurements.append(total_latency)
        
        # Track error patterns
        if error_message:
            self.error_patterns[error_message] += 1
        
        return chunk_metrics
    
    def _update_session_metrics(self, session_id: str, chunk_metrics: ChunkMetrics):
        """Update session-level metrics"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        session = self.sessions[session_id]
        session.total_chunks += 1
        
        if chunk_metrics.success:
            session.successful_chunks += 1
            session.total_words += chunk_metrics.word_count
            
            # Update cumulative text
            if chunk_metrics.transcribed_text and not chunk_metrics.is_filtered:
                if session.cumulative_text:
                    session.cumulative_text += " " + chunk_metrics.transcribed_text
                else:
                    session.cumulative_text = chunk_metrics.transcribed_text
        
        if chunk_metrics.is_duplicate:
            session.duplicate_chunks += 1
        
        if chunk_metrics.is_filtered:
            session.filtered_chunks += 1
        
        if not chunk_metrics.success:
            session.dropped_chunks += 1
        
        # Update latency metrics
        latency = chunk_metrics.total_latency_ms
        session.max_chunk_latency_ms = max(session.max_chunk_latency_ms, latency)
        session.min_chunk_latency_ms = min(session.min_chunk_latency_ms, latency)
        
        # Calculate rolling average
        session_chunks = [c for c in self.chunk_history if c.session_id == session_id and c.success]
        if session_chunks:
            latencies = [c.total_latency_ms for c in session_chunks]
            session.avg_chunk_latency_ms = statistics.mean(latencies)
            
            # Calculate P95
            sorted_latencies = sorted(latencies)
            if len(sorted_latencies) >= 20:  # Need reasonable sample size
                p95_index = int(len(sorted_latencies) * 0.95)
                session.p95_chunk_latency_ms = sorted_latencies[p95_index]
            
            # Calculate average confidence
            confidences = [c.confidence_score for c in session_chunks if c.confidence_score > 0]
            if confidences:
                session.avg_confidence = statistics.mean(confidences)
    
    def finalize_session(self, session_id: str, generate_final: bool = True) -> SessionMetrics:
        """Finalize a session and generate final transcript"""
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found")
            return None
        
        session = self.sessions[session_id]
        session.end_time = datetime.now()
        
        if generate_final and session.cumulative_text:
            # Request final transcript
            payload = {
                'session_id': session_id,
                'action': 'finalize',
                'text': session.cumulative_text,
                'is_final': True
            }
            
            try:
                response = requests.post(
                    self.transcription_url,
                    json=payload,
                    timeout=15,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    session.final_transcript = result.get('final_text', session.cumulative_text)
                else:
                    session.final_transcript = session.cumulative_text
                    
            except Exception as e:
                logger.error(f"Failed to generate final transcript: {e}")
                session.final_transcript = session.cumulative_text
        
        # Calculate quality metrics
        if session_id in self.reference_transcripts:
            session.word_error_rate = self._calculate_wer(
                self.reference_transcripts[session_id],
                session.final_transcript or session.cumulative_text
            )
        
        # Calculate text stability (how much the transcript changed)
        session.text_stability_score = self._calculate_text_stability(session_id)
        
        # Update system metrics
        session.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
        session.cpu_usage_percent = psutil.Process().cpu_percent()
        
        logger.info(f"✅ Finalized session {session_id}: {session.success_rate:.1f}% success, {session.total_words} words")
        
        return session
    
    def _calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate between reference and hypothesis"""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if not ref_words:
            return 100.0 if hyp_words else 0.0
        
        # Simple WER calculation (can be enhanced with dynamic programming)
        # For now, use a basic approach
        import difflib
        
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        matching_blocks = matcher.get_matching_blocks()
        matches = sum(block.size for block in matching_blocks)
        
        wer = ((len(ref_words) - matches) / len(ref_words)) * 100
        return min(100.0, max(0.0, wer))
    
    def _calculate_text_stability(self, session_id: str) -> float:
        """Calculate how stable the cumulative text was throughout the session"""
        session_chunks = [c for c in self.chunk_history 
                         if c.session_id == session_id and c.success and not c.is_filtered]
        
        if len(session_chunks) < 2:
            return 100.0
        
        # Build cumulative text at each step
        cumulative_texts = []
        current_text = ""
        
        for chunk in session_chunks:
            if chunk.transcribed_text:
                if current_text:
                    current_text += " " + chunk.transcribed_text
                else:
                    current_text = chunk.transcribed_text
                cumulative_texts.append(current_text)
        
        if len(cumulative_texts) < 2:
            return 100.0
        
        # Calculate how much text changed between steps
        stability_scores = []
        for i in range(1, len(cumulative_texts)):
            prev_text = cumulative_texts[i-1]
            curr_text = cumulative_texts[i]
            
            # Simple stability metric: ratio of preserved text
            if not prev_text:
                stability_scores.append(100.0)
                continue
            
            # Check how much of the previous text is preserved
            if curr_text.startswith(prev_text):
                stability = 100.0  # Perfect stability
            else:
                # Calculate similarity
                import difflib
                similarity = difflib.SequenceMatcher(None, prev_text, curr_text).ratio()
                stability = similarity * 100
            
            stability_scores.append(stability)
        
        return statistics.mean(stability_scores) if stability_scores else 100.0
    
    def run_comprehensive_test(self, test_scenarios: List[Dict]) -> Dict:
        """Run comprehensive pipeline test with multiple scenarios"""
        logger.info(f"🧪 Starting comprehensive test with {len(test_scenarios)} scenarios")
        
        results = {
            'test_summary': {
                'start_time': datetime.now().isoformat(),
                'scenarios_tested': len(test_scenarios),
                'total_sessions': 0,
                'total_chunks': 0,
                'overall_success_rate': 0.0
            },
            'scenario_results': [],
            'performance_analysis': {},
            'quality_analysis': {},
            'error_analysis': {},
            'recommendations': []
        }
        
        all_sessions = []
        
        for i, scenario in enumerate(test_scenarios):
            logger.info(f"📋 Running scenario {i+1}: {scenario.get('name', 'Unnamed')}")
            
            session_id = f"test_scenario_{i+1}_{int(time.time())}"
            expected_text = scenario.get('expected_text', '')
            
            # Create session
            session = self.create_session(session_id, expected_text)
            
            # Generate or load audio chunks
            audio_chunks = self._generate_scenario_audio(scenario)
            
            # Process chunks
            chunk_results = []
            for j, audio_data in enumerate(audio_chunks):
                chunk_metrics = self.process_chunk(session_id, audio_data, j+1, expected_text)
                chunk_results.append(asdict(chunk_metrics))
                
                # Add realistic delay between chunks
                time.sleep(scenario.get('chunk_interval', 1.5))
            
            # Finalize session
            final_session = self.finalize_session(session_id)
            all_sessions.append(final_session)
            
            # Store scenario results
            scenario_result = {
                'scenario': scenario,
                'session_metrics': asdict(final_session),
                'chunk_results': chunk_results
            }
            results['scenario_results'].append(scenario_result)
            
            logger.info(f"✅ Scenario {i+1} complete: {final_session.success_rate:.1f}% success")
        
        # Calculate aggregate metrics
        if all_sessions:
            results['test_summary']['total_sessions'] = len(all_sessions)
            results['test_summary']['total_chunks'] = sum(s.total_chunks for s in all_sessions)
            results['test_summary']['overall_success_rate'] = statistics.mean([s.success_rate for s in all_sessions])
            
            # Performance analysis
            results['performance_analysis'] = self._analyze_performance(all_sessions)
            
            # Quality analysis
            results['quality_analysis'] = self._analyze_quality(all_sessions)
            
            # Error analysis
            results['error_analysis'] = self._analyze_errors()
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(all_sessions)
        
        results['test_summary']['end_time'] = datetime.now().isoformat()
        
        # Save results
        with open('comprehensive_pipeline_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📊 Comprehensive test complete. Results saved to comprehensive_pipeline_test_results.json")
        
        return results
    
    def _generate_scenario_audio(self, scenario: Dict) -> List[bytes]:
        """Generate audio chunks based on scenario specification"""
        audio_type = scenario.get('audio_type', 'sine_wave')
        chunk_count = scenario.get('chunk_count', 5)
        
        chunks = []
        
        if audio_type == 'sine_wave':
            for i in range(chunk_count):
                frequency = 440 + (i * 50)  # Varying frequency
                duration = scenario.get('chunk_duration', 1.0)
                audio_data = AudioGenerator.generate_sine_wave_wav(frequency, duration)
                chunks.append(audio_data)
                
        elif audio_type == 'speech_pattern':
            words = scenario.get('words', ['hello', 'world', 'test', 'audio', 'transcription'])
            # Split words across chunks
            words_per_chunk = max(1, len(words) // chunk_count)
            
            for i in range(chunk_count):
                start_idx = i * words_per_chunk
                end_idx = min(start_idx + words_per_chunk, len(words))
                chunk_words = words[start_idx:end_idx]
                
                if chunk_words:
                    audio_data = AudioGenerator.generate_speech_pattern_wav(chunk_words)
                    chunks.append(audio_data)
        
        elif audio_type == 'silence':
            # Generate silent audio
            for i in range(chunk_count):
                duration = scenario.get('chunk_duration', 1.0)
                sample_rate = 16000
                samples_count = int(sample_rate * duration)
                
                # Create silent WAV
                wav_data = b'RIFF'
                wav_data += struct.pack('<I', 36 + samples_count * 2)
                wav_data += b'WAVE'
                wav_data += b'fmt '
                wav_data += struct.pack('<I', 16)
                wav_data += struct.pack('<H', 1)   # PCM
                wav_data += struct.pack('<H', 1)   # Mono
                wav_data += struct.pack('<I', sample_rate)
                wav_data += struct.pack('<I', sample_rate * 2)
                wav_data += struct.pack('<H', 2)
                wav_data += struct.pack('<H', 16)
                wav_data += b'data'
                wav_data += struct.pack('<I', samples_count * 2)
                
                # Add silent samples
                for _ in range(samples_count):
                    wav_data += struct.pack('<h', 0)
                
                chunks.append(wav_data)
        
        return chunks
    
    def _analyze_performance(self, sessions: List[SessionMetrics]) -> Dict:
        """Analyze performance metrics across sessions"""
        if not sessions:
            return {}
        
        latencies = []
        success_rates = []
        
        for session in sessions:
            if session.avg_chunk_latency_ms > 0:
                latencies.append(session.avg_chunk_latency_ms)
            success_rates.append(session.success_rate)
        
        analysis = {
            'latency_metrics': {
                'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
                'median_latency_ms': statistics.median(latencies) if latencies else 0,
                'p95_latency_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0),
                'max_latency_ms': max(latencies) if latencies else 0,
                'min_latency_ms': min(latencies) if latencies else 0
            },
            'throughput_metrics': {
                'avg_success_rate': statistics.mean(success_rates),
                'min_success_rate': min(success_rates),
                'sessions_above_95_percent': len([s for s in success_rates if s >= 95.0]),
                'total_words_processed': sum(s.total_words for s in sessions),
                'avg_words_per_session': statistics.mean([s.total_words for s in sessions])
            },
            'efficiency_metrics': {
                'avg_chunks_per_session': statistics.mean([s.total_chunks for s in sessions]),
                'avg_duplicate_rate': statistics.mean([(s.duplicate_chunks / s.total_chunks * 100) if s.total_chunks > 0 else 0 for s in sessions]),
                'avg_filter_rate': statistics.mean([(s.filtered_chunks / s.total_chunks * 100) if s.total_chunks > 0 else 0 for s in sessions])
            }
        }
        
        return analysis
    
    def _analyze_quality(self, sessions: List[SessionMetrics]) -> Dict:
        """Analyze transcription quality metrics"""
        analysis = {
            'accuracy_metrics': {
                'sessions_with_reference': len([s for s in sessions if s.word_error_rate > 0]),
                'avg_word_error_rate': statistics.mean([s.word_error_rate for s in sessions if s.word_error_rate > 0]) if any(s.word_error_rate > 0 for s in sessions) else 0,
                'avg_confidence_score': statistics.mean([s.avg_confidence for s in sessions if s.avg_confidence > 0]) if any(s.avg_confidence > 0 for s in sessions) else 0,
                'avg_text_stability': statistics.mean([s.text_stability_score for s in sessions if s.text_stability_score > 0]) if any(s.text_stability_score > 0 for s in sessions) else 0
            },
            'content_metrics': {
                'sessions_with_output': len([s for s in sessions if s.total_words > 0]),
                'avg_words_per_minute': statistics.mean([s.words_per_minute for s in sessions if s.words_per_minute > 0]) if any(s.words_per_minute > 0 for s in sessions) else 0,
                'longest_transcript': max([len(s.final_transcript or s.cumulative_text) for s in sessions]) if sessions else 0,
                'empty_transcripts': len([s for s in sessions if not (s.final_transcript or s.cumulative_text)])
            }
        }
        
        return analysis
    
    def _analyze_errors(self) -> Dict:
        """Analyze error patterns and frequencies"""
        total_errors = sum(self.error_patterns.values())
        
        analysis = {
            'error_frequency': {
                'total_errors': total_errors,
                'unique_error_types': len(self.error_patterns),
                'top_errors': dict(sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:10])
            },
            'error_categories': {
                'network_errors': sum(count for error, count in self.error_patterns.items() if 'network' in error.lower() or 'timeout' in error.lower()),
                'format_errors': sum(count for error, count in self.error_patterns.items() if 'format' in error.lower() or 'invalid' in error.lower()),
                'api_errors': sum(count for error, count in self.error_patterns.items() if 'HTTP' in error),
                'processing_errors': sum(count for error, count in self.error_patterns.items() if 'processing' in error.lower())
            }
        }
        
        return analysis
    
    def _generate_recommendations(self, sessions: List[SessionMetrics]) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        if not sessions:
            return ["No session data available for analysis"]
        
        # Performance recommendations
        avg_success_rate = statistics.mean([s.success_rate for s in sessions])
        if avg_success_rate < 90:
            recommendations.append(f"CRITICAL: Low success rate ({avg_success_rate:.1f}%). Investigate error patterns and improve reliability.")
        
        latencies = [s.avg_chunk_latency_ms for s in sessions if s.avg_chunk_latency_ms > 0]
        if latencies:
            avg_latency = statistics.mean(latencies)
            if avg_latency > 2000:
                recommendations.append(f"HIGH: Average latency ({avg_latency:.0f}ms) exceeds target. Optimize audio processing pipeline.")
        
        # Quality recommendations
        empty_sessions = len([s for s in sessions if s.total_words == 0])
        if empty_sessions > 0:
            recommendations.append(f"CRITICAL: {empty_sessions} sessions produced no transcription output. Verify audio processing pipeline.")
        
        # Error pattern recommendations
        format_errors = sum(count for error, count in self.error_patterns.items() if 'format' in error.lower())
        if format_errors > 0:
            recommendations.append(f"HIGH: {format_errors} audio format errors detected. Improve format validation and conversion.")
        
        # Efficiency recommendations
        avg_duplicate_rate = statistics.mean([(s.duplicate_chunks / s.total_chunks * 100) if s.total_chunks > 0 else 0 for s in sessions])
        if avg_duplicate_rate > 5:
            recommendations.append(f"MEDIUM: High duplicate rate ({avg_duplicate_rate:.1f}%). Implement better deduplication.")
        
        # Positive feedback
        if avg_success_rate >= 95 and (not latencies or statistics.mean(latencies) <= 2000):
            recommendations.append("EXCELLENT: System meets performance targets. Consider additional load testing.")
        
        return recommendations

def main():
    """Run comprehensive pipeline profiling"""
    print("🚀 COMPREHENSIVE PIPELINE PROFILER")
    print("=" * 50)
    
    profiler = PipelineProfiler()
    
    # Define test scenarios
    test_scenarios = [
        {
            'name': 'Basic Audio Processing',
            'audio_type': 'sine_wave',
            'chunk_count': 5,
            'chunk_duration': 1.0,
            'chunk_interval': 1.5,
            'expected_text': 'test audio'
        },
        {
            'name': 'Speech Pattern Simulation',
            'audio_type': 'speech_pattern',
            'words': ['hello', 'world', 'this', 'is', 'a', 'test'],
            'chunk_count': 3,
            'chunk_interval': 2.0,
            'expected_text': 'hello world this is a test'
        },
        {
            'name': 'Silent Audio Handling',
            'audio_type': 'silence',
            'chunk_count': 3,
            'chunk_duration': 1.0,
            'chunk_interval': 1.0,
            'expected_text': ''
        },
        {
            'name': 'High Frequency Test',
            'audio_type': 'sine_wave',
            'chunk_count': 10,
            'chunk_duration': 0.5,
            'chunk_interval': 0.8,
            'expected_text': 'rapid audio chunks'
        }
    ]
    
    # Run comprehensive test
    results = profiler.run_comprehensive_test(test_scenarios)
    
    # Print summary
    print("\n" + "=" * 50)
    print("COMPREHENSIVE PIPELINE ANALYSIS RESULTS")
    print("=" * 50)
    
    summary = results['test_summary']
    performance = results['performance_analysis']
    quality = results['quality_analysis']
    
    print(f"Test Duration: {summary.get('start_time', 'N/A')} - {summary.get('end_time', 'N/A')}")
    print(f"Scenarios Tested: {summary['scenarios_tested']}")
    print(f"Total Sessions: {summary['total_sessions']}")
    print(f"Total Chunks: {summary['total_chunks']}")
    print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
    
    if performance:
        print(f"\n📊 Performance Metrics:")
        latency = performance.get('latency_metrics', {})
        print(f"  Average Latency: {latency.get('avg_latency_ms', 0):.1f}ms")
        print(f"  P95 Latency: {latency.get('p95_latency_ms', 0):.1f}ms")
        
        throughput = performance.get('throughput_metrics', {})
        print(f"  Words Processed: {throughput.get('total_words_processed', 0)}")
        print(f"  Sessions ≥95% Success: {throughput.get('sessions_above_95_percent', 0)}")
    
    if quality:
        print(f"\n🎯 Quality Metrics:")
        accuracy = quality.get('accuracy_metrics', {})
        print(f"  Average WER: {accuracy.get('avg_word_error_rate', 0):.1f}%")
        print(f"  Average Confidence: {accuracy.get('avg_confidence_score', 0):.2f}")
        print(f"  Text Stability: {accuracy.get('avg_text_stability', 0):.1f}%")
        
        content = quality.get('content_metrics', {})
        print(f"  Sessions with Output: {content.get('sessions_with_output', 0)}")
        print(f"  Empty Transcripts: {content.get('empty_transcripts', 0)}")
    
    print(f"\n📝 Recommendations:")
    for rec in results['recommendations']:
        print(f"  • {rec}")
    
    print(f"\n📄 Full results saved to: comprehensive_pipeline_test_results.json")
    
    return results

if __name__ == "__main__":
    main()