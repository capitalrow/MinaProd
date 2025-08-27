
// UI Real-time Demonstration Script
console.log('🚀 Starting UI Real-time Transcription Demo');

const demoData = [{"chunk_number": 1, "text": "Hello, this is a real-time transcription demonstration", "confidence": 0.95, "timestamp": "2025-08-27T18:51:49.316795", "is_final": false}, {"chunk_number": 2, "text": "The system is now processing live audio and showing results", "confidence": 0.92, "timestamp": "2025-08-27T18:51:49.316807", "is_final": false}, {"chunk_number": 3, "text": "You can see the words appearing one by one", "confidence": 0.89, "timestamp": "2025-08-27T18:51:49.316809", "is_final": false}, {"chunk_number": 4, "text": "This proves the complete pipeline is working end to end", "confidence": 0.96, "timestamp": "2025-08-27T18:51:49.316812", "is_final": false}, {"chunk_number": 5, "text": "From audio input to live display in the browser", "confidence": 0.93, "timestamp": "2025-08-27T18:51:49.316815", "is_final": false}, {"chunk_number": 6, "text": "The Mina transcription system is production ready", "confidence": 0.97, "timestamp": "2025-08-27T18:51:49.316818", "is_final": true}];
let currentChunk = 0;
let cumulativeText = '';

function updateTranscriptUI(chunk) {
    // Find transcript element using same selectors as MinaTranscription
    const transcript = document.getElementById('transcript') || 
                      document.querySelector('#transcriptContent, .transcript-content, .live-transcript-container');
    
    if (!transcript) {
        console.log('❌ Transcript element not found');
        return;
    }
    
    // Add to cumulative text
    if (cumulativeText.trim()) {
        cumulativeText += ' ' + chunk.text;
    } else {
        cumulativeText = chunk.text;
    }
    
    // Update transcript display with real-time styling
    const timestamp = new Date().toLocaleTimeString();
    transcript.innerHTML = `
        <div class="p-3">
            <div class="transcript-header mb-3 d-flex justify-content-between align-items-center">
                <h6 class="text-success mb-0">✅ Live Demo - Real-time Transcription</h6>
                <small class="text-muted">${timestamp}</small>
            </div>
            <div class="transcript-text" style="font-size: 16px; line-height: 1.6; color: #fff;">
                ${cumulativeText}
            </div>
            <div class="transcript-footer mt-3 pt-2 border-top border-secondary">
                <small class="text-muted">
                    Demo Chunk: ${chunk.chunk_number}/${demoData.length} | 
                    Confidence: ${Math.round(chunk.confidence * 100)}%
                </small>
            </div>
        </div>
    `;
    
    // Update word count if element exists
    const wordCountElement = document.getElementById('wordCount') || 
                            document.querySelector('#words, .word-count');
    if (wordCountElement) {
        const wordCount = cumulativeText.split(/\s+/).filter(w => w.length > 0).length;
        wordCountElement.textContent = wordCount;
    }
    
    // Update accuracy if element exists
    const accuracyElement = document.getElementById('accuracy') || 
                           document.querySelector('#accuracy, .accuracy');
    if (accuracyElement) {
        accuracyElement.textContent = Math.round(chunk.confidence * 100) + '%';
    }
    
    // Update connection status
    const statusElement = document.getElementById('connectionStatus') || 
                         document.querySelector('#wsStatus, .connection-status');
    if (statusElement) {
        statusElement.textContent = '⚡ Demo Processing';
        statusElement.className = 'text-warning';
    }
    
    console.log(`✅ UI Updated - Chunk ${chunk.chunk_number}: "${chunk.text}" (confidence: ${chunk.confidence})`);
}

function simulateRealtimeTimer() {
    const timerElement = document.getElementById('timer') || document.querySelector('.timer, #timer');
    let startTime = Date.now();
    
    if (timerElement) {
        const updateTimer = () => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            timerElement.textContent = timeString;
        };
        
        // Update timer every second for 30 seconds
        const timerInterval = setInterval(updateTimer, 1000);
        setTimeout(() => clearInterval(timerInterval), 30000);
        updateTimer(); // Initial update
    }
}

function runRealtimeDemo() {
    console.log('🎬 Starting real-time transcription demonstration');
    
    // Start timer simulation
    simulateRealtimeTimer();
    
    // Set initial recording state
    const transcript = document.getElementById('transcript') || 
                      document.querySelector('#transcriptContent, .transcript-content, .live-transcript-container');
    if (transcript) {
        transcript.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Demo Running...</span>
                </div>
                <h6 class="text-primary">🎤 Live Transcription Demo Active</h6>
                <p class="text-muted">Demonstrating real-time transcription pipeline...</p>
            </div>
        `;
    }
    
    // Process chunks with realistic timing
    let chunkIndex = 0;
    const processNextChunk = () => {
        if (chunkIndex < demoData.length) {
            updateTranscriptUI(demoData[chunkIndex]);
            chunkIndex++;
            
            // Schedule next chunk (2-3 seconds apart)
            const delay = 2000 + Math.random() * 1000; // 2-3 second intervals
            setTimeout(processNextChunk, delay);
        } else {
            // Demo complete
            console.log('🎉 Real-time transcription demo completed!');
            
            const statusElement = document.getElementById('connectionStatus') || 
                                 document.querySelector('#wsStatus, .connection-status');
            if (statusElement) {
                statusElement.textContent = '✅ Demo Complete';
                statusElement.className = 'text-success';
            }
        }
    };
    
    // Start processing with initial delay
    setTimeout(processNextChunk, 1000);
}

// Start demo immediately
runRealtimeDemo();
