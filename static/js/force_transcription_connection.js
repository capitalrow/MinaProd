// EMERGENCY CONNECTION SCRIPT - Force Real Whisper Integration
(function() {
    console.log('🚨 EMERGENCY: Forcing Real Whisper Integration connection');
    
    // Wait for the system to be ready
    setTimeout(() => {
        if (window.realWhisperIntegration) {
            console.log('🎯 Found Real Whisper Integration - forcing connection');
            
            // Force start transcription with current session
            const currentSession = `session_${Date.now()}_emergency`;
            
            window.realWhisperIntegration.startTranscription(currentSession)
                .then(() => {
                    console.log('✅ Emergency connection successful!');
                    
                    // Update transcript area immediately
                    const transcriptContainer = document.querySelector('.live-transcript-container') ||
                                              document.getElementById('transcript') || 
                                              document.getElementById('transcriptContent') ||
                                              document.querySelector('.transcript-content');
                                              
                    if (transcriptContainer) {
                        transcriptContainer.innerHTML = `
                            <div class="alert alert-success">
                                <h6>🎤 Transcription Now Active!</h6>
                                <p class="mb-0">Keep speaking - your words will appear here.</p>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    console.error('❌ Emergency connection failed:', error);
                });
        } else {
            console.log('⚠️ Real Whisper Integration not found - retrying...');
            setTimeout(arguments.callee, 1000);
        }
    }, 500);
})();

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
