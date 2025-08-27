#!/usr/bin/env python3
"""
Browser WebSocket Server - Optimized specifically for browser compatibility
Uses minimal WebSocket implementation designed for browser connections
"""

import asyncio
import websockets
import json
import logging
import time
import uuid
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class BrowserWebSocketServer:
    """WebSocket server optimized specifically for browser connections."""
    
    def __init__(self, host="0.0.0.0", port=8771):
        self.host = host
        self.port = port
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
        """Handle audio data from browser MediaRecorder."""
        session_id = self.sessions.get(client_id, 'unknown')
        timestamp = datetime.now().strftime('%H:%M:%S')
        audio_size = len(audio_data)
        
        logger.info(f"🎵 Received browser audio: {audio_size} bytes from {client_id}")
        
        # Generate mock transcription for immediate feedback
        mock_responses = [
            "Hello, this is working perfectly!",
            "Browser audio transcription is functioning.",
            "Your microphone input is being processed.",
            "Real-time WebSocket transcription active.",
            "Audio chunks successfully received and processed."
        ]
        
        import random
        text = random.choice(mock_responses)
        is_final = audio_size > 500  # Larger chunks are considered final
        
        # Send transcription back to browser
        transcription = {
            'type': 'transcription_result',
            'session_id': session_id,
            'text': f"[{timestamp}] {text} (Audio: {audio_size} bytes)",
            'is_final': is_final,
            'confidence': 0.95,
            'timestamp': time.time()
        }
        
        await websocket.send(json.dumps(transcription))
        logger.info(f"📝 Sent browser transcription: {text[:30]}...")
    
    async def start_server(self):
        """Start the browser-optimized WebSocket server."""
        logger.info(f"🌐 Starting Browser WebSocket Server on {self.host}:{self.port}")
        
        # Create server with browser-friendly settings
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=90,
            max_size=5*1024*1024,  # 5MB for audio chunks
            max_queue=64,
            compression=None  # Disable compression for better compatibility
        )
        
        self.running = True
        logger.info(f"✅ Browser WebSocket Server running on ws://{self.host}:{self.port}")
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
    """Start the browser WebSocket server in a thread."""
    global browser_server
    
    def run_server():
        global browser_server
        browser_server = BrowserWebSocketServer()
        browser_server.run_forever()
    
    thread = threading.Thread(target=run_server, daemon=True, name="BrowserWebSocketServer")
    thread.start()
    logger.info("🌐 Browser WebSocket Server thread started")
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