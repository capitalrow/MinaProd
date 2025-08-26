#!/usr/bin/env python3
"""
🔧 MOBILE AUDIO RECORDING FIX
Specifically addresses mobile recording failures seen in screenshots
"""

import logging

logger = logging.getLogger(__name__)

class MobileAudioOptimizer:
    """Optimizes audio recording for mobile devices"""
    
    @staticmethod
    def get_mobile_audio_constraints():
        """Get optimized WebRTC constraints for mobile devices"""
        return {
            'audio': {
                'mandatory': {
                    'googEchoCancellation': False,
                    'googAutoGainControl': False,
                    'googNoiseSuppression': False,
                    'googHighpassFilter': False
                },
                'optional': [
                    {'googEchoCancellation2': False},
                    {'googAutoGainControl2': False}
                ]
            }
        }
    
    @staticmethod
    def get_mobile_optimized_settings():
        """Get settings optimized for mobile recording"""
        return {
            'sampleRate': 16000,  # Lower sample rate for mobile
            'channelCount': 1,    # Mono for mobile
            'echoCancellation': False,
            'autoGainControl': False,
            'noiseSuppression': False,
            'latency': 'interactive'  # Low latency for real-time
        }

# JavaScript code to be injected for mobile optimization
MOBILE_AUDIO_JS_FIX = """
// 🔧 MOBILE AUDIO RECORDING OPTIMIZATION
function initializeMobileAudioRecording() {
    // Detect mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        console.log('📱 Mobile device detected - applying optimizations');
        
        // Mobile-optimized constraints
        const mobileConstraints = {
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: false,
                autoGainControl: false,
                noiseSuppression: false,
                latency: 'interactive'
            }
        };
        
        // Override default constraints
        window.AUDIO_CONSTRAINTS = mobileConstraints;
        
        // Add mobile-specific error handling
        window.handleMobileAudioError = function(error) {
            console.error('🚨 Mobile audio error:', error);
            
            if (error.name === 'NotAllowedError') {
                showMobilePermissionGuide();
            } else if (error.name === 'NotFoundError') {
                showMobileDeviceGuide();
            } else if (error.name === 'NotReadableError') {
                showMobileDeviceBusyGuide();
            }
        };
        
        // Mobile permission guidance
        function showMobilePermissionGuide() {
            const guide = `
                📱 Microphone Permission Required
                
                To enable recording:
                1. Tap the address bar
                2. Look for microphone icon 🎤
                3. Select 'Allow'
                4. Refresh the page
                
                For Chrome: Settings > Site Settings > Microphone
                For Safari: Settings > Safari > Camera & Microphone
            `;
            
            showUserFriendlyError('Microphone Permission', guide, 'permission_denied');
        }
        
        function showMobileDeviceGuide() {
            showUserFriendlyError(
                'Microphone Not Found', 
                'No microphone detected. Please check your device settings and try again.',
                'device_not_found'
            );
        }
        
        function showMobileDeviceBusyGuide() {
            showUserFriendlyError(
                'Microphone In Use', 
                'Microphone is being used by another app. Please close other apps and try again.',
                'device_busy'
            );
        }
    }
    
    return isMobile;
}

// Enhanced error display for mobile
function showUserFriendlyError(title, message, errorType) {
    // Create mobile-friendly error modal
    const errorModal = document.createElement('div');
    errorModal.className = 'mobile-error-modal';
    errorModal.innerHTML = `
        <div class="error-content">
            <h3>${title}</h3>
            <p>${message}</p>
            <div class="error-actions">
                <button onclick="retryRecording()" class="btn btn-primary">Try Again</button>
                <button onclick="closeMobileError()" class="btn btn-secondary">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(errorModal);
    
    // Log for debugging
    console.log(`🚨 Mobile Error [${errorType}]: ${title} - ${message}`);
}

function retryRecording() {
    closeMobileError();
    // Trigger recording retry with mobile constraints
    if (window.startRecording) {
        window.startRecording();
    }
}

function closeMobileError() {
    const modal = document.querySelector('.mobile-error-modal');
    if (modal) {
        modal.remove();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeMobileAudioRecording);
"""

def generate_mobile_css_fixes():
    """Generate CSS fixes for mobile UI issues"""
    return """
/* 📱 MOBILE AUDIO RECORDING FIXES */
.mobile-error-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 20px;
}

.error-content {
    background: var(--bs-dark);
    border: 1px solid var(--bs-gray-600);
    border-radius: 8px;
    padding: 24px;
    max-width: 400px;
    width: 100%;
    text-align: center;
}

.error-content h3 {
    color: var(--bs-danger);
    margin-bottom: 16px;
    font-size: 1.2rem;
}

.error-content p {
    color: var(--bs-light);
    margin-bottom: 20px;
    line-height: 1.5;
    white-space: pre-line;
}

.error-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
}

.error-actions .btn {
    flex: 1;
    max-width: 120px;
}

/* Mobile-specific recording status */
@media (max-width: 768px) {
    .recording-status {
        font-size: 0.9rem;
        padding: 8px 12px;
    }
    
    .audio-controls .btn {
        font-size: 0.85rem;
        padding: 8px 16px;
    }
    
    .transcription-display {
        min-height: 200px;
        font-size: 0.9rem;
    }
    
    .session-metrics {
        font-size: 0.8rem;
    }
}

/* Better mobile touch targets */
@media (max-width: 480px) {
    .btn {
        min-height: 44px; /* iOS recommended touch target */
        font-size: 16px; /* Prevents zoom on iOS */
    }
    
    .form-control {
        font-size: 16px; /* Prevents zoom on iOS */
        min-height: 44px;
    }
}
"""

if __name__ == "__main__":
    print("🔧 Mobile Audio Recording Fix Generator")
    print("=" * 50)
    print("JavaScript fixes:")
    print(MOBILE_AUDIO_JS_FIX)
    print("\nCSS fixes:")
    print(generate_mobile_css_fixes())