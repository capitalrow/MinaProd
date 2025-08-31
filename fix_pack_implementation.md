# 🎯 MINA Live Transcription - Fix Pack Implementation Plan

## 📊 Current State Analysis

### Critical Issue Found
**Recording fails immediately** - MediaRecorder not initializing properly
- **Root Cause**: `professional_recorder.js` was missing
- **Impact**: 0% success rate, no audio chunks captured
- **Status**: File now created with proper error handling

### Screenshot Analysis (19:18:27)
- **UI State**: Recording button active (red) but failing
- **Error**: "Recording failed - try again"
- **Statistics**: All zeros (duration, words, accuracy, chunks)
- **System Health**: Shows "Ready" but not actually working

### Console Errors
1. ✅ **FIXED**: JavaScript error - duplicate 'style' declaration
2. 🔧 **IN PROGRESS**: Recording operation fails on button click

## 📦 Fix Pack 1: Critical Recording Fix (P0 - IMMEDIATE)

### Task 1.1: Professional Recorder Implementation ✅
**Status**: COMPLETED
- Created `static/js/professional_recorder.js`
- Implemented MediaRecorder with error handling
- Added microphone permission request flow
- Specific error messages for different failure modes

### Task 1.2: Wire Record Button to Professional Recorder 🔧
**Status**: IN PROGRESS
- Need to update button event handler in `live.html`
- Connect to `professionalRecorder` instance
- Handle permission flow properly

### Task 1.3: Test Audio Capture
**Status**: PENDING
- Verify MediaRecorder initializes
- Confirm chunks are generated
- Check audio upload to backend

### Acceptance Criteria
- ✅ Recording starts without errors
- ✅ Clear permission dialog appears
- ✅ Specific error messages for failures
- ✅ Audio chunks sent to backend

## 📦 Fix Pack 2: Pipeline Optimization (P1 - HIGH)

### Task 2.1: Reduce Chunk Size
```javascript
// Change from 1000ms to 500ms chunks
this.config = {
    chunkDuration: 500, // Reduced for lower latency
    sampleRate: 16000,
    channelCount: 1
};
```

### Task 2.2: Implement Streaming
- Use streaming responses from OpenAI
- Display partial results immediately
- Update UI progressively

### Task 2.3: Add Chunk Queuing
```python
from queue import Queue
import threading

class ChunkQueue:
    def __init__(self):
        self.queue = Queue()
        self.worker = threading.Thread(target=self.process_queue)
        self.worker.start()
    
    def add_chunk(self, chunk):
        self.queue.put(chunk)
    
    def process_queue(self):
        while True:
            chunk = self.queue.get()
            # Process chunk
            self.queue.task_done()
```

### Acceptance Criteria
- ✅ Latency < 500ms per chunk
- ✅ No dropped chunks under load
- ✅ Smooth UI updates

## 📦 Fix Pack 3: QA Pipeline (P2 - MEDIUM)

### Task 3.1: WER Calculation
```python
import jiwer

def calculate_wer(reference, hypothesis):
    '''Calculate Word Error Rate'''
    wer = jiwer.wer(reference, hypothesis)
    return wer * 100  # Convert to percentage

# Target: WER ≤ 10%
```

### Task 3.2: Drift Detection
```python
def detect_drift(segments):
    '''Detect semantic drift in transcription'''
    from sklearn.metrics.pairwise import cosine_similarity
    
    drift_scores = []
    for i in range(1, len(segments)):
        similarity = cosine_similarity(
            vectorize(segments[i-1]), 
            vectorize(segments[i])
        )
        drift_scores.append(1 - similarity)
    
    return np.mean(drift_scores)

# Target: Drift < 5%
```

### Task 3.3: Test Corpus Creation
```python
test_corpus = [
    {
        "audio": "test_1.wav",
        "reference": "Hello, this is a test recording",
        "expected_wer": 0.0
    },
    {
        "audio": "test_2.wav",
        "reference": "The quick brown fox jumps over the lazy dog",
        "expected_wer": 0.05
    }
]
```

### Acceptance Criteria
- ✅ WER ≤ 10% on test corpus
- ✅ Drift < 5% over 5 minutes
- ✅ Automated test suite

## 📦 Fix Pack 4: Robustness & Monitoring (P2 - MEDIUM)

### Task 4.1: Structured Logging
```python
import json
import uuid
import logging
from datetime import datetime

class StructuredLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def log_request(self, session_id, event, metrics):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4()),
            "session_id": session_id,
            "event": event,
            "metrics": metrics
        }
        self.logger.info(json.dumps(log_entry))
```

### Task 4.2: Connection Management
```javascript
class ConnectionManager {
    constructor() {
        this.activeConnection = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        if (this.activeConnection?.readyState === 'open') {
            return this.activeConnection;
        }
        
        // Close existing connection
        this.disconnect();
        
        // Create new connection with retry logic
        this.activeConnection = this.createConnection();
        return this.activeConnection;
    }
    
    createConnection() {
        const ws = new WebSocket(this.wsUrl);
        
        ws.onerror = () => this.handleError();
        ws.onclose = () => this.handleClose();
        
        return ws;
    }
    
    handleClose() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                this.connect();
            }, Math.pow(2, this.reconnectAttempts) * 1000);
        }
    }
}
```

### Acceptance Criteria
- ✅ Structured JSON logs with request_id
- ✅ Zero duplicate connections
- ✅ Automatic reconnection with backoff
- ✅ Full observability dashboard

## 📊 Testing Strategy

### Unit Tests
```python
import pytest
from services.transcription_service import TranscriptionService

def test_chunk_processing():
    service = TranscriptionService()
    chunk = create_test_chunk()
    result = service.process_chunk(chunk)
    assert result.latency < 0.5
    assert result.transcript is not None

def test_retry_logic():
    service = TranscriptionService()
    # Simulate API failure
    with mock.patch('openai.Audio.transcribe', side_effect=RateLimitError):
        result = service.transcribe_with_retry(audio)
        assert result.retry_count == 3
```

### E2E Tests with Playwright
```javascript
test('recording flow', async ({ page }) => {
    await page.goto('/live');
    
    // Grant mic permission
    await context.grantPermissions(['microphone']);
    
    // Start recording
    await page.click('.record-btn');
    await expect(page.locator('.status-text')).toHaveText('Recording...');
    
    // Wait for transcription
    await page.waitForSelector('.transcript-segment', { timeout: 5000 });
    
    // Stop recording
    await page.click('.record-btn.recording');
    await expect(page.locator('.status-text')).toHaveText('Stopped');
});
```

## ✅ Acceptance Checklist

### Backend
- [ ] Latency < 500ms per chunk
- [ ] Queue length < 10 chunks
- [ ] Zero dropped chunks
- [ ] Retry logic working
- [ ] Structured JSON logs
- [ ] Memory < 500MB
- [ ] CPU < 50%

### Frontend
- [ ] Recording starts without errors
- [ ] Mic permission dialog clear
- [ ] Interim updates < 2s
- [ ] One final transcript on stop
- [ ] Specific error messages
- [ ] Works on iOS Safari
- [ ] Works on Android Chrome
- [ ] Keyboard navigation
- [ ] ARIA labels present

### QA Metrics
- [ ] WER ≤ 10%
- [ ] Drift < 5%
- [ ] No duplicate phrases
- [ ] Hallucination rate < 1%
- [ ] 100% audio coverage

## 🚀 Implementation Timeline

1. **Hour 1**: Fix MediaRecorder (Critical)
2. **Hour 2**: Pipeline optimization
3. **Hour 3**: QA implementation
4. **Hour 4**: Robustness & monitoring
5. **Hour 5**: Testing & validation

## 📝 Next Immediate Actions

1. ✅ Fix JavaScript syntax error
2. ✅ Create professional_recorder.js
3. 🔧 Wire record button to professional recorder
4. ⏳ Test on actual device
5. ⏳ Implement specific error messages
6. ⏳ Verify chunk generation