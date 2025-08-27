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
    
    def __init__(self, host="0.0.0.0", port=8773, ssl_context=None):
        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.clients = {}
        self.sessions = {}
        self.running = False
        
    async def handle_client(self, websocket):
        """Handle a browser WebSocket connection."""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        
        logger.info(f"🌐 Browser client connected: {client_id}")
        
        try:
            # Send immediate welcome message
            welcome = {
                'type': 'connected',
                'client_id': client_id,
                'server_time': time.time(),
                'message': 'Browser WebSocket Server Ready'
            }
            await websocket.send(json.dumps(welcome))
            
            # Handle messages from browser
            async for message in websocket:
                try:
                    if isinstance(message, str):
                        # JSON message from browser
                        data = json.loads(message)
                        await self.handle_browser_message(websocket, client_id, data)
                    else:
                        # Binary audio data from MediaRecorder
                        await self.handle_browser_audio(websocket, client_id, message)
                except Exception as e:
                    logger.error(f"❌ Error handling browser message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🌐 Browser client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"❌ Browser client error: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.sessions:
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
        """Handle audio data from browser MediaRecorder with real Whisper API transcription and instant feedback."""
        session_id = self.sessions.get(client_id, 'unknown')
        timestamp = datetime.now().strftime('%H:%M:%S')
        audio_size = len(audio_data)
        
        logger.info(f"🎵 Received browser audio: {audio_size} bytes from {client_id}")
        
        # Skip very small audio chunks to reduce API calls
        if audio_size < 1024:
            logger.debug(f"⏭️ Skipping small audio chunk: {audio_size} bytes")
            return
        
        # Send immediate interim feedback for excellent latency
        interim_response = {
            'type': 'transcription_result',
            'session_id': session_id,
            'text': "🎙️ Processing audio...",
            'is_final': False,
            'confidence': 0.1,
            'timestamp': time.time(),
            'processing': True
        }
        await websocket.send(json.dumps(interim_response))
        
        try:
            # Process audio with real OpenAI Whisper API
            transcription_text = await self.transcribe_audio_real(audio_data)
            
            if transcription_text and transcription_text.strip():
                is_final = audio_size > 2048
                confidence = 0.95
                
                # Send real transcription result
                final_response = {
                    'type': 'transcription_result',
                    'session_id': session_id,
                    'text': transcription_text.strip(),
                    'is_final': is_final,
                    'confidence': confidence,
                    'timestamp': time.time(),
                    'audio_duration': audio_size,
                    'processing': False
                }
                
                await websocket.send(json.dumps(final_response))
                logger.info(f"📝 Real transcription sent: {transcription_text[:50]}...")
            else:
                # No speech detected - send feedback
                no_speech_response = {
                    'type': 'transcription_result',
                    'session_id': session_id,
                    'text': "[No speech detected]",
                    'is_final': False,
                    'confidence': 0.0,
                    'timestamp': time.time(),
                    'processing': False
                }
                await websocket.send(json.dumps(no_speech_response))
                logger.debug("🔇 No speech detected in audio chunk")
                
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            # Send error feedback
            error_response = {
                'type': 'transcription_result',
                'session_id': session_id,
                'text': f"[Audio processing temporarily unavailable]",
                'is_final': False,
                'confidence': 0.0,
                'timestamp': time.time(),
                'processing': False
            }
            await websocket.send(json.dumps(error_response))
    
    async def transcribe_audio_real(self, audio_data):
        """Transcribe audio using OpenAI Whisper API with optimized audio processing."""
        try:
            # Check if audio data looks like valid WebM
            if len(audio_data) < 50 or not self.is_valid_webm(audio_data):
                logger.debug(f"⚠️ Audio data doesn't appear to be valid WebM format")
                return None
            
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
        """Check if audio data appears to be valid WebM format."""
        # WebM files typically start with EBML header
        webm_signatures = [
            b'\x1A\x45\xDF\xA3',  # EBML header
            b'webm',              # WebM string
            b'Opus',              # Opus codec
            b'OpusHead'           # Opus header
        ]
        
        # Check for any WebM signature in the first 200 bytes
        header = audio_data[:200]
        return any(sig in header for sig in webm_signatures)
    
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
        
        browser_server = BrowserWebSocketServer(ssl_context=ssl_context)
        browser_server.run_forever()
    
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