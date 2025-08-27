#!/usr/bin/env python3
"""
Synchronous WebSocket Server - Works with Flask eventlet without conflicts
Uses pure threading approach to avoid async event loop issues
"""

import socket
import threading
import time
import json
import base64
import hashlib
import struct
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SyncWebSocketServer:
    """Synchronous WebSocket server that avoids async event loop conflicts."""
    
    def __init__(self, host="0.0.0.0", port=8768):
        self.host = host
        self.port = port
        self.clients = {}
        self.sessions = {}
        self.running = False
        self.server_socket = None
        
    def start_server(self):
        """Start the synchronous WebSocket server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"✅ Sync WebSocket Server running on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        logger.error(f"❌ Error accepting connection: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Failed to start sync WebSocket server: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_client(self, client_socket, address):
        """Handle a WebSocket client connection."""
        client_id = f"client_{int(time.time())}"
        logger.info(f"✅ Client connected: {client_id} from {address}")
        
        try:
            # Perform WebSocket handshake
            if not self.perform_handshake(client_socket):
                logger.error(f"❌ WebSocket handshake failed for {client_id}")
                return
            
            self.clients[client_id] = client_socket
            
            # Send welcome message
            welcome_msg = {
                'type': 'connected',
                'client_id': client_id,
                'server_time': time.time(),
                'message': 'Connected to Sync WebSocket Server'
            }
            self.send_message(client_socket, json.dumps(welcome_msg))
            
            # Listen for messages
            while self.running:
                try:
                    message = self.receive_message(client_socket)
                    if message is None:
                        break
                    
                    self.handle_message(client_socket, client_id, message)
                    
                except Exception as e:
                    logger.error(f"❌ Error handling message from {client_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error with client {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.sessions:
                del self.sessions[client_id]
            client_socket.close()
            logger.info(f"🔌 Client {client_id} disconnected")
    
    def perform_handshake(self, client_socket):
        """Perform WebSocket handshake."""
        try:
            # Receive HTTP request
            data = client_socket.recv(1024).decode('utf-8')
            
            # Extract WebSocket key
            lines = data.split('\r\n')
            key = None
            for line in lines:
                if 'Sec-WebSocket-Key' in line:
                    key = line.split(':')[1].strip()
                    break
            
            if not key:
                return False
            
            # Generate accept key
            accept_key = base64.b64encode(
                hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
            ).decode()
            
            # Send handshake response
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n"
                "\r\n"
            )
            
            client_socket.send(response.encode())
            return True
            
        except Exception as e:
            logger.error(f"❌ Handshake error: {e}")
            return False
    
    def receive_message(self, client_socket):
        """Receive a WebSocket message."""
        try:
            # Read first 2 bytes for frame info
            first_bytes = client_socket.recv(2)
            if len(first_bytes) < 2:
                return None
            
            # Parse frame
            fin = first_bytes[0] & 0x80
            opcode = first_bytes[0] & 0x0f
            masked = first_bytes[1] & 0x80
            payload_length = first_bytes[1] & 0x7f
            
            # Handle extended payload length
            if payload_length == 126:
                length_bytes = client_socket.recv(2)
                payload_length = struct.unpack(">H", length_bytes)[0]
            elif payload_length == 127:
                length_bytes = client_socket.recv(8)
                payload_length = struct.unpack(">Q", length_bytes)[0]
            
            # Read mask key if present
            mask_key = None
            if masked:
                mask_key = client_socket.recv(4)
            
            # Read payload
            payload = client_socket.recv(payload_length)
            
            # Unmask payload if needed
            if mask_key:
                payload = bytes([payload[i] ^ mask_key[i % 4] for i in range(len(payload))])
            
            # Handle different opcodes
            if opcode == 1:  # Text frame
                return payload.decode('utf-8')
            elif opcode == 2:  # Binary frame
                return payload
            elif opcode == 8:  # Close frame
                return None
            elif opcode == 9:  # Ping frame
                self.send_pong(client_socket, payload)
                return "ping"
            
            return payload
            
        except Exception as e:
            logger.error(f"❌ Error receiving message: {e}")
            return None
    
    def send_message(self, client_socket, message):
        """Send a WebSocket message."""
        try:
            if isinstance(message, str):
                message = message.encode('utf-8')
                opcode = 1  # Text frame
            else:
                opcode = 2  # Binary frame
            
            # Create frame
            frame = bytearray()
            frame.append(0x80 | opcode)  # FIN + opcode
            
            length = len(message)
            if length < 126:
                frame.append(length)
            elif length < 65536:
                frame.append(126)
                frame.extend(struct.pack(">H", length))
            else:
                frame.append(127)
                frame.extend(struct.pack(">Q", length))
            
            frame.extend(message)
            client_socket.send(frame)
            
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
    
    def send_pong(self, client_socket, payload):
        """Send a pong frame."""
        frame = bytearray([0x8A])  # FIN + pong opcode
        frame.append(len(payload))
        frame.extend(payload)
        client_socket.send(frame)
    
    def handle_message(self, client_socket, client_id, message):
        """Handle incoming messages."""
        try:
            if isinstance(message, str) and message != "ping":
                # Handle JSON messages
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'join_session':
                    session_id = data.get('session_id')
                    self.sessions[client_id] = session_id
                    
                    logger.info(f"📝 Client {client_id} joined session {session_id}")
                    
                    response = {
                        'type': 'session_joined',
                        'session_id': session_id,
                        'client_id': client_id,
                        'timestamp': time.time()
                    }
                    self.send_message(client_socket, json.dumps(response))
                    
                elif message_type == 'ping':
                    response = {
                        'type': 'pong',
                        'timestamp': time.time()
                    }
                    self.send_message(client_socket, json.dumps(response))
                    
            elif isinstance(message, bytes):
                # Handle binary audio data
                self.handle_audio_data(client_socket, client_id, message)
                
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
    
    def handle_audio_data(self, client_socket, client_id, audio_data):
        """Handle binary audio data and send mock transcription."""
        session_id = self.sessions.get(client_id, 'unknown')
        timestamp = datetime.now().strftime('%H:%M:%S')
        audio_size = len(audio_data)
        
        # Mock transcription responses
        mock_responses = [
            "Hello, this is a test transcription.",
            "The sync WebSocket is working perfectly.",
            "Audio processing is functioning correctly.",
            "Real-time transcription is active.",
            "Microphone input received and processed."
        ]
        
        import random
        text = random.choice(mock_responses)
        is_final = audio_size > 1000
        
        # Send transcription result
        result = {
            'type': 'transcription_result',
            'session_id': session_id,
            'text': f"[{timestamp}] {text} (Audio: {audio_size} bytes)",
            'is_final': is_final,
            'confidence': 0.92,
            'timestamp': time.time()
        }
        
        self.send_message(client_socket, json.dumps(result))
        logger.info(f"📝 Sent transcription to {client_id}: {text[:30]}...")
    
    def stop_server(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

# Global server instance
sync_server = None

def start_sync_websocket_server():
    """Start the sync WebSocket server in a thread."""
    global sync_server
    
    def run_server():
        global sync_server
        sync_server = SyncWebSocketServer()
        sync_server.start_server()
    
    thread = threading.Thread(target=run_server, daemon=True, name="SyncWebSocketServer")
    thread.start()
    logger.info("🚀 Sync WebSocket Server thread started")
    return thread

def get_sync_server_status():
    """Get server status."""
    global sync_server
    if sync_server and sync_server.running:
        return {
            'status': 'running',
            'host': sync_server.host,
            'port': sync_server.port,
            'clients': len(sync_server.clients),
            'sessions': len(sync_server.sessions),
            'websocket_url': f'ws://{sync_server.host}:{sync_server.port}'
        }
    return {'status': 'not_running'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = SyncWebSocketServer()
    server.start_server()