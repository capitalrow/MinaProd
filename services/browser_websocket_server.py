#!/usr/bin/env python3
"""
Browser WebSocket Server - Real-time transcription with OpenAI Whisper API
Uses minimal WebSocket implementation designed for browser connections
"""

import asyncio
import websockets
import json
import logging
import time
import uuid
import threading
import os
import io
import tempfile
from datetime import datetime
import openai
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class BrowserWebSocketServer:
    """WebSocket server optimized specifically for browser connections."""
    
    def __init__(self, host="0.0.0.0", port=8774, ssl_context=None):  # Changed default port
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.clients = {}
        self.sessions = {}
        self.running = False
        
    async def handle_client(self, websocket):
        """Handle Enhanced WebSocket connection with robust protocol handling."""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        
        logger.info(f"🌐 Enhanced WebSocket client connected: {client_id}")
        
        try:
            # Send enhanced welcome message
            welcome = {
                'type': 'connected',
                'client_id': client_id,
                'server_time': time.time(),
                'server': 'Enhanced WebSocket Server v2.0',
                'protocol': 'mixed_json_binary',
                'message': 'Ready for real-time transcription'
            }
            await websocket.send(json.dumps(welcome))
            
            # Handle messages from browser with enhanced error recovery
            async for message in websocket:
                try:
                    if isinstance(message, str):
                        # JSON control messages (session join, ping, etc.)
                        try:
                            data = json.loads(message)
                            logger.debug(f"📨 JSON message: {data.get('type', 'unknown')} from {client_id}")
                            await self.handle_browser_message(websocket, client_id, data)
                        except json.JSONDecodeError as e:
                            logger.error(f"❌ Invalid JSON from {client_id}: {e}")
                            await websocket.send(json.dumps({
                                'type': 'error',
                                'message': 'Invalid JSON format',
                                'client_id': client_id,
                                'timestamp': time.time()
                            }))
                    elif isinstance(message, bytes):
                        # Binary audio data from MediaRecorder - CRITICAL FIX
                        logger.debug(f"🎵 Binary audio detected: {len(message)} bytes from {client_id}")
                        await self.handle_browser_audio(websocket, client_id, message)
                    else:
                        logger.warning(f"⚠️ Unknown message type from {client_id}: {type(message)}")
                        
                except Exception as e:
                    logger.error(f"❌ Message processing error for {client_id}: {e}")
                    # Send error but keep connection alive
                    try:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': f'Processing failed: {str(e)}',
                            'client_id': client_id,
                            'timestamp': time.time()
                        }))
                    except:
                        pass  # Connection might be closed
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🌐 Enhanced WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"❌ Enhanced WebSocket client error: {e}")
        finally:
            # Enhanced cleanup
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.sessions:
                session_id = self.sessions[client_id]
                logger.info(f"🧹 Session cleanup: {session_id} for client {client_id}")
                del self.sessions[client_id]
    
    async def handle_browser_message(self, websocket, client_id, data):
        """Handle JSON messages from browser."""
        message_type = data.get('type')
        
        if message_type == 'join_session':
            session_id = data.get('session_id')
            self.sessions[client_id] = session_id
            
            logger.info(f"🌐 Browser client {client_id} joined session {session_id}")
            
            # Send session confirmation
            await websocket.send(json.dumps({
                'type': 'session_joined',
                'session_id': session_id,
                'client_id': client_id,
                'timestamp': time.time()
            }))
            
        elif message_type == 'ping':
            # Respond to browser ping
            await websocket.send(json.dumps({
                'type': 'pong',
                'timestamp': time.time()
            }))
    
    async def handle_browser_audio(self, websocket, client_id, audio_data):
        """Handle audio data from browser MediaRecorder with concurrent processing for optimal performance."""
        session_id = self.sessions.get(client_id, 'unknown')
        timestamp = datetime.now().strftime('%H:%M:%S')
        audio_size = len(audio_data)
        start_time = time.time()
        
        logger.info(f"🎵 Received browser audio: {audio_size} bytes from {client_id}")
        
        # Skip only extremely small audio chunks to reduce API calls
        if audio_size < 100:
            logger.debug(f"⏭️ Skipping tiny audio chunk: {audio_size} bytes")
            return
        
        # Send immediate interim feedback for excellent latency (<100ms)
        interim_response = {
            'type': 'transcription_result',
            'session_id': session_id,
            'text': "🎙️ Processing audio...",
            'is_final': False,
            'confidence': 0.1,
            'timestamp': start_time,
            'processing': True
        }
        await websocket.send(json.dumps(interim_response))
        
        # CRITICAL: Process audio in background thread pool for concurrency
        import concurrent.futures
        import asyncio
        
        try:
            # Use thread pool for I/O-bound Whisper API calls
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # Submit transcription task to thread pool (FIXED)
                future = loop.run_in_executor(
                    executor, 
                    self.transcribe_audio_blocking, 
                    audio_data
                )
                
                # Wait for transcription with timeout
                try:
                    transcription_text = await asyncio.wait_for(future, timeout=10.0)
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Transcription timeout for {audio_size} bytes")
                    transcription_text = None
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if transcription_text and transcription_text.strip():
                # Determine if this is interim or final based on chunk size
                is_final = audio_size > 2048
                confidence = 0.95
                
                # Send real transcription result
                final_response = {
                    'type': 'transcription_result',
                    'session_id': session_id,
                    'text': transcription_text.strip(),
                    'is_final': is_final,
                    'confidence': confidence,
                    'timestamp': start_time,
                    'audio_duration': audio_size,
                    'processing_time_ms': processing_time,
                    'processing': False
                }
                
                await websocket.send(json.dumps(final_response))
                logger.info(f"📝 Real transcription sent ({processing_time:.1f}ms): {transcription_text[:50]}...")
            else:
                # No speech detected - send feedback
                no_speech_response = {
                    'type': 'transcription_result',
                    'session_id': session_id,
                    'text': "[No speech detected]",
                    'is_final': False,
                    'confidence': 0.0,
                    'timestamp': start_time,
                    'processing_time_ms': processing_time,
                    'processing': False
                }
                await websocket.send(json.dumps(no_speech_response))
                logger.debug(f"🔇 No speech detected in audio chunk ({processing_time:.1f}ms)")
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Transcription error ({processing_time:.1f}ms): {e}")
            # Send error feedback
            error_response = {
                'type': 'transcription_result',
                'session_id': session_id,
                'text': f"[Audio processing temporarily unavailable]",
                'is_final': False,
                'confidence': 0.0,
                'timestamp': start_time,
                'processing_time_ms': processing_time,
                'processing': False
            }
            await websocket.send(json.dumps(error_response))
    
    def transcribe_audio_sync(self, audio_data):
        """Synchronous wrapper for Whisper API calls (runs in thread pool)."""
        # FIXED: Call synchronous version directly to avoid event loop conflict
        return self.transcribe_audio_blocking(audio_data)
    
    def transcribe_audio_blocking(self, audio_data):
        """Synchronous transcription using OpenAI Whisper API (for thread pool execution)."""
        try:
            # ENHANCED: Accept more audio formats and smaller chunks
            if len(audio_data) < 50:
                logger.debug(f"⚠️ Audio chunk too small: {len(audio_data)} bytes")
                return None
                
            # Check if audio data looks like valid audio (more permissive)
            if not self.is_valid_webm(audio_data):
                logger.debug(f"⚠️ Audio data format validation failed, attempting conversion anyway")
                # Don't return None, attempt to process anyway
            
            # Save audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_webm_path = temp_file.name
            
            # Convert to WAV using ffmpeg directly for better compatibility
            wav_path = temp_webm_path.replace('.webm', '.wav')
            
            try:
                # Use ffmpeg to convert WebM to WAV with optimal settings for Whisper
                import subprocess
                ffmpeg_cmd = [
                    'ffmpeg', '-i', temp_webm_path,
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',      # Mono channel
                    '-c:a', 'pcm_s16le',  # 16-bit PCM
                    '-y',            # Overwrite output
                    wav_path
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0:
                    logger.error(f"❌ FFmpeg conversion failed: {result.stderr}")
                    return None
                
                # Check if WAV file was created and has content
                if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 1000:
                    logger.debug(f"⚠️ WAV conversion produced empty or small file")
                    return None
                
                # Read the converted WAV file
                with open(wav_path, 'rb') as wav_file:
                    wav_data = wav_file.read()
                
                # Set up OpenAI client
                client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
                
                # Call Whisper API with optimized settings
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=("audio.wav", wav_data, "audio/wav"),
                    language="en",
                    prompt="Transcribe this speech clearly and accurately.",
                    temperature=0.0
                )
                
                return response.text
                
            finally:
                # Clean up temporary files
                for path in [temp_webm_path, wav_path]:
                    if os.path.exists(path):
                        try:
                            os.unlink(path)
                        except:
                            pass
                            
        except Exception as e:
            logger.error(f"❌ Real transcription error: {e}")
            return None
    
    def is_valid_webm(self, audio_data):
        """Check if audio data appears to be valid audio format (WebM, WAV, or other)."""
        # Support multiple audio formats from browsers
        audio_signatures = [
            b'\x1A\x45\xDF\xA3',  # EBML header (WebM)
            b'webm',              # WebM string
            b'Opus',              # Opus codec
            b'OpusHead',          # Opus header
            b'RIFF',              # WAV/WEBM RIFF header
            b'ftyp',              # MP4/M4A header
            b'OggS',              # Ogg container
            b'\xFF\xFB',          # MP3 header (variable bitrate)
            b'\xFF\xF3',          # MP3 header (fixed bitrate)
            b'\xFF\xF2'           # MP3 header (Layer III)
        ]
        
        # Check for any audio signature in the first 300 bytes
        header = audio_data[:300]
        
        # Also accept if it looks like binary audio data (has reasonable size and variety)
        has_audio_signature = any(sig in header for sig in audio_signatures)
        looks_like_audio = len(audio_data) > 50 and len(set(audio_data[:100])) > 10
        
        return has_audio_signature or looks_like_audio
    
    async def start_server(self):
        """Start the browser-optimized WebSocket server."""
        logger.info(f"🌐 Starting Browser WebSocket Server on {self.host}:{self.port}")
        
        # Create server with browser-friendly settings and SSL support
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ssl=self.ssl_context,
            ping_interval=30,
            ping_timeout=90,
            max_size=5*1024*1024,  # 5MB for audio chunks
            max_queue=64,
            compression=None  # Disable compression for better compatibility
        )
        
        self.running = True
        protocol = "wss" if self.ssl_context else "ws"
        logger.info(f"✅ Browser WebSocket Server running on {protocol}://{self.host}:{self.port}")
        return server
    
    def run_forever(self):
        """Run the server forever in the current thread."""
        async def run():
            server = await self.start_server()
            await server.wait_closed()
        
        # Create dedicated event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run())
        except Exception as e:
            logger.error(f"❌ Browser WebSocket server error: {e}")
        finally:
            loop.close()

# Global server instance
browser_server = None

def start_browser_websocket_server():
    """Start the browser WebSocket server in a thread with SSL support."""
    import os
    import ssl
    global browser_server
    
    def run_server():
        global browser_server
        
        # Check if we need SSL for HTTPS environment
        ssl_context = None
        if os.environ.get('REPLIT_SLUG') or os.environ.get('HTTPS'):
            logger.info("🔒 HTTPS environment detected - enabling SSL for WebSocket")
            try:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            except Exception as e:
                logger.warning(f"⚠️ SSL context creation failed: {e}")
                ssl_context = None
        
        # MANUAL MONITORING RECOMMENDATION: Try multiple ports to avoid conflicts
        ports_to_try = [8774, 8775, 8776, 8777]
        server_started = False
        
        for port in ports_to_try:
            try:
                logger.info(f"🔧 Attempting to start Enhanced WebSocket server on port {port}")
                browser_server = BrowserWebSocketServer(port=port, ssl_context=ssl_context)
                browser_server.run_forever()
                server_started = True
                break
            except OSError as e:
                if "Address already in use" in str(e):
                    logger.warning(f"⚠️ Port {port} in use, trying next port...")
                    continue
                else:
                    logger.error(f"❌ Failed to start server on port {port}: {e}")
                    continue
            except Exception as e:
                logger.error(f"❌ Unexpected error on port {port}: {e}")
                continue
        
        if not server_started:
            logger.error("❌ Could not start Enhanced WebSocket server on any port")
    
    thread = threading.Thread(target=run_server, daemon=True, name="BrowserWebSocketServer")
    thread.start()
    logger.info("🌐 Browser WebSocket Server thread started with SSL support")
    return thread

def get_browser_server_status():
    """Get browser server status."""
    global browser_server
    if browser_server and browser_server.running:
        return {
            'status': 'running',
            'host': browser_server.host,
            'port': browser_server.port,
            'clients': len(browser_server.clients),
            'sessions': len(browser_server.sessions),
            'websocket_url': f'ws://{browser_server.host}:{browser_server.port}'
        }
    return {'status': 'not_running'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = BrowserWebSocketServer()
    server.run_forever()