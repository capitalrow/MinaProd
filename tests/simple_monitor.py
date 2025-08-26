#!/usr/bin/env python3
"""
Simple Live Transcription Monitor
Tracks live sessions without complex setup
"""

import asyncio
import socketio
import time
import json
from datetime import datetime

class SimpleMonitor:
    def __init__(self):
        self.sio = socketio.AsyncClient()
        self.session_id = None
        self.session_start = None
        self.events = []
        self.interims = 0
        self.finals = 0
        self.first_response = None
        
        # Setup handlers
        @self.sio.on('connect')
        async def on_connect():
            print("🔗 Connected to server - ready to monitor")
        
        @self.sio.on('session_created')
        async def on_session_created(data):
            self.session_id = data.get('session_id')
            self.session_start = time.time()
            print(f"🆕 Session started: {self.session_id}")
        
        @self.sio.on('joined_session') 
        async def on_joined(data):
            self.session_id = data.get('session_id')
            if not self.session_start:
                self.session_start = time.time()
            print(f"🏠 Joined session: {self.session_id}")
        
        @self.sio.on('interim_transcript')
        async def on_interim(data):
            self.interims += 1
            current_time = time.time()
            
            if not self.first_response:
                self.first_response = current_time - self.session_start
                print(f"⚡ First response: {self.first_response:.2f}s")
            
            text = data.get('text', '')[:50]
            confidence = data.get('confidence', 0)
            print(f"📝 Interim #{self.interims}: '{text}...' (conf: {confidence:.2f})")
            
            self.events.append({
                'type': 'interim',
                'time': current_time - self.session_start,
                'text': data.get('text', ''),
                'confidence': confidence
            })
        
        @self.sio.on('final_transcript')
        async def on_final(data):
            self.finals += 1
            current_time = time.time()
            
            text = data.get('text', '')[:50]
            confidence = data.get('confidence', 0)
            print(f"✅ Final #{self.finals}: '{text}...' (conf: {confidence:.2f})")
            
            self.events.append({
                'type': 'final',
                'time': current_time - self.session_start,
                'text': data.get('text', ''),
                'confidence': confidence
            })
    
    async def run(self):
        print("🎤 Simple Live Transcription Monitor")
        print("="*40)
        
        try:
            await self.sio.connect('http://localhost:5000')
            
            print("👀 Monitoring all transcription events")
            print("📋 Go to /live and click 'Start Recording'")
            print("🗣️ Speak for 1-2 minutes, then press Ctrl+C here")
            print()
            
            # Monitor until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ Stopping monitor...")
                await self.generate_report()
        
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await self.sio.disconnect()
    
    async def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*50)
        print("📊 LIVE TRANSCRIPTION ANALYSIS")
        print("="*50)
        
        if not self.session_id:
            print("❌ No session detected - make sure to start recording")
            return
        
        duration = time.time() - self.session_start if self.session_start else 0
        
        print(f"\n🎯 SESSION SUMMARY:")
        print(f"   Session ID: {self.session_id}")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Total Events: {len(self.events)}")
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"   First Response: {self.first_response:.2f}s" if self.first_response else "   No response received")
        print(f"   Interim Transcripts: {self.interims}")
        print(f"   Final Transcripts: {self.finals}")
        
        if self.events:
            # Calculate average interval
            interim_times = [e['time'] for e in self.events if e['type'] == 'interim']
            if len(interim_times) > 1:
                intervals = [interim_times[i+1] - interim_times[i] for i in range(len(interim_times)-1)]
                avg_interval = sum(intervals) / len(intervals)
                print(f"   Average Interim Interval: {avg_interval:.2f}s")
        
        # Quality score
        score = self.calculate_quality_score(duration)
        print(f"\n⭐ QUALITY SCORE: {score}/10")
        
        # Latest transcripts
        print(f"\n📝 RECENT TRANSCRIPTS:")
        for event in self.events[-5:]:  # Last 5 events
            print(f"   {event['time']:.1f}s - {event['type'].upper()}: '{event['text'][:40]}...'")
        
        # Final transcript
        final_texts = [e['text'] for e in self.events if e['type'] == 'final']
        if final_texts:
            print(f"\n📄 FINAL TRANSCRIPT:")
            print(f"   '{final_texts[-1]}'")
    
    def calculate_quality_score(self, duration):
        """Simple quality scoring"""
        score = 5
        
        # Response time bonus
        if self.first_response and self.first_response <= 2.0:
            score += 2
        elif self.first_response and self.first_response <= 3.0:
            score += 1
        
        # Activity bonus
        if self.interims >= 5:
            score += 2
        elif self.interims >= 2:
            score += 1
        
        # Final transcript bonus
        if self.finals >= 1:
            score += 1
        
        return min(10, max(1, score))

async def main():
    monitor = SimpleMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())