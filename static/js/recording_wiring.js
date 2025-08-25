/**
 * Fix Pack UX-R1: Start/Stop recording wiring
 * Simple implementation that follows the exact specification
 */

// Guard against double initialization
if (!window._minaHandlersBound) {
    let socket = null;
    let mediaRecorder = null;
    let audioStream = null;
    let CURRENT_SESSION_ID = null;

    // Initialize Socket.IO connection
    function initializeSocket() {
        socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true,
            timeout: 20000,  // FIXED: Increased timeout for better connection stability
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
            autoConnect: true,
            forceNew: false
        });
        
        // Connection status handlers
        socket.on('connect', () => {
            document.getElementById('wsStatus').textContent = 'Connected';
            console.log('Socket connected');
            // Enable recording button when connected
            const startBtn = document.getElementById('startRecordingBtn');
            if (startBtn) {
                startBtn.disabled = false;
            }
        });
        
        socket.on('disconnect', () => {
            document.getElementById('wsStatus').textContent = 'Disconnected';
            console.log('Socket disconnected');
            // Disable recording button when disconnected
            const startBtn = document.getElementById('startRecordingBtn');
            if (startBtn) {
                startBtn.disabled = true;
            }
        });
        
        socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            document.getElementById('wsStatus').textContent = 'Connection Error';
        });
        
        // Transcription result handlers - INT-LIVE-I1: Enhanced interim handling
        socket.on('interim_transcript', (payload) => {
            console.log('Interim transcript received:', payload);
            
            // Check if interim updates are enabled
            const showInterimToggle = document.getElementById('showInterim');
            if (showInterimToggle && !showInterimToggle.checked) {
                return; // Skip interim updates if disabled
            }
            
            const interimText = document.getElementById('interimText');
            if (interimText) {
                interimText.textContent = payload.text || '';
                interimText.style.display = payload.text ? 'block' : 'none';
                
                // Hide initial message when interim text appears
                const initialMessage = document.getElementById('initialMessage');
                if (initialMessage && payload.text) {
                    initialMessage.style.display = 'none';
                }
            }
        });
        
        socket.on('final_transcript', (payload) => {
            const finalDiv = document.getElementById('finalText');
            const interimDiv = document.getElementById('interimText');
            
            if (finalDiv && payload.text) {
                finalDiv.textContent = (finalDiv.textContent + ' ' + payload.text).trim();
                // Hide initial message if present
                const initialMessage = document.getElementById('initialMessage');
                if (initialMessage) {
                    initialMessage.style.display = 'none';
                }
            }
            
            if (interimDiv) {
                interimDiv.textContent = '';
                interimDiv.style.display = 'none';
            }
            
            // Update quality monitoring with enhanced data
            if (window.qualityMonitor && payload.confidence !== undefined) {
                window.qualityMonitor.handleQualityUpdate({
                    type: 'final_processed',
                    confidence: payload.confidence || 0,
                    text_quality: payload.quality_status || 'good',
                    timestamp: payload.timestamp
                });
            }
        });
        
        // Enhanced Quality Monitoring Event Handlers
        socket.on('quality_update', (data) => {
            console.log('Quality update received:', data);
            if (window.qualityMonitor) {
                window.qualityMonitor.handleQualityUpdate(data);
            }
        });
        
        // Session management
        socket.on('session_created', (data) => {
            CURRENT_SESSION_ID = data.session_id;
            console.log('Session created:', CURRENT_SESSION_ID);
            
            // INT-LIVE-I1: Explicitly join the WebSocket room
            socket.emit('join_session', { session_id: CURRENT_SESSION_ID });
            console.log('Explicitly joined session room:', CURRENT_SESSION_ID);
            
            // Update UI to show session is ready
            const sessionInfo = document.getElementById('sessionInfo');
            if (sessionInfo) {
                sessionInfo.textContent = `Session: ${CURRENT_SESSION_ID.substring(0, 8)}...`;
            }
        });
        
        // Audio processing confirmation
        socket.on('audio_received', (data) => {
            console.log('Audio processing confirmed:', data);
            updateAudioStats(data);
        });
        
        // Transcription result handlers - enhanced logging
        socket.on('transcription_segment', (data) => {
            console.log('Transcription segment received:', data);
            displayTranscriptionSegment(data);
        });
        
        // Error handling
        socket.on('error', (error) => {
            console.error('Socket error:', error);
            showError('Transcription error: ' + error.message);
        });
    }

    function startRecording() {
        console.log('Starting recording...');
        
        // Check WebSocket connection with retry
        if (!socket || !socket.connected) {
            console.log('Socket not connected, attempting to reconnect...');
            document.getElementById('wsStatus').textContent = 'Connecting...';
            
            // Try to reconnect
            if (socket) {
                socket.connect();
            } else {
                initializeSocket();
            }
            
            // Wait a moment and try again
            setTimeout(() => {
                if (!socket || !socket.connected) {
                    document.getElementById('wsStatus').textContent = 'Not connected';
                    showError('WebSocket connection failed. Please check your internet connection and try again.');
                    return;
                } else {
                    // Connection succeeded, proceed with recording
                    proceedWithRecording();
                }
            }, 2000);
            return;
        }
        
        proceedWithRecording();
    }
    
    function proceedWithRecording() {
        // Request microphone access
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                audioStream = stream;
                
                // Create session if needed
                if (!CURRENT_SESSION_ID) {
                    socket.emit('create_session', {
                        title: 'Live Recording Session',
                        language: 'en'
                    });
                }

                // Determine supported MIME type
                let mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/webm;codecs=opus';
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = ''; // Use default
                    }
                }

                // Create MediaRecorder
                const options = mimeType ? { mimeType } : {};
                mediaRecorder = new MediaRecorder(stream, options);
                
                mediaRecorder.addEventListener('dataavailable', event => {
                    console.log('MediaRecorder data available:', {
                        size: event.data.size,
                        type: event.data.type,
                        sessionId: CURRENT_SESSION_ID,
                        socketConnected: socket?.connected
                    });
                    
                    if (event.data.size > 0 && CURRENT_SESSION_ID) {
                        // Convert blob to ArrayBuffer and then to base64
                        event.data.arrayBuffer().then(arrayBuffer => {
                            console.log('Audio ArrayBuffer size:', arrayBuffer.byteLength);
                            
                            // Split large chunks to avoid transmission issues
                            const MAX_CHUNK_SIZE = 32768; // 32KB chunks
                            const uint8Array = new Uint8Array(arrayBuffer);
                            
                            if (uint8Array.length > MAX_CHUNK_SIZE) {
                                // Split into smaller chunks
                                for (let i = 0; i < uint8Array.length; i += MAX_CHUNK_SIZE) {
                                    const chunk = uint8Array.slice(i, i + MAX_CHUNK_SIZE);
                                    const chunkBase64 = btoa(String.fromCharCode.apply(null, chunk));
                                    
                                    console.log(`Sending audio chunk ${i / MAX_CHUNK_SIZE + 1}, size: ${chunk.length}`);
                                    socket.emit('audio_chunk', {
                                        session_id: CURRENT_SESSION_ID,
                                        audio_data: chunkBase64,
                                        timestamp: Date.now(),
                                        chunk_index: i / MAX_CHUNK_SIZE,
                                        is_final_chunk: i + MAX_CHUNK_SIZE >= uint8Array.length
                                    });
                                }
                            } else {
                                // Send as single chunk
                                const base64 = btoa(String.fromCharCode.apply(null, uint8Array));
                                console.log('Sending single audio chunk, size:', uint8Array.length);
                                
                                socket.emit('audio_chunk', {
                                    session_id: CURRENT_SESSION_ID,
                                    audio_data: base64,
                                    timestamp: Date.now(),
                                    chunk_index: 0,
                                    is_final_chunk: true
                                });
                            }
                        }).catch(error => {
                            console.error('Error processing audio data:', error);
                        });
                    } else {
                        console.warn('Skipping audio chunk:', {
                            dataSize: event.data.size,
                            hasSessionId: !!CURRENT_SESSION_ID
                        });
                    }
                });

                mediaRecorder.addEventListener('error', event => {
                    console.error('MediaRecorder error:', event.error);
                    showError('Recording error: ' + event.error.message);
                });

                // Start recording with 1 second chunks
                mediaRecorder.start(1000);
                
                // Update UI
                document.getElementById('startRecordingBtn').disabled = true;
                document.getElementById('stopRecordingBtn').disabled = false;
                document.getElementById('micStatus').textContent = 'Recording...';
                
                console.log('Recording started');
            })
            .catch(err => {
                console.error('Microphone access denied:', err);
                if (err.name === 'NotAllowedError') {
                    showError('Microphone access denied. Enable mic to use live transcription.');
                } else {
                    showError('Error accessing microphone: ' + err.message);
                }
            });
    }

    function stopRecording() {
        console.log('Stopping recording...');
        
        // Stop MediaRecorder
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        
        // Stop audio stream
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
            audioStream = null;
        }
        
        // Emit end of stream
        if (socket && CURRENT_SESSION_ID) {
            socket.emit('end_of_stream', { session_id: CURRENT_SESSION_ID });
        }
        
        // Update UI
        document.getElementById('startRecordingBtn').disabled = false;
        document.getElementById('stopRecordingBtn').disabled = true;
        document.getElementById('micStatus').textContent = 'Stopped';
        
        console.log('Recording stopped');
    }

    function refreshStatuses() {
        // Update connection status
        if (socket && socket.connected) {
            document.getElementById('wsStatus').textContent = 'Connected';
        } else {
            document.getElementById('wsStatus').textContent = 'Disconnected';
        }
        
        // Update mic status
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            document.getElementById('micStatus').textContent = 'Recording...';
        } else {
            document.getElementById('micStatus').textContent = 'Not connected';
        }
    }

    function showError(message) {
        // Simple error display - could be enhanced with toast notifications
        console.error('Recording error:', message);
        alert(message); // Replace with better UI later
    }
    
    // Helper functions for enhanced UI feedback
    function updateAudioStats(data) {
        const inputLevel = document.getElementById('inputLevel');
        const vadStatus = document.getElementById('vadStatus');
        
        if (inputLevel && data.input_level !== undefined) {
            inputLevel.textContent = `Input Level: ${Math.round(data.input_level * 100)}%`;
        }
        
        if (vadStatus && data.vad_status) {
            vadStatus.textContent = `VAD: ${data.vad_status}`;
        }
    }
    
    function displayTranscriptionSegment(data) {
        const finalDiv = document.getElementById('finalText');
        const interimDiv = document.getElementById('interimText');
        const initialMessage = document.getElementById('initialMessage');
        
        if (data.is_final && finalDiv) {
            // Add final transcription text
            const currentText = finalDiv.textContent || '';
            finalDiv.textContent = (currentText + ' ' + data.text).trim();
            
            // Hide initial message
            if (initialMessage) {
                initialMessage.style.display = 'none';
            }
            
            // Clear interim text
            if (interimDiv) {
                interimDiv.textContent = '';
                interimDiv.style.display = 'none';
            }
        } else if (!data.is_final && interimDiv) {
            // Show interim transcription
            interimDiv.textContent = data.text || '';
            interimDiv.style.display = data.text ? 'block' : 'none';
        }
        
        // Update segment counter
        const segmentCounter = document.querySelector('[data-segment-count]');
        if (segmentCounter && data.segment_count !== undefined) {
            segmentCounter.textContent = `Segments: ${data.segment_count}`;
        }
    }

    // DOM ready handler
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, setting up recording controls...');
        
        // Get button elements
        const startBtn = document.getElementById('startRecordingBtn');
        const stopBtn = document.getElementById('stopRecordingBtn');
        
        if (!startBtn || !stopBtn) {
            console.error('Required buttons not found:', { startBtn: !!startBtn, stopBtn: !!stopBtn });
            return;
        }
        
        // Disable start button until WebSocket connects
        startBtn.disabled = true;
        stopBtn.disabled = true;
        
        // Bind event listeners
        startBtn.addEventListener('click', startRecording);
        stopBtn.addEventListener('click', stopRecording);
        
        // Initialize Socket.IO
        initializeSocket();
        
        // Update initial status
        refreshStatuses();
        
        console.log('Recording controls initialized');
    });

    // Mark handlers as bound
    window._minaHandlersBound = true;
    console.log('Recording wiring initialized');
}