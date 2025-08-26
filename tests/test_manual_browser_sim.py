#!/usr/bin/env python3
"""
Manual Browser Simulation Test
Tests the simulation system via direct JavaScript execution
"""

import asyncio
import socketio
import time
import json
import requests

class ManualBrowserSimulationTest:
    """Manual test for browser simulation functionality"""
    
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self.session_id = None
        
        # Metrics
        self.metrics = {
            'start_time': None,
            'first_interim_time': None,
            'interim_count': 0,
            'final_count': 0,
            'transcripts': []
        }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.sio.on('connect')
        async def on_connect():
            print("🔗 Connected to WebSocket")
        
        @self.sio.on('joined_session')
        async def on_joined_session(data):
            self.session_id = data.get('session_id')
            print(f"🏠 Joined session: {self.session_id}")
        
        @self.sio.on('interim_transcript')
        async def on_interim(data):
            self.metrics['interim_count'] += 1
            current_time = time.time()
            
            if self.metrics['first_interim_time'] is None:
                self.metrics['first_interim_time'] = current_time
                latency = current_time - self.metrics['start_time']
                print(f"🚀 First interim in {latency:.2f}s: '{data.get('text', '')[:40]}...'")
            
            self.metrics['transcripts'].append({
                'type': 'interim',
                'text': data.get('text', ''),
                'time': current_time
            })
            
            print(f"📝 Interim #{self.metrics['interim_count']}: '{data.get('text', '')[:50]}...'")
        
        @self.sio.on('final_transcript')
        async def on_final(data):
            self.metrics['final_count'] += 1
            current_time = time.time()
            
            self.metrics['transcripts'].append({
                'type': 'final',
                'text': data.get('text', ''),
                'time': current_time
            })
            
            print(f"✅ Final #{self.metrics['final_count']}: '{data.get('text', '')[:50]}...'")
    
    async def test_simulation_via_websocket(self):
        """Test simulation by monitoring WebSocket events"""
        print("\n🎭 Manual Browser Simulation Test")
        print("="*50)
        
        try:
            # Connect to WebSocket
            await self.sio.connect(self.server_url)
            
            # Create session
            session_response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.post(f"{self.server_url}/api/sessions")
            )
            session_data = session_response.json()
            test_session_id = session_data['session_id']
            
            # Join session
            await self.sio.emit('join_session', {'session_id': test_session_id})
            await asyncio.sleep(2)
            
            # Start monitoring
            self.metrics['start_time'] = time.time()
            print(f"🎬 Monitoring session: {test_session_id}")
            print("   (You should manually click 'Simulate from file' in the browser)")
            
            # Monitor for 30 seconds
            monitor_duration = 30
            end_time = time.time() + monitor_duration
            
            while time.time() < end_time:
                await asyncio.sleep(1)
                
                # Print periodic updates
                elapsed = time.time() - self.metrics['start_time']
                if int(elapsed) % 5 == 0:  # Every 5 seconds
                    print(f"   📊 {elapsed:.0f}s - Interims: {self.metrics['interim_count']}, Finals: {self.metrics['final_count']}")
            
            # Final results
            total_time = time.time() - self.metrics['start_time']
            first_interim_latency = None
            if self.metrics['first_interim_time']:
                first_interim_latency = self.metrics['first_interim_time'] - self.metrics['start_time']
            
            results = {
                'total_time': total_time,
                'first_interim_latency': first_interim_latency,
                'interim_count': self.metrics['interim_count'],
                'final_count': self.metrics['final_count'],
                'session_id': test_session_id,
                'transcripts': self.metrics['transcripts']
            }
            
            print("\n📊 RESULTS:")
            print(f"   Total monitoring time: {results['total_time']:.1f}s")
            print(f"   First interim latency: {results['first_interim_latency']:.2f}s" if first_interim_latency else "   No interims received")
            print(f"   Interims received: {results['interim_count']}")
            print(f"   Finals received: {results['final_count']}")
            print(f"   Session ID: {results['session_id']}")
            
            if results['transcripts']:
                print(f"   Sample transcript: '{results['transcripts'][0]['text'][:60]}...'")
            
            return results
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return {'error': str(e)}
        finally:
            await self.sio.disconnect()

async def main():
    """Run the manual browser simulation test"""
    tester = ManualBrowserSimulationTest()
    results = await tester.test_simulation_via_websocket()
    
    print("\n" + "="*60)
    print("🎯 MANUAL BROWSER SIMULATION TEST COMPLETE")
    print("="*60)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())