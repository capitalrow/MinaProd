#!/usr/bin/env python3
"""
WebSocket MP3 Streamer for End-to-End Testing
Streams MP3 audio as live-paced WAV chunks over WebSocket
"""

import os
import sys
import time
import wave
import base64
import asyncio
import socketio
import tempfile
from pathlib import Path
from pydub import AudioSegment
import argparse
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MP3WebSocketStreamer:
    def __init__(self, mp3_path, server_url="http://localhost:5000", chunk_duration_ms=600):
        self.mp3_path = Path(mp3_path)
        self.server_url = server_url
        self.chunk_duration_ms = chunk_duration_ms
        self.sio = socketio.AsyncClient()
        self.session_id = None
        self.chunks_sent = 0
        self.start_time = None
        self.metrics = {
            "chunks_sent": 0,
            "bytes_sent": 0,
            "duration_ms": 0,
            "audio_duration_ms": 0,
            "responses_received": 0,
            "transcription_results": [],
            "errors": []
        }
        
        # Setup event handlers
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.sio.event
        async def connect():
            logger.info(f"🔌 Connected to {self.server_url}")
            
        @self.sio.event
        async def disconnect():
            logger.info("🔌 Disconnected from server")
            
        @self.sio.event
        async def transcription_result(data):
            """Handle transcription results from server"""
            self.metrics["responses_received"] += 1
            self.metrics["transcription_results"].append({
                "timestamp": time.time(),
                "data": data
            })
            
            text = data.get("text", "")
            is_final = data.get("is_final", False)
            confidence = data.get("confidence", 0)
            
            status = "FINAL" if is_final else "INTERIM"
            logger.info(f"📝 {status}: '{text}' (confidence: {confidence:.0%})")
            
        @self.sio.event
        async def transcription_error(data):
            """Handle transcription errors"""
            error_msg = data.get("error", "Unknown error")
            self.metrics["errors"].append({
                "timestamp": time.time(),
                "error": error_msg
            })
            logger.error(f"❌ Transcription error: {error_msg}")
            
        @self.sio.event
        async def session_started(data):
            """Handle session start confirmation"""
            self.session_id = data.get("session_id")
            logger.info(f"🎯 Session started: {self.session_id}")
    
    def load_and_prepare_audio(self):
        """Load MP3 and convert to appropriate format"""
        logger.info(f"🎵 Loading audio: {self.mp3_path}")
        
        if not self.mp3_path.exists():
            raise FileNotFoundError(f"MP3 file not found: {self.mp3_path}")
        
        # Load MP3 and convert to mono 16kHz WAV format
        audio = AudioSegment.from_mp3(str(self.mp3_path))
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(16000)  # 16kHz sample rate
        audio = audio.set_sample_width(2)  # 16-bit
        
        logger.info(f"📊 Audio prepared: {len(audio)}ms duration, {audio.frame_rate}Hz, {audio.channels}ch")
        self.metrics["audio_duration_ms"] = len(audio)
        
        return audio
    
    def create_audio_chunks(self, audio):
        """Split audio into chunks"""
        chunks = []
        total_duration = len(audio)
        
        for start_ms in range(0, total_duration, self.chunk_duration_ms):
            end_ms = min(start_ms + self.chunk_duration_ms, total_duration)
            chunk = audio[start_ms:end_ms]
            
            # Convert chunk to WAV bytes
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                chunk.export(temp_wav.name, format="wav")
                temp_wav.seek(0)
                
                with open(temp_wav.name, 'rb') as wav_file:
                    wav_bytes = wav_file.read()
                
                os.unlink(temp_wav.name)  # Clean up temp file
            
            chunks.append({
                "data": wav_bytes,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": end_ms - start_ms
            })
        
        logger.info(f"🔧 Created {len(chunks)} chunks ({self.chunk_duration_ms}ms each)")
        return chunks
    
    async def connect_to_server(self):
        """Connect to the WebSocket server"""
        logger.info(f"🔌 Connecting to {self.server_url}")
        await self.sio.connect(self.server_url, socketio_path='/socket.io/')
        
        # Wait a moment for connection to stabilize
        await asyncio.sleep(0.5)
        
        # Start session
        await self.sio.emit('start_session', {})
        await asyncio.sleep(0.5)  # Wait for session confirmation
    
    async def stream_chunks(self, chunks):
        """Stream audio chunks with real-time pacing"""
        logger.info(f"🚀 Starting to stream {len(chunks)} chunks")
        self.start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            chunk_start_time = time.time()
            
            # Encode chunk as base64
            audio_data = base64.b64encode(chunk["data"]).decode('utf-8')
            
            # Create chunk payload
            payload = {
                "audio_data": audio_data,
                "chunk_id": i,
                "timestamp": chunk_start_time,
                "duration_ms": chunk["duration_ms"],
                "is_final_chunk": (i == len(chunks) - 1)
            }
            
            # Send chunk
            await self.sio.emit('audio_chunk', payload)
            
            self.chunks_sent += 1
            self.metrics["chunks_sent"] = self.chunks_sent
            self.metrics["bytes_sent"] += len(chunk["data"])
            
            logger.info(f"📤 Sent chunk {i+1}/{len(chunks)} ({len(chunk['data'])} bytes)")
            
            # Real-time pacing: wait for chunk duration before sending next chunk
            if i < len(chunks) - 1:  # Don't wait after the last chunk
                chunk_duration_seconds = chunk["duration_ms"] / 1000.0
                elapsed = time.time() - chunk_start_time
                sleep_time = max(0, chunk_duration_seconds - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
        
        # Send end of stream signal
        await self.sio.emit('end_of_stream', {
            "session_id": self.session_id,
            "total_chunks": len(chunks),
            "total_duration_ms": sum(c["duration_ms"] for c in chunks)
        })
        
        logger.info("🏁 Stream complete, sent end_of_stream signal")
    
    async def wait_for_final_results(self, timeout_seconds=30):
        """Wait for final transcription results"""
        logger.info(f"⏳ Waiting up to {timeout_seconds}s for final results...")
        
        start_wait = time.time()
        while time.time() - start_wait < timeout_seconds:
            await asyncio.sleep(1)
            
            # Check if we have received recent results
            if self.metrics["responses_received"] > 0:
                last_response_time = max(
                    result["timestamp"] for result in self.metrics["transcription_results"]
                )
                
                # If no new results for 5 seconds, assume we're done
                if time.time() - last_response_time > 5:
                    break
        
        logger.info(f"✅ Received {self.metrics['responses_received']} transcription responses")
    
    async def disconnect(self):
        """Disconnect from server"""
        await self.sio.disconnect()
        
        # Calculate final metrics
        if self.start_time:
            self.metrics["duration_ms"] = int((time.time() - self.start_time) * 1000)
    
    def get_metrics(self):
        """Get streaming metrics"""
        # Count words and final segments
        total_words = 0
        final_segments = 0
        
        for result in self.metrics["transcription_results"]:
            data = result["data"]
            text = data.get("text", "")
            is_final = data.get("is_final", False)
            
            if text.strip():
                words = len(text.strip().split())
                total_words += words
                
                if is_final:
                    final_segments += 1
        
        self.metrics.update({
            "words_total": total_words,
            "final_segments": final_segments,
            "session_id": self.session_id
        })
        
        return self.metrics
    
    async def run_stream(self):
        """Main streaming function"""
        try:
            # Load and prepare audio
            audio = self.load_and_prepare_audio()
            chunks = self.create_audio_chunks(audio)
            
            # Connect to server
            await self.connect_to_server()
            
            # Stream chunks
            await self.stream_chunks(chunks)
            
            # Wait for final results
            await self.wait_for_final_results()
            
        except Exception as e:
            logger.error(f"❌ Streaming failed: {e}")
            self.metrics["errors"].append({
                "timestamp": time.time(),
                "error": str(e)
            })
            raise
        finally:
            await self.disconnect()

async def main():
    parser = argparse.ArgumentParser(description='Stream MP3 audio over WebSocket for testing')
    parser.add_argument('mp3_path', help='Path to MP3 file to stream')
    parser.add_argument('--server', default='http://localhost:5000', help='Server URL')
    parser.add_argument('--chunk-ms', type=int, default=600, help='Chunk duration in milliseconds')
    parser.add_argument('--output-metrics', help='JSON file to save metrics')
    
    args = parser.parse_args()
    
    # Create streamer
    streamer = MP3WebSocketStreamer(
        mp3_path=args.mp3_path,
        server_url=args.server,
        chunk_duration_ms=args.chunk_ms
    )
    
    # Run streaming
    await streamer.run_stream()
    
    # Get and display metrics
    metrics = streamer.get_metrics()
    
    logger.info("📊 Final Metrics:")
    logger.info(f"   Chunks sent: {metrics['chunks_sent']}")
    logger.info(f"   Bytes sent: {metrics['bytes_sent']:,}")
    logger.info(f"   Audio duration: {metrics['audio_duration_ms']:,}ms")
    logger.info(f"   Stream duration: {metrics['duration_ms']:,}ms")
    logger.info(f"   Responses received: {metrics['responses_received']}")
    logger.info(f"   Total words: {metrics['words_total']}")
    logger.info(f"   Final segments: {metrics['final_segments']}")
    logger.info(f"   Errors: {len(metrics['errors'])}")
    
    # Save metrics if requested
    if args.output_metrics:
        with open(args.output_metrics, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        logger.info(f"💾 Metrics saved to {args.output_metrics}")
    
    # Return metrics for programmatic use
    return metrics

if __name__ == "__main__":
    asyncio.run(main())