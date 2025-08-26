#!/usr/bin/env python3
"""
Headless WebSocket Streamer for End-to-End Transcription Validation
Loads podcast MP3, resamples to mono 16kHz, and streams like live mic input
"""

import asyncio
import socketio
import subprocess
import base64
import time
import logging
import numpy as np
import json
import wave
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PodcastWebSocketStreamer:
    """Streams podcast audio via WebSocket to simulate live microphone input"""
    
    def __init__(self, audio_file_path: str, server_url: str = "http://localhost:5000"):
        self.audio_file_path = audio_file_path
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self.session_id = None
        
        # Streaming configuration
        self.chunk_duration = 1.2  # 1.0-1.5s chunks as specified
        self.sample_rate = 16000
        self.channels = 1
        
        # Metrics tracking
        self.metrics = {
            'chunks_sent': 0,
            'acks_received': 0,
            'interim_received': 0,
            'final_received': 0,
            'start_time': None,
            'first_interim_latency': None,
            'interim_intervals': [],
            'errors': []
        }
        
        # Event handlers
        self._setup_socket_handlers()
    
    def _setup_socket_handlers(self):
        """Setup WebSocket event handlers for validation"""
        
        @self.sio.on('connect')
        async def on_connect():
            logger.info("🔗 WebSocket connected to server")
        
        @self.sio.on('disconnect')
        async def on_disconnect():
            logger.info("🔌 WebSocket disconnected")
        
        @self.sio.on('joined_session')
        async def on_joined_session(data):
            logger.info(f"✅ Joined session: {data}")
            self.session_id = data.get('session_id')
        
        @self.sio.on('ack')
        async def on_ack(data):
            self.metrics['acks_received'] += 1
            logger.debug(f"📩 ACK received: {data}")
        
        @self.sio.on('interim_transcript')
        async def on_interim_transcript(data):
            self.metrics['interim_received'] += 1
            current_time = time.time()
            
            # Track first interim latency
            if self.metrics['first_interim_latency'] is None and self.metrics['start_time']:
                self.metrics['first_interim_latency'] = current_time - self.metrics['start_time']
                logger.info(f"🚀 First interim received in {self.metrics['first_interim_latency']:.2f}s")
            
            # Track interim intervals
            if len(self.metrics['interim_intervals']) > 0:
                last_interim = self.metrics['interim_intervals'][-1]
                interval = current_time - last_interim
                self.metrics['interim_intervals'].append(current_time)
            else:
                self.metrics['interim_intervals'].append(current_time)
            
            logger.info(f"📝 Interim #{self.metrics['interim_received']}: '{data.get('text', '')[:50]}...'")
        
        @self.sio.on('final_transcript')
        async def on_final_transcript(data):
            self.metrics['final_received'] += 1
            logger.info(f"✅ Final #{self.metrics['final_received']}: '{data.get('text', '')[:50]}...'")
        
        @self.sio.on('error')
        async def on_error(data):
            error_msg = f"❌ Server error: {data}"
            logger.error(error_msg)
            self.metrics['errors'].append(error_msg)
    
    def load_and_process_audio(self) -> List[bytes]:
        """Load MP3 and convert to mono 16kHz WAV chunks"""
        logger.info(f"🎵 Loading audio file: {self.audio_file_path}")
        
        try:
            # Convert MP3 to mono 16kHz WAV using ffmpeg
            cmd = [
                'ffmpeg', '-i', self.audio_file_path,
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', str(self.sample_rate),  # 16kHz
                '-ac', str(self.channels),     # Mono
                '-f', 'wav',                   # WAV format
                '-'                            # Output to stdout
            ]
            
            result = subprocess.run(cmd, capture_output=True, check=True)
            audio_data = result.stdout
            
            logger.info(f"✅ Converted audio: {len(audio_data)} bytes")
            
            # Parse WAV data and extract audio samples
            wav_io = BytesIO(audio_data)
            with wave.open(wav_io, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                
            # Convert to numpy array for chunking
            audio_samples = np.frombuffer(frames, dtype=np.int16)
            logger.info(f"📊 Audio samples: {len(audio_samples)} ({len(audio_samples)/self.sample_rate:.2f}s)")
            
            # Create chunks with specified duration
            samples_per_chunk = int(self.chunk_duration * self.sample_rate)
            chunks = []
            
            for i in range(0, len(audio_samples), samples_per_chunk):
                chunk_samples = audio_samples[i:i + samples_per_chunk]
                
                # Create WAV chunk
                chunk_wav = BytesIO()
                with wave.open(chunk_wav, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(chunk_samples.tobytes())
                
                chunk_wav.seek(0)
                chunks.append(chunk_wav.getvalue())
            
            logger.info(f"🔪 Created {len(chunks)} audio chunks ({self.chunk_duration}s each)")
            return chunks
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            logger.error(f"stderr: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"❌ Audio processing error: {e}")
            raise
    
    def calculate_rms(self, audio_chunk: bytes) -> float:
        """Calculate RMS value for audio chunk"""
        try:
            # Skip WAV header (44 bytes) and get PCM data
            pcm_data = audio_chunk[44:]
            samples = np.frombuffer(pcm_data, dtype=np.int16)
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            return float(rms / 32768.0)  # Normalize to 0-1
        except Exception as e:
            logger.warning(f"⚠️ RMS calculation failed: {e}")
            return 0.5  # Default value
    
    async def stream_podcast(self) -> Dict[str, Any]:
        """Main streaming function - simulates live microphone input"""
        logger.info("🎙️ Starting podcast WebSocket streaming simulation")
        
        try:
            # Connect to server
            await self.sio.connect(self.server_url)
            await asyncio.sleep(1)  # Allow connection to stabilize
            
            # Join session
            logger.info("🏠 Creating and joining session...")
            await self.sio.emit('join_session', {'session_id': f'e2e_test_{int(time.time())}'})
            await asyncio.sleep(2)  # Wait for session creation
            
            if not self.session_id:
                raise Exception("Failed to join session")
            
            # Load and process audio
            audio_chunks = self.load_and_process_audio()
            
            # Start streaming
            self.metrics['start_time'] = time.time()
            logger.info(f"🚀 Starting real-time streaming of {len(audio_chunks)} chunks...")
            
            for i, chunk in enumerate(audio_chunks):
                # Calculate RMS for this chunk
                rms = self.calculate_rms(chunk)
                
                # Prepare payload (same as real mic path)
                payload = {
                    'session_id': self.session_id,
                    'audio_data_b64': base64.b64encode(chunk).decode('utf-8'),
                    'mime_type': 'audio/wav',
                    'rms': rms,
                    'ts_client': int(time.time() * 1000),
                    'is_final_chunk': False
                }
                
                # Send chunk
                await self.sio.emit('audio_chunk', payload)
                self.metrics['chunks_sent'] += 1
                
                # Log progress
                if (i + 1) % 5 == 0:
                    logger.info(f"📦 Sent {i + 1}/{len(audio_chunks)} chunks, "
                              f"Interims: {self.metrics['interim_received']}, "
                              f"Finals: {self.metrics['final_received']}")
                
                # Real-time pacing (sleep = chunk_duration)
                await asyncio.sleep(self.chunk_duration)
            
            # Send final chunk signal
            final_payload = {
                'session_id': self.session_id,
                'audio_data_b64': '',
                'mime_type': 'audio/wav',
                'rms': 0.0,
                'ts_client': int(time.time() * 1000),
                'is_final_chunk': True
            }
            await self.sio.emit('audio_chunk', final_payload)
            logger.info("🏁 Sent final chunk signal")
            
            # Wait for final processing
            await asyncio.sleep(5)
            
            # Send end_of_stream
            await self.sio.emit('end_of_stream', {'session_id': self.session_id})
            logger.info("🔚 Sent end_of_stream signal")
            
            # Wait for final results
            await asyncio.sleep(3)
            
            # Calculate metrics
            total_time = time.time() - self.metrics['start_time']
            if len(self.metrics['interim_intervals']) > 1:
                avg_interim_interval = np.mean(np.diff(self.metrics['interim_intervals']))
            else:
                avg_interim_interval = 0
            
            # Compile results
            results = {
                'session_id': self.session_id,
                'total_duration_seconds': total_time,
                'chunks_sent': self.metrics['chunks_sent'],
                'acks_received': self.metrics['acks_received'],
                'interim_received': self.metrics['interim_received'],
                'final_received': self.metrics['final_received'],
                'first_interim_latency_ms': (self.metrics['first_interim_latency'] * 1000) if self.metrics['first_interim_latency'] else None,
                'avg_interim_interval_ms': avg_interim_interval * 1000 if avg_interim_interval else 0,
                'errors': self.metrics['errors'],
                'success': len(self.metrics['errors']) == 0 and self.metrics['interim_received'] > 0
            }
            
            logger.info("📊 STREAMING RESULTS:")
            logger.info(f"   Session: {results['session_id']}")
            logger.info(f"   Duration: {results['total_duration_seconds']:.1f}s")
            logger.info(f"   Chunks sent: {results['chunks_sent']}")
            logger.info(f"   ACKs received: {results['acks_received']}")
            logger.info(f"   Interims received: {results['interim_received']}")
            logger.info(f"   Finals received: {results['final_received']}")
            logger.info(f"   First interim latency: {results['first_interim_latency_ms']:.1f}ms")
            logger.info(f"   Avg interim interval: {results['avg_interim_interval_ms']:.1f}ms")
            logger.info(f"   Success: {results['success']}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Streaming failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': self.session_id,
                'metrics': self.metrics
            }
        finally:
            await self.sio.disconnect()

# CLI interface for direct testing
if __name__ == "__main__":
    import sys
    
    # Use the latest podcast file
    podcast_file = "attached_assets/ytmp3free.cc_boosie-goes-off-on-irv-gotti-dying-he-got-hated-on-while-he-was-alive-now-they-show-love-part-5-youtubemp3free.org_1756227635769.mp3"
    
    if len(sys.argv) > 1:
        podcast_file = sys.argv[1]
    
    if not Path(podcast_file).exists():
        logger.error(f"❌ Audio file not found: {podcast_file}")
        sys.exit(1)
    
    async def main():
        streamer = PodcastWebSocketStreamer(podcast_file)
        results = await streamer.stream_podcast()
        
        print("\n" + "="*60)
        print("🎯 E2E VALIDATION RESULTS")
        print("="*60)
        print(json.dumps(results, indent=2))
    
    asyncio.run(main())