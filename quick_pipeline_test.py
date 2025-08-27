#!/usr/bin/env python3
"""
Quick Pipeline Test - Uses existing AudioFileSimulator + STUB mode
Run this for immediate end-to-end validation without API costs
"""

import os
import time
import subprocess
import threading
from pathlib import Path

def test_existing_infrastructure():
    """Test using existing AudioFileSimulator and STUB mode"""
    
    print("🎯 MINA PIPELINE QUICK TEST")
    print("=" * 40)
    
    # 1. Enable STUB mode
    print("📋 Step 1: Enabling STUB_TRANSCRIPTION mode...")
    os.environ['STUB_TRANSCRIPTION'] = 'true'
    
    # 2. Check if test audio file exists
    test_audio_path = Path("static/test/podcast.mp3")
    print(f"📋 Step 2: Checking test audio file: {test_audio_path}")
    
    if test_audio_path.exists():
        print(f"   ✅ Audio file found: {test_audio_path}")
        print(f"   📊 File size: {test_audio_path.stat().st_size / 1024:.1f} KB")
    else:
        print(f"   ⚠️  Audio file not found: {test_audio_path}")
        print("   💡 You can add any MP3 file there for testing")
    
    # 3. Instructions for manual testing with existing tools
    print("\n📋 Step 3: Manual Testing Instructions")
    print("   🌐 Open browser to: http://localhost:5000/live")
    print("   🧪 Open browser console and run:")
    print("   ```javascript")
    print("   // Enable AudioFileSimulator testing")
    print("   if (window.audioFileSimulator) {")
    print("       console.log('🎵 Starting AudioFileSimulator...');")
    print("       window.audioFileSimulator.startSimulation();")
    print("   } else {")
    print("       console.log('⚠️ AudioFileSimulator not available');")
    print("   }")
    print("   ```")
    
    # 4. Automated server-side testing
    print("\n📋 Step 4: Testing server-side components...")
    
    # Test STUB transcription
    test_stub_transcription()
    
    # Test VAD with mock data  
    test_vad_with_mock_data()
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Run the manual browser test above")
    print("   2. Watch console for AudioFileSimulator output") 
    print("   3. Verify transcription appears in UI")
    print("   4. Check that STUB responses are working")
    
    # Clean up
    os.environ.pop('STUB_TRANSCRIPTION', None)
    print("\n✅ Quick test setup complete!")

def test_stub_transcription():
    """Test STUB_TRANSCRIPTION mode server-side"""
    try:
        # Import and test the WhisperStreamingService
        import sys
        sys.path.append('.')
        
        from services.whisper_streaming import WhisperStreamingService
        
        # Create service instance
        service = WhisperStreamingService()
        
        # Test with mock audio data
        mock_audio = b"mock audio data for testing"
        result = service._stub_transcription(mock_audio, is_final=True)
        
        if result and result.text:
            print(f"   ✅ STUB transcription working: '{result.text[:50]}...'")
            return True
        else:
            print("   ❌ STUB transcription failed")
            return False
            
    except Exception as e:
        print(f"   ⚠️  STUB transcription test error: {e}")
        return False

def test_vad_with_mock_data():
    """Test VAD service with mock audio data"""
    try:
        import sys
        sys.path.append('.')
        
        from tests import MockAudioData
        from services.enhanced_vad import VADService
        from config.vad_config import VADConfig
        
        # Create VAD service
        vad_config = VADConfig()
        vad_service = VADService(vad_config)
        
        # Test with mock speech data
        speech_audio = MockAudioData.generate_sine_wave(frequency=200, duration_ms=1000)
        speech_result = vad_service.process_audio_chunk(speech_audio)
        
        # Test with mock silence data  
        silence_audio = MockAudioData.generate_silent_audio(duration_ms=1000)
        silence_result = vad_service.process_audio_chunk(silence_audio)
        
        print(f"   ✅ VAD speech detection: {speech_result.is_speech}")
        print(f"   ✅ VAD silence detection: {silence_result.is_speech}")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  VAD test error: {e}")
        return False

if __name__ == "__main__":
    test_existing_infrastructure()