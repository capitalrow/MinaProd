# MINA Transcription System - Manual Test Guide

## Quick Test Steps

### 1. Basic Functionality Test

1. **Open the Live Transcription Page**
   - Navigate to `/live` in your browser
   - You should see:
     - A large microphone button
     - Session stats showing 00:00 duration, 0 words, etc.
     - An empty transcript area with "Ready for Live Transcription" message

2. **Test Recording**
   - Click the microphone button (it should turn red when recording)
   - Say a few sentences clearly into your microphone
   - Click the button again to stop (it should return to normal color)
   - **Expected Result**: After 1-2 seconds, your speech should appear as text in the transcript area

3. **Check Stats**
   - After transcription appears, verify:
     - Word count increases
     - Latency shows actual processing time (should be under 2 seconds)
     - Chunks processed shows at least 1

### 2. Console Verification

Open browser developer console (F12) and check for:
- ✅ Green checkmarks showing successful initialization
- No red error messages about "ProfessionalRecorder already declared"
- No errors about "recording buttons not found"

### 3. API Test (Optional)

Run this command to test the backend directly:
```bash
curl -X POST http://localhost:5000/api/transcribe \
  -F "audio=@test_audio.wav" \
  -F "session_id=test_123"
```

You should get a JSON response with:
- `success: true`
- `transcript: "..."` (the transcribed text)
- `processing_time: X.XX` (in seconds)

## Known Issues to Check

1. **If transcription doesn't appear:**
   - Check browser console for errors
   - Verify microphone permissions are granted
   - Ensure OPENAI_API_KEY is set in environment

2. **If recording button doesn't work:**
   - Check console for "Recording buttons not found" error
   - Verify button turns red when clicked

3. **Current Limitations:**
   - Latency is ~1.9 seconds (target is <500ms)
   - Transcription happens after recording stops (not real-time streaming)
   - Requires OPENAI_API_KEY for actual transcription

## What's Working vs What's Not

### ✅ Working:
- Audio recording and capture
- Sending audio to backend
- Backend transcription with OpenAI Whisper
- Display of transcription results
- Basic stats tracking

### ⚠️ Needs Improvement:
- Latency optimization (currently 1.9s vs 500ms target)
- Real-time streaming (currently batch processing)
- WebSocket support for live updates

### ❌ Not Working Yet:
- Real-time streaming transcription
- WebSocket connections
- Sub-500ms latency target

Please test these steps and let me know what you observe!