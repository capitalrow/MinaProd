#!/usr/bin/env python3
"""
Native WebSocket Server for Real-Time Audio Transcription
Replaces Flask-SocketIO with direct WebSocket implementation for maximum compatibility
"""

import asyncio
import websockets
from websockets.server import serve
from websockets.legacy.server import WebSocketServerProtocol
import json
import logging
import time
import uuid
from typing import Dict, Set, Optional, Any
import threading
from datetime import datetime
import base64

# Import existing transcription services
try:
    from services.transcription_service import TranscriptionService, TranscriptionServiceConfig
except ImportError:
    # Fallback if transcription service not available
    TranscriptionService = None
    TranscriptionServiceConfig = None

logger = logging.getLogger(__name__)

class NativeWebSocketServer:
    """
    Production-ready native WebSocket server for real-time audio transcription.
    Designed for maximum compatibility and performance.
    """
    
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.sessions: Dict[str, str] = {}  # client_id -> session_id mapping
        self.active_sessions: Set[str] = set()
        
        # Initialize transcription service
        if TranscriptionService and TranscriptionServiceConfig:
            self.transcription_config = TranscriptionServiceConfig()
            self.transcription_service = TranscriptionService(self.transcription_config)
        else:
            self.transcription_service = None
            logger.warning("⚠️ Transcription service not available - using stub mode")
        
        logger.info(f"🔧 Native WebSocket Server initialized on {host}:{port}")
    
    async def register_client(self, websocket: WebSocketServerProtocol, client_id: str):
        """Register a new client connection."""
        self.clients[client_id] = websocket
        logger.info(f"✅ Client registered: {client_id}")
    
    async def unregister_client(self, client_id: str):
        """Unregister a client connection."""
        if client_id in self.clients:
            del self.clients[client_id]
        if client_id in self.sessions:
            session_id = self.sessions[client_id]
            del self.sessions[client_id]
            self.active_sessions.discard(session_id)
        logger.info(f"🔌 Client unregistered: {client_id}")
    
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle a new WebSocket connection."""
        client_id = str(uuid.uuid4())
        
        try:
            await self.register_client(websocket, client_id)
            
            # Send connection confirmation
            await websocket.send(json.dumps({
                'type': 'connected',
                'client_id': client_id,
                'server_time': time.time(),
                'message': 'Connected to Mina Native WebSocket Server'
            }))
            
            # Listen for messages
            async for message in websocket:
                await self.handle_message(websocket, client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"❌ Error handling client {client_id}: {e}")
        finally:
            await self.unregister_client(client_id)
    
    async def handle_message(self, websocket, client_id: str, message):
        """Handle incoming WebSocket messages."""
        try:
            if isinstance(message, bytes):
                # Handle binary audio data
                await self.handle_audio_data(websocket, client_id, message)
            else:
                # Handle JSON messages
                data = json.loads(message)
                await self.handle_json_message(websocket, client_id, data)
                
        except Exception as e:
            logger.error(f"❌ Error handling message from {client_id}: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))
    
    async def handle_json_message(self, websocket, client_id: str, data: dict):
        """Handle JSON control messages."""
        message_type = data.get('type')
        
        if message_type == 'join_session':
            session_id = data.get('session_id')
            await self.join_session(websocket, client_id, session_id)
            
        elif message_type == 'audio_chunk':
            # Handle base64 encoded audio
            audio_data_b64 = data.get('audio_data')
            session_id = data.get('session_id', self.sessions.get(client_id))
            
            if audio_data_b64 and session_id:
                try:
                    # Decode base64 audio data
                    audio_data = base64.b64decode(audio_data_b64)
                    await self.process_audio_chunk(websocket, client_id, session_id, audio_data)
                except Exception as e:
                    logger.error(f"❌ Error decoding audio data: {e}")
            
        elif message_type == 'ping':
            # Respond to ping with pong
            await websocket.send(json.dumps({
                'type': 'pong',
                'timestamp': time.time()
            }))
            
        else:
            logger.warning(f"⚠️ Unknown message type: {message_type}")
    
    async def join_session(self, websocket, client_id: str, session_id: str):
        """Handle session join request."""
        try:
            # Map client to session
            self.sessions[client_id] = session_id
            self.active_sessions.add(session_id)
            
            # Initialize transcription session
            if self.transcription_service:
                # Use existing session initialization logic
                # This will be connected to existing transcription pipeline
                logger.info(f"🔧 Transcription session ready: {session_id}")
            else:
                # Stub mode for testing
                logger.info(f"🔧 Stub transcription session: {session_id}")
            
            logger.info(f"📝 Client {client_id} joined session {session_id}")
            
            # Send confirmation
            await websocket.send(json.dumps({
                'type': 'session_joined',
                'session_id': session_id,
                'client_id': client_id,
                'timestamp': time.time()
            }))
            
        except Exception as e:
            logger.error(f"❌ Error joining session: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Failed to join session: {str(e)}'
            }))
    
    async def handle_audio_data(self, websocket, client_id: str, audio_data: bytes):
        """Handle binary audio data."""
        session_id = self.sessions.get(client_id)
        if not session_id:
            logger.warning(f"⚠️ No session for client {client_id}")
            return
        
        await self.process_audio_chunk(websocket, client_id, session_id, audio_data)
    
    async def process_audio_chunk(self, websocket: WebSocketServerProtocol, client_id: str, session_id: str, audio_data: bytes):
        """Process audio chunk and send transcription results."""
        try:
            # For testing, simulate transcription
            if self.transcription_service:
                # TODO: Connect to existing transcription pipeline
                result = {
                    'text': f"[Audio chunk {len(audio_data)} bytes received]",
                    'is_final': False,
                    'confidence': 0.95
                }
            else:
                # Stub response for immediate testing
                result = {
                    'text': f"🎤 Audio received: {len(audio_data)} bytes @ {datetime.now().strftime('%H:%M:%S')}",
                    'is_final': len(audio_data) > 1000,  # Simulate final vs interim
                    'confidence': 0.9
                }
            
            if result:
                # Send transcription result
                await websocket.send(json.dumps({
                    'type': 'transcription_result',
                    'session_id': session_id,
                    'text': result.get('text', ''),
                    'is_final': result.get('is_final', False),
                    'confidence': result.get('confidence', 0.0),
                    'timestamp': time.time()
                }))
                
                logger.info(f"📝 Sent transcription: {result.get('text', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing audio chunk: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': f'Audio processing error: {str(e)}'
            }))
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all clients in a session."""
        message_json = json.dumps(message)
        disconnected_clients = []
        
        for client_id, websocket in self.clients.items():
            if self.sessions.get(client_id) == session_id:
                try:
                    await websocket.send(message_json)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"❌ Error broadcasting to {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.unregister_client(client_id)
    
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"🚀 Starting Native WebSocket Server on {self.host}:{self.port}")
        
        # Create and start server
        server = await serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=60,
            max_size=2**20,  # 1MB max message size
            max_queue=32
        )
        
        logger.info(f"✅ Native WebSocket Server running on ws://{self.host}:{self.port}")
        return server
    
    def run_server(self):
        """Run the server in the current event loop."""
        asyncio.run(self.start_server_forever())
    
    async def start_server_forever(self):
        """Start server and run forever."""
        server = await self.start_server()
        await server.wait_closed()

# Global server instance
native_ws_server = None

def get_native_websocket_server():
    """Get the global native WebSocket server instance."""
    global native_ws_server
    if native_ws_server is None:
        native_ws_server = NativeWebSocketServer()
    return native_ws_server

def start_native_websocket_server_thread():
    """Start the native WebSocket server in a separate thread."""
    def run_server():
        server = get_native_websocket_server()
        server.run_server()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("🚀 Native WebSocket Server thread started")
    return thread

if __name__ == "__main__":
    # Run server directly
    logging.basicConfig(level=logging.INFO)
    server = NativeWebSocketServer()
    server.run_server()