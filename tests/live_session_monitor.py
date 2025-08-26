#!/usr/bin/env python3
"""
Live Session Monitoring Tool for Real-Environment Testing
Tracks real-time transcription performance during live microphone sessions
"""

import asyncio
import socketio
import time
import json
import threading
from datetime import datetime
from typing import Dict, List, Any
import requests

class LiveSessionMonitor:
    """Monitors live transcription sessions with comprehensive metrics"""
    
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self.session_id = None
        
        # Session tracking
        self.session_start_time = None
        self.session_end_time = None
        self.transcription_events = []
        self.performance_metrics = {
            'total_interims': 0,
            'total_finals': 0,
            'first_response_latency': None,
            'average_interim_interval': 0,
            'longest_silence_gap': 0,
            'chunk_count': 0,
            'last_activity_time': None
        }
        
        # Quality tracking
        self.transcript_history = []
        self.real_time_transcript = ""
        self.final_transcript = ""
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup WebSocket event handlers for monitoring"""
        
        @self.sio.on('connect')
        async def on_connect():
            print("🔗 Monitor connected to server")
        
        @self.sio.on('disconnect')
        async def on_disconnect():
            print("🔌 Monitor disconnected")
        
        @self.sio.on('joined_session')
        async def on_joined_session(data):
            self.session_id = data.get('session_id')
            print(f"🏠 Now monitoring session: {self.session_id}")
            if not self.session_start_time:
                self.session_start_time = time.time()
        
        @self.sio.on('session_created')
        async def on_session_created(data):
            self.session_id = data.get('session_id')
            print(f"🆕 Session created: {self.session_id}")
            if not self.session_start_time:
                self.session_start_time = time.time()
        
        @self.sio.on('interim_transcript')
        async def on_interim_transcript(data):
            current_time = time.time()
            
            # Track first response
            if self.performance_metrics['first_response_latency'] is None:
                self.performance_metrics['first_response_latency'] = current_time - self.session_start_time
                print(f"⚡ First interim response: {self.performance_metrics['first_response_latency']:.2f}s")
            
            # Update metrics
            self.performance_metrics['total_interims'] += 1
            self.performance_metrics['last_activity_time'] = current_time
            
            # Store event
            event = {
                'type': 'interim',
                'timestamp': current_time,
                'text': data.get('text', ''),
                'confidence': data.get('confidence', 0),
                'session_time': current_time - self.session_start_time
            }
            self.transcription_events.append(event)
            
            # Update real-time transcript
            self.real_time_transcript = data.get('text', '')
            
            print(f"📝 Interim #{self.performance_metrics['total_interims']}: '{data.get('text', '')[:50]}...' (confidence: {data.get('confidence', 0):.2f})")
        
        @self.sio.on('final_transcript')
        async def on_final_transcript(data):
            current_time = time.time()
            
            # Update metrics
            self.performance_metrics['total_finals'] += 1
            self.performance_metrics['last_activity_time'] = current_time
            
            # Store event
            event = {
                'type': 'final',
                'timestamp': current_time,
                'text': data.get('text', ''),
                'confidence': data.get('confidence', 0),
                'session_time': current_time - self.session_start_time
            }
            self.transcription_events.append(event)
            
            # Update final transcript
            self.final_transcript = data.get('text', '')
            
            print(f"✅ Final #{self.performance_metrics['total_finals']}: '{data.get('text', '')[:50]}...' (confidence: {data.get('confidence', 0):.2f})")
        
        @self.sio.on('ack')
        async def on_ack(data):
            self.performance_metrics['chunk_count'] += 1
            if self.performance_metrics['chunk_count'] % 10 == 0:
                print(f"📦 Processed {self.performance_metrics['chunk_count']} audio chunks")
    
    async def start_monitoring(self, target_session_id: str = None):
        """Start monitoring a live session"""
        print("🎬 Starting Live Session Monitor")
        print("="*50)
        
        try:
            # Connect to WebSocket
            await self.sio.connect(self.server_url)
            await asyncio.sleep(1)
            
            if target_session_id:
                # Monitor specific session
                self.session_id = target_session_id
                print(f"🎯 Monitoring existing session: {self.session_id}")
            else:
                # We'll join any session that gets created
                print("👀 Waiting for session to be created via web interface...")
                print("📋 Go to /live page and click 'Start Recording' now!")
            
            self.session_start_time = time.time()
            
            print("🔍 Monitoring active - watching for transcription events...")
            print()
            print("📋 INSTRUCTIONS:")
            print("   1. Go to /live page in your browser")
            print("   2. Click 'Start Recording' to begin live transcription")
            print("   3. Speak naturally for up to 2 minutes")
            print("   4. Monitor will automatically track all events")
            print("   5. Press Ctrl+C here when done to generate report")
            print()
            print("⏳ Waiting for recording to start...")
            
            # Monitor until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
                    
                    # Check for long silence gaps
                    if (self.performance_metrics['last_activity_time'] and 
                        time.time() - self.performance_metrics['last_activity_time'] > 5):
                        gap = time.time() - self.performance_metrics['last_activity_time']
                        if gap > self.performance_metrics['longest_silence_gap']:
                            self.performance_metrics['longest_silence_gap'] = gap
            
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                self.session_end_time = time.time()
                await self.generate_report()
        
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
        finally:
            await self.sio.disconnect()
    
    async def generate_report(self):
        """Generate comprehensive session analysis report"""
        print("\n" + "="*60)
        print("📊 LIVE SESSION ANALYSIS REPORT")
        print("="*60)
        
        session_duration = self.session_end_time - self.session_start_time if self.session_end_time else time.time() - self.session_start_time
        
        # Basic metrics
        print(f"\n🎯 SESSION OVERVIEW:")
        print(f"   Session ID: {self.session_id}")
        print(f"   Duration: {session_duration:.1f} seconds")
        print(f"   Start Time: {datetime.fromtimestamp(self.session_start_time).strftime('%H:%M:%S')}")
        print(f"   End Time: {datetime.fromtimestamp(self.session_end_time).strftime('%H:%M:%S') if self.session_end_time else 'Ongoing'}")
        
        # Performance metrics
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   First Response Latency: {self.performance_metrics['first_response_latency']:.2f}s" if self.performance_metrics['first_response_latency'] else "   No response received")
        print(f"   Total Interim Transcripts: {self.performance_metrics['total_interims']}")
        print(f"   Total Final Transcripts: {self.performance_metrics['total_finals']}")
        print(f"   Audio Chunks Processed: {self.performance_metrics['chunk_count']}")
        print(f"   Longest Silence Gap: {self.performance_metrics['longest_silence_gap']:.1f}s")
        
        # Calculate intervals
        if len(self.transcription_events) > 1:
            interim_intervals = []
            last_time = None
            for event in self.transcription_events:
                if event['type'] == 'interim':
                    if last_time:
                        interval = event['timestamp'] - last_time
                        interim_intervals.append(interval)
                    last_time = event['timestamp']
            
            if interim_intervals:
                avg_interval = sum(interim_intervals) / len(interim_intervals)
                print(f"   Average Interim Interval: {avg_interval:.2f}s")
        
        # Transcript analysis
        print(f"\n📝 TRANSCRIPT ANALYSIS:")
        print(f"   Real-time Transcript Length: {len(self.real_time_transcript)} chars")
        print(f"   Final Transcript Length: {len(self.final_transcript)} chars")
        print(f"   Word Count (final): {len(self.final_transcript.split()) if self.final_transcript else 0}")
        
        # Quality assessment
        quality_score = self._calculate_quality_score()
        print(f"\n⭐ QUALITY ASSESSMENT:")
        print(f"   Overall Quality Score: {quality_score}/10")
        print(f"   Rationale: {self._get_quality_rationale(quality_score)}")
        
        # Transcripts
        print(f"\n📄 TRANSCRIPTS:")
        print(f"   Real-time (as displayed): '{self.real_time_transcript}'")
        print(f"   Final transcript: '{self.final_transcript}'")
        
        # Event timeline
        print(f"\n📋 EVENT TIMELINE:")
        for i, event in enumerate(self.transcription_events[-10:]):  # Last 10 events
            print(f"   {event['session_time']:.1f}s - {event['type'].upper()}: '{event['text'][:40]}...' (conf: {event['confidence']:.2f})")
        
        # Return structured data
        return {
            'session_id': self.session_id,
            'duration': session_duration,
            'performance_metrics': self.performance_metrics,
            'quality_score': quality_score,
            'real_time_transcript': self.real_time_transcript,
            'final_transcript': self.final_transcript,
            'events': self.transcription_events
        }
    
    def _calculate_quality_score(self) -> int:
        """Calculate quality score from 1-10 based on performance metrics"""
        score = 5  # Base score
        
        # First response latency (up to +2 points)
        if self.performance_metrics['first_response_latency']:
            if self.performance_metrics['first_response_latency'] <= 2.0:
                score += 2
            elif self.performance_metrics['first_response_latency'] <= 3.0:
                score += 1
        
        # Interim frequency (up to +2 points)
        if self.performance_metrics['total_interims'] >= 10:
            score += 2
        elif self.performance_metrics['total_interims'] >= 5:
            score += 1
        
        # Final transcript quality (up to +2 points)
        if self.final_transcript and len(self.final_transcript) > 50:
            score += 2
        elif self.final_transcript and len(self.final_transcript) > 20:
            score += 1
        
        # Silence gaps (-1 for long gaps)
        if self.performance_metrics['longest_silence_gap'] > 10:
            score -= 1
        
        return max(1, min(10, score))
    
    def _get_quality_rationale(self, score: int) -> str:
        """Get explanation for quality score"""
        if score >= 9:
            return "Excellent performance with fast response times and comprehensive transcription"
        elif score >= 7:
            return "Good performance with acceptable latency and transcription quality"
        elif score >= 5:
            return "Average performance with room for improvement in responsiveness or accuracy"
        elif score >= 3:
            return "Below average performance with significant delays or transcription issues"
        else:
            return "Poor performance requiring major improvements to system responsiveness"

async def main():
    """Run the live session monitor"""
    monitor = LiveSessionMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    print("🎤 MINA Live Session Monitor")
    print("Ready to monitor real microphone transcription...")
    asyncio.run(main())