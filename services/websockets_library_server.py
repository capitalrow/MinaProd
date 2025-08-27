#!/usr/bin/env python3
"""
WebSocket Library Server - Uses the standard websockets library
Ensures 100% browser compatibility by using the official WebSocket implementation
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

class WebSocketLibraryServer:
    """Production-grade WebSocket server using the standard websockets library."""
    
    def __init__(self, host="0.0.0.0", port=8770):  # Changed port to avoid conflicts
        self.host = host
        self.port = port
        self.clients = {}
        self.sessions = {}
        self.running = False
        
    async def handle_connection(self, websocket):
        """Handle a WebSocket connection."""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        
        logger.info(f"✅ Client connected: {client_id}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'connected',
                'client_id': client_id,
                'server_time': time.time(),
                'message': 'Connected to WebSocket Library Server'
            }))
            
            # Listen for messages
            async for message in websocket:
                try:
                    await self.handle_message(websocket, client_id, message)
                except Exception as e:
                    logger.error(f"❌ Error handling message from {client_id}: {e}")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"❌ Error with client {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.sessions:
                del self.sessions[client_id]
    
    async def handle_message(self, websocket, client_id, message):
        """Handle incoming messages."""
        try:
            if isinstance(message, str):
                # Handle JSON messages
                data = json.loads(message)
                await self.handle_json_message(websocket, client_id, data)
            elif isinstance(message, bytes):
                # Handle binary audio data
                await self.handle_audio_data(websocket, client_id, message)
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
    
    async def handle_json_message(self, websocket, client_id, data):
        """Handle JSON control messages."""
        message_type = data.get('type')
        
        if message_type == 'join_session':
            session_id = data.get('session_id')
            self.sessions[client_id] = session_id
            
            logger.info(f"📝 Client {client_id} joined session {session_id}")
            
            await websocket.send(json.dumps({
                'type': 'session_joined',
                'session_id': session_id,
                'client_id': client_id,
                'timestamp': time.time()
            }))
            
        elif message_type == 'ping':
            await websocket.send(json.dumps({
                'type': 'pong',
                'timestamp': time.time()
            }))
    
    async def handle_audio_data(self, websocket, client_id, audio_data):
        """Handle binary audio data and send mock transcription."""
        session_id = self.sessions.get(client_id, 'unknown')
        timestamp = datetime.now().strftime('%H:%M:%S')
        audio_size = len(audio_data)
        
        # Mock transcription responses for immediate testing
        mock_responses = [
            "Hello, this is a test transcription.",
            "The WebSocket library server is working perfectly.",
            "Audio processing is functioning correctly.",
            "Real-time transcription is active and responsive.",
            "Microphone input received and processed successfully."
        ]
        
        import random
        text = random.choice(mock_responses)
        is_final = audio_size > 1000  # Simulate final vs interim
        
        # Send transcription result
        result = {
            'type': 'transcription_result',
            'session_id': session_id,
            'text': f"[{timestamp}] {text} (Audio: {audio_size} bytes)",
            'is_final': is_final,
            'confidence': 0.92,
            'timestamp': time.time()
        }
        
        await websocket.send(json.dumps(result))
        logger.info(f"📝 Sent transcription to {client_id}: {text[:30]}...")
    
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"🚀 Starting WebSocket Library Server on {self.host}:{self.port}")
        
        server = await websockets.serve(
            lambda websocket, path: self.handle_connection(websocket),
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=60,
            max_size=2**20,  # 1MB max message size
            max_queue=32
        )
        
        self.running = True
        logger.info(f"✅ WebSocket Library Server running on ws://{self.host}:{self.port}")
        return server
    
    def run_server(self):
        """Run the server in current thread."""
        async def run():
            server = await self.start_server()
            await server.wait_closed()
        
        # Set up event loop for this thread
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run())
        except Exception as e:
            logger.error(f"❌ Server error: {e}")

# Global server instance
library_server = None

def start_websocket_library_server():
    """Start the WebSocket library server in a thread."""
    global library_server
    
    def run_server():
        global library_server
        library_server = WebSocketLibraryServer()
        library_server.run_server()
    
    thread = threading.Thread(target=run_server, daemon=True, name="WebSocketLibraryServer")
    thread.start()
    logger.info("🚀 WebSocket Library Server thread started")
    return thread

def get_library_server_status():
    """Get server status."""
    global library_server
    if library_server and library_server.running:
        return {
            'status': 'running',
            'host': library_server.host,
            'port': library_server.port,
            'clients': len(library_server.clients),
            'sessions': len(library_server.sessions),
            'websocket_url': f'ws://{library_server.host}:{library_server.port}'
        }
    return {'status': 'not_running'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = WebSocketLibraryServer()
    server.run_server()