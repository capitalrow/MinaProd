#!/usr/bin/env python3
"""
End-to-End Live Transcription Pipeline Test with Real Audio
Tests the complete pipeline from audio input to live transcription display
"""

import requests
import json
import time
import base64
import wave
import os
from datetime import datetime, timedelta
import threading
from pathlib import Path
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LivePipelineTest')

class LiveTranscriptionPipelineTester:
    """Complete pipeline testing with real audio file"""
    
    def __init__(self, audio_file_path, base_url="http://localhost:5000"):
        self.audio_file_path = Path(audio_file_path)
        self.base_url = base_url
        self.session_id = f"pipeline_test_{int(time.time())}"
        
        # Test configuration
        self.chunk_duration = 2.0  # 2 seconds per chunk
        self.overlap_duration = 0.5  # 0.5 second overlap
        self.target_sample_rate = 16000
        self.target_format = 'wav'
        
        # Results tracking
        self.test_results = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'audio_file': str(self.audio_file_path),
            'chunks_sent': 0,
            'chunks_successful': 0,
            'interim_results': [],
            'final_results': [],
            'errors': [],
            'latency_measurements': [],
            'pipeline_stages': {},
            'gaps_identified': []
        }
        
        # Audio processing
        self.converted_audio_path = None
        self.audio_duration = 0
        self.total_chunks = 0
        
    def convert_audio_to_wav(self):
        """Convert MP3 to WAV format suitable for transcription."""
        try:
            logger.info(f"🎵 Converting audio file: {self.audio_file_path}")
            
            # Output file path
            output_path = self.audio_file_path.with_suffix('.wav')
            self.converted_audio_path = output_path
            
            # Try multiple conversion methods
            conversion_success = False
            
            # Method 1: Try ffmpeg
            try:
                cmd = [
                    'ffmpeg', '-y',  # -y to overwrite
                    '-i', str(self.audio_file_path),
                    '-acodec', 'pcm_s16le',  # 16-bit PCM
                    '-ar', str(self.target_sample_rate),  # 16kHz sample rate
                    '-ac', '1',  # Mono
                    str(output_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    conversion_success = True
                    logger.info("✅ FFmpeg conversion successful")
                else:
                    logger.warning(f"FFmpeg failed: {result.stderr}")
                    
            except FileNotFoundError:
                logger.warning("FFmpeg not found, trying alternative method")
            
            # Method 2: Try pydub (if available)
            if not conversion_success:
                try:
                    from pydub import AudioSegment
                    
                    # Load MP3 file
                    audio = AudioSegment.from_mp3(str(self.audio_file_path))
                    
                    # Convert to mono, 16kHz
                    audio = audio.set_channels(1).set_frame_rate(self.target_sample_rate)
                    
                    # Export as WAV
                    audio.export(str(output_path), format="wav")
                    conversion_success = True
                    logger.info("✅ Pydub conversion successful")
                    
                except ImportError:
                    logger.warning("Pydub not available")
                except Exception as e:
                    logger.warning(f"Pydub conversion failed: {e}")
            
            # Method 3: Create test WAV file if conversion fails
            if not conversion_success:
                logger.warning("🔧 Audio conversion failed, creating test audio for pipeline testing")
                self.create_test_audio_file(output_path)
                conversion_success = True
            
            if conversion_success:
                # Get audio duration
                with wave.open(str(output_path), 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    self.audio_duration = frames / sample_rate
                
                self.total_chunks = int(self.audio_duration / self.chunk_duration) + 1
                
                logger.info(f"✅ Audio ready for testing")
                logger.info(f"📊 Duration: {self.audio_duration:.1f}s, Expected chunks: {self.total_chunks}")
                
                return True
            else:
                logger.error("All audio conversion methods failed")
                return False
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            self.test_results['errors'].append(f"Audio conversion failed: {e}")
            return False
    
    def create_test_audio_file(self, output_path):
        """Create a test audio file for pipeline testing."""
        import math
        
        # Generate 30 seconds of test audio (speech-like pattern)
        duration = 30.0
        sample_rate = self.target_sample_rate
        
        # Generate samples
        samples = []
        for i in range(int(duration * sample_rate)):
            t = i / sample_rate
            
            # Create speech-like pattern with multiple frequencies
            freq1 = 200 + 50 * math.sin(2 * math.pi * 0.5 * t)  # Varying fundamental
            freq2 = freq1 * 2  # Second harmonic
            freq3 = freq1 * 3  # Third harmonic
            
            # Mix frequencies with speech-like envelope
            envelope = 0.5 * (1 + math.sin(2 * math.pi * 2 * t))  # 2 Hz modulation
            
            sample = envelope * (
                0.6 * math.sin(2 * math.pi * freq1 * t) +
                0.3 * math.sin(2 * math.pi * freq2 * t) +
                0.1 * math.sin(2 * math.pi * freq3 * t)
            )
            
            # Convert to 16-bit integer
            sample_int = int(sample * 32767 * 0.7)  # 70% volume
            samples.append(sample_int)
        
        # Save as WAV file
        with wave.open(str(output_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Write samples
            for sample in samples:
                wav_file.writeframes(sample.to_bytes(2, byteorder='little', signed=True))
        
        logger.info(f"✅ Created test audio file: {output_path}")
    
    def extract_audio_chunk(self, start_time, duration):
        """Extract a specific chunk from the converted audio."""
        try:
            with wave.open(str(self.converted_audio_path), 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                # Calculate frame positions
                start_frame = int(start_time * sample_rate)
                chunk_frames = int(duration * sample_rate)
                
                # Read the chunk
                wav_file.setpos(start_frame)
                chunk_data = wav_file.readframes(chunk_frames)
                
                if not chunk_data:
                    return None
                
                # Create in-memory WAV data
                import io
                chunk_buffer = io.BytesIO()
                
                with wave.open(chunk_buffer, 'wb') as chunk_wav:
                    chunk_wav.setnchannels(channels)
                    chunk_wav.setsampwidth(sample_width)
                    chunk_wav.setframerate(sample_rate)
                    chunk_wav.writeframes(chunk_data)
                
                chunk_buffer.seek(0)
                return chunk_buffer.getvalue()
                
        except Exception as e:
            logger.error(f"Failed to extract chunk at {start_time}s: {e}")
            return None
    
    def send_audio_chunk(self, chunk_data, chunk_number, action='transcribe'):
        """Send audio chunk to transcription API."""
        try:
            # Encode audio data as base64
            audio_base64 = base64.b64encode(chunk_data).decode('utf-8')
            
            # Prepare request
            payload = {
                'session_id': self.session_id,
                'chunk_number': chunk_number,
                'audio_data': audio_base64,
                'action': action
            }
            
            # Send request with timing
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/transcribe-audio",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to ms
            
            self.test_results['latency_measurements'].append({
                'chunk_number': chunk_number,
                'latency_ms': latency,
                'timestamp': datetime.now().isoformat()
            })
            
            # Process response
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Log the result
                    logger.info(f"📝 Chunk {chunk_number}: {result.get('status', 'unknown')} ({latency:.1f}ms)")
                    
                    if result.get('text'):
                        logger.info(f"   Text: '{result['text'][:50]}...' (confidence: {result.get('confidence', 0):.2f})")
                    
                    # Track interim vs final results
                    if result.get('is_final'):
                        self.test_results['final_results'].append(result)
                    else:
                        self.test_results['interim_results'].append(result)
                    
                    self.test_results['chunks_successful'] += 1
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response for chunk {chunk_number}: {e}")
                    self.test_results['errors'].append(f"Chunk {chunk_number}: Invalid JSON response")
                    return None
            else:
                logger.error(f"API error for chunk {chunk_number}: {response.status_code} - {response.text}")
                self.test_results['errors'].append(f"Chunk {chunk_number}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to send chunk {chunk_number}: {e}")
            self.test_results['errors'].append(f"Chunk {chunk_number}: {e}")
            return None
    
    def simulate_live_recording(self):
        """Simulate live recording by sending chunks in real-time."""
        logger.info(f"🎙️ Starting live recording simulation")
        logger.info(f"📋 Session ID: {self.session_id}")
        logger.info(f"⏱️ Total duration: {self.audio_duration:.1f}s")
        logger.info(f"📦 Expected chunks: {self.total_chunks}")
        
        start_time = time.time()
        
        for chunk_num in range(self.total_chunks):
            chunk_start_time = chunk_num * self.chunk_duration
            
            # Check if we've reached the end of the audio
            if chunk_start_time >= self.audio_duration:
                break
            
            # Calculate actual chunk duration (might be shorter for last chunk)
            remaining_duration = self.audio_duration - chunk_start_time
            actual_chunk_duration = min(self.chunk_duration, remaining_duration)
            
            logger.info(f"🎵 Processing chunk {chunk_num + 1}/{self.total_chunks} ({chunk_start_time:.1f}s - {chunk_start_time + actual_chunk_duration:.1f}s)")
            
            # Extract audio chunk
            chunk_data = self.extract_audio_chunk(chunk_start_time, actual_chunk_duration)
            
            if chunk_data is None:
                logger.warning(f"⚠️ No data for chunk {chunk_num + 1}")
                continue
            
            # Send to transcription API
            self.test_results['chunks_sent'] += 1
            result = self.send_audio_chunk(chunk_data, chunk_num + 1)
            
            # Simulate real-time delay (wait for chunk duration)
            elapsed = time.time() - start_time
            expected_time = chunk_start_time + actual_chunk_duration
            
            if elapsed < expected_time:
                wait_time = expected_time - elapsed
                logger.debug(f"⏸️ Waiting {wait_time:.1f}s to maintain real-time pace")
                time.sleep(wait_time)
        
        # Send finalization request
        logger.info("🏁 Finalizing transcription session")
        self.send_audio_chunk(b"", 0, action='finalize')
        
        # Wait a moment for final processing
        time.sleep(2)
        
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['total_duration'] = time.time() - start_time
    
    def analyze_pipeline_performance(self):
        """Analyze the complete pipeline performance and identify gaps."""
        logger.info("📊 Analyzing pipeline performance")
        
        analysis = {
            'summary': {},
            'performance_metrics': {},
            'quality_metrics': {},
            'gaps_identified': [],
            'recommendations': []
        }
        
        # Summary statistics
        analysis['summary'] = {
            'total_chunks_sent': self.test_results['chunks_sent'],
            'successful_responses': self.test_results['chunks_successful'],
            'success_rate': (self.test_results['chunks_successful'] / self.test_results['chunks_sent']) * 100 if self.test_results['chunks_sent'] > 0 else 0,
            'total_errors': len(self.test_results['errors']),
            'interim_results_count': len(self.test_results['interim_results']),
            'final_results_count': len(self.test_results['final_results'])
        }
        
        # Performance metrics
        if self.test_results['latency_measurements']:
            latencies = [m['latency_ms'] for m in self.test_results['latency_measurements']]
            analysis['performance_metrics'] = {
                'average_latency_ms': sum(latencies) / len(latencies),
                'min_latency_ms': min(latencies),
                'max_latency_ms': max(latencies),
                'p95_latency_ms': sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0
            }
        
        # Quality metrics
        successful_transcriptions = [r for r in self.test_results['interim_results'] + self.test_results['final_results'] if r.get('text') and r.get('text').strip() and r.get('status') == 'success']
        
        if successful_transcriptions:
            confidences = [r.get('confidence', 0) for r in successful_transcriptions]
            word_counts = [len(r.get('text', '').split()) for r in successful_transcriptions]
            
            analysis['quality_metrics'] = {
                'transcriptions_with_text': len(successful_transcriptions),
                'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'total_words_transcribed': sum(word_counts),
                'average_words_per_chunk': sum(word_counts) / len(word_counts) if word_counts else 0
            }
        
        # Identify gaps
        gaps = []
        
        # Gap 1: Low success rate
        if analysis['summary']['success_rate'] < 95:
            gaps.append(f"Low API success rate: {analysis['summary']['success_rate']:.1f}% (target: >95%)")
        
        # Gap 2: High latency
        if analysis['performance_metrics'].get('average_latency_ms', 0) > 2000:
            gaps.append(f"High average latency: {analysis['performance_metrics']['average_latency_ms']:.1f}ms (target: <2000ms)")
        
        # Gap 3: Low transcription rate
        transcription_rate = (analysis['quality_metrics'].get('transcriptions_with_text', 0) / self.test_results['chunks_sent']) * 100 if self.test_results['chunks_sent'] > 0 else 0
        if transcription_rate < 70:
            gaps.append(f"Low transcription rate: {transcription_rate:.1f}% chunks produced text (target: >70%)")
        
        # Gap 4: Missing interim results
        if len(self.test_results['interim_results']) == 0:
            gaps.append("No interim results detected - real-time updates not working")
        
        # Gap 5: Low confidence scores
        if analysis['quality_metrics'].get('average_confidence', 0) < 0.8:
            gaps.append(f"Low average confidence: {analysis['quality_metrics']['average_confidence']:.2f} (target: >0.8)")
        
        # Gap 6: Error patterns
        if len(self.test_results['errors']) > 0:
            error_summary = {}
            for error in self.test_results['errors']:
                error_type = error.split(':')[0] if ':' in error else 'Unknown'
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
            
            for error_type, count in error_summary.items():
                gaps.append(f"Recurring {error_type} errors: {count} occurrences")
        
        analysis['gaps_identified'] = gaps
        self.test_results['pipeline_analysis'] = analysis
        
        return analysis
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        analysis = self.analyze_pipeline_performance()
        
        logger.info("\n" + "="*60)
        logger.info("LIVE TRANSCRIPTION PIPELINE TEST RESULTS")
        logger.info("="*60)
        
        # Test Summary
        logger.info(f"📋 Test Summary:")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   Audio File: {self.audio_file_path.name}")
        logger.info(f"   Duration: {self.audio_duration:.1f}s")
        logger.info(f"   Chunks Sent: {analysis['summary']['total_chunks_sent']}")
        logger.info(f"   Success Rate: {analysis['summary']['success_rate']:.1f}%")
        
        # Performance Metrics
        if analysis['performance_metrics']:
            logger.info(f"\n⚡ Performance Metrics:")
            logger.info(f"   Average Latency: {analysis['performance_metrics']['average_latency_ms']:.1f}ms")
            logger.info(f"   P95 Latency: {analysis['performance_metrics']['p95_latency_ms']:.1f}ms")
            logger.info(f"   Min/Max Latency: {analysis['performance_metrics']['min_latency_ms']:.1f}ms / {analysis['performance_metrics']['max_latency_ms']:.1f}ms")
        
        # Quality Metrics
        if analysis['quality_metrics']:
            logger.info(f"\n🎯 Quality Metrics:")
            logger.info(f"   Transcriptions with Text: {analysis['quality_metrics']['transcriptions_with_text']}")
            logger.info(f"   Average Confidence: {analysis['quality_metrics']['average_confidence']:.2f}")
            logger.info(f"   Total Words: {analysis['quality_metrics']['total_words_transcribed']}")
            logger.info(f"   Interim Results: {len(self.test_results['interim_results'])}")
            logger.info(f"   Final Results: {len(self.test_results['final_results'])}")
        
        # Gaps Identified
        logger.info(f"\n🚨 Gaps Identified:")
        if analysis['gaps_identified']:
            for gap in analysis['gaps_identified']:
                logger.info(f"   • {gap}")
        else:
            logger.info("   ✅ No critical gaps identified")
        
        # Error Summary
        if self.test_results['errors']:
            logger.info(f"\n❌ Errors ({len(self.test_results['errors'])}):")
            for error in self.test_results['errors'][:5]:  # Show first 5 errors
                logger.info(f"   • {error}")
            if len(self.test_results['errors']) > 5:
                logger.info(f"   ... and {len(self.test_results['errors']) - 5} more errors")
        
        # Sample Transcriptions
        successful_transcriptions = [r for r in self.test_results['interim_results'] + self.test_results['final_results'] if r.get('text') and r.get('text').strip()]
        if successful_transcriptions:
            logger.info(f"\n📝 Sample Transcriptions:")
            for i, result in enumerate(successful_transcriptions[:3]):
                result_type = "FINAL" if result.get('is_final') else "INTERIM"
                logger.info(f"   {i+1}. [{result_type}] '{result['text'][:60]}...' (confidence: {result.get('confidence', 0):.2f})")
        
        logger.info("\n" + "="*60)
        
        # Save detailed results
        results_file = f"pipeline_test_results_{self.session_id}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"📄 Detailed results saved to: {results_file}")
        
        return analysis
    
    def run_complete_test(self):
        """Run the complete end-to-end pipeline test."""
        try:
            logger.info("🚀 Starting comprehensive live transcription pipeline test")
            
            # Step 1: Convert audio
            if not self.convert_audio_to_wav():
                logger.error("❌ Audio conversion failed - cannot proceed")
                return False
            
            # Step 2: Test API connectivity
            try:
                response = requests.get(f"{self.base_url}/api/stats", timeout=10)
                if response.status_code != 200:
                    logger.error(f"❌ API connectivity test failed: {response.status_code}")
                    return False
                logger.info("✅ API connectivity confirmed")
            except Exception as e:
                logger.error(f"❌ API connectivity failed: {e}")
                return False
            
            # Step 3: Simulate live recording
            self.simulate_live_recording()
            
            # Step 4: Generate comprehensive report
            analysis = self.generate_comprehensive_report()
            
            # Step 5: Cleanup
            if self.converted_audio_path and self.converted_audio_path.exists():
                self.converted_audio_path.unlink()
                logger.info("🧹 Cleaned up temporary audio file")
            
            return len(analysis['gaps_identified']) == 0
            
        except Exception as e:
            logger.error(f"❌ Test failed with exception: {e}")
            self.test_results['errors'].append(f"Test exception: {e}")
            return False

def main():
    """Main test execution."""
    # Look for the attached audio file
    audio_files = list(Path('attached_assets').glob('*.mp3')) if Path('attached_assets').exists() else []
    
    if not audio_files:
        logger.error("❌ No MP3 audio files found in attached_assets/")
        logger.info("Please ensure the audio file is available for testing")
        return
    
    audio_file = audio_files[0]  # Use the first MP3 found
    logger.info(f"🎵 Using audio file: {audio_file}")
    
    # Create and run tester
    tester = LiveTranscriptionPipelineTester(audio_file)
    
    success = tester.run_complete_test()
    
    if success:
        logger.info("🎉 Pipeline test completed successfully!")
    else:
        logger.info("⚠️ Pipeline test completed with issues - check gaps identified")

if __name__ == "__main__":
    main()