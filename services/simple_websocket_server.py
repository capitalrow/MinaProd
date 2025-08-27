#!/usr/bin/env python3
"""
Simple WebSocket Server - Standalone implementation for immediate testing
Bypasses all import conflicts and circular dependencies
"""

import asyncio
import websockets
import json
import logging
import time
import uuid
from datetime import datetime
import threading
import base64

logger = logging.getLogger(__name__)

class SimpleWebSocketServer:
    """Ultra-simple WebSocket server for immediate audio transcription testing."""
    
    def __init__(self, host="0.0.0.0", port=8767):
        self.host = host
        self.port = port
        self.clients = {}
        self.sessions = {}
        self.running = False
        
    async def handle_connection(self, websocket, path):
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
                'message': 'Connected to Simple WebSocket Server'
            }))
            
            # Listen for messages
            async for message in websocket:
                await self.handle_message(websocket, client_id, message)
                
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
            if isinstance(message, bytes):
                # Handle binary audio data
                await self.handle_audio_data(websocket, client_id, message)
            else:
                # Handle JSON messages
                data = json.loads(message)
                await self.handle_json_message(websocket, client_id, data)
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
        
        # Mock transcription for immediate testing
        timestamp = datetime.now().strftime('%H:%M:%S')
        audio_size = len(audio_data)
        
        # Simulate realistic transcription responses
        mock_responses = [
            "Hello, this is a test transcription.",
            "The audio is being processed successfully.",
            "Real-time transcription is working properly.",
            "Audio chunk received and processed.",
            "Testing microphone input and WebSocket connection."
        ]
        
        import random
        text = random.choice(mock_responses)
        is_final = audio_size > 1000  # Simulate final vs interim
        
        # Send transcription result
        await websocket.send(json.dumps({
            'type': 'transcription_result',
            'session_id': session_id,
            'text': f"[{timestamp}] {text} (Audio: {audio_size} bytes)",
            'is_final': is_final,
            'confidence': 0.92,
            'timestamp': time.time()
        }))
        
        logger.info(f"📝 Sent mock transcription to {client_id}: {text[:30]}...")
    
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"🚀 Starting Simple WebSocket Server on {self.host}:{self.port}")
        
        server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=60
        )
        
        self.running = True
        logger.info(f"✅ Simple WebSocket Server running on ws://{self.host}:{self.port}")
        return server
    
    def run_server(self):
        """Run server in thread-safe way."""
        async def run():
            server = await self.start_server()
            await server.wait_closed()
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run())

# Global server instance
simple_server = None

def start_simple_websocket_server():
    """Start the simple WebSocket server in a thread."""
    global simple_server
    
    def run_server():
        global simple_server
        simple_server = SimpleWebSocketServer()
        simple_server.run_server()
    
    thread = threading.Thread(target=run_server, daemon=True, name="SimpleWebSocketServer")
    thread.start()
    logger.info("🚀 Simple WebSocket Server thread started")
    return thread

def get_simple_server_status():
    """Get server status."""
    global simple_server
    if simple_server and simple_server.running:
        return {
            'status': 'running',
            'host': simple_server.host,
            'port': simple_server.port,
            'clients': len(simple_server.clients),
            'sessions': len(simple_server.sessions)
        }
    return {'status': 'not_running'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = SimpleWebSocketServer()
    server.run_server()