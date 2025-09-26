/**
 * Mobile Enhanced Optimizations for Live Transcription
 * Ensures optimal performance and UX on mobile devices.
 */

class MobileEnhancedOptimizations {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTouch = 'ontouchstart' in window;
        this.orientation = window.orientation || 0;
        
        // Mobile-specific settings
        this.mobileSettings = {
            reducedPollingFrequency: 200, // Slower polling on mobile to save battery
            optimizedChunkSize: 400, // Larger chunks on mobile for efficiency
            touchFeedbackEnabled: true,
            adaptiveQuality: true,
            batteryOptimization: true
        };
        
        this.initialized = false;
        this.init();
    }
    
    init() {
        if (this.initialized) return;
        
        console.log('📱 Initializing mobile optimizations...');
        console.log('📱 Device info:', {
            isMobile: this.isMobile,
            isTouch: this.isTouch,
            orientation: this.orientation,
            userAgent: navigator.userAgent
        });
        
        if (this.isMobile) {
            this.applyMobileOptimizations();
        }
        
        this.setupOrientationHandling();
        this.setupTouchOptimizations();
        this.setupMobileAudioOptimizations();
        this.setupBatteryOptimizations();
        
        this.initialized = true;
        console.log('✅ Mobile optimizations initialized');
    }
    
    detectMobile() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        
        // Enhanced mobile detection
        const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini|mobile/i;
        const isAndroid = /android/i.test(userAgent);
        const isiOS = /iphone|ipad|ipod/i.test(userAgent);
        const isWindowsMobile = /windows phone/i.test(userAgent);
        
        // Check screen size as secondary indicator
        const hasSmallScreen = window.screen.width <= 768 || window.screen.height <= 768;
        
        return mobileRegex.test(userAgent) || isAndroid || isiOS || isWindowsMobile || 
               (hasSmallScreen && this.isTouch);
    }
    
    applyMobileOptimizations() {
        console.log('📱 Applying mobile-specific optimizations...');
        
        // Optimize viewport for mobile transcription
        this.optimizeViewport();
        
        // Enhance touch interactions
        this.enhanceTouchInteractions();
        
        // Optimize layout for mobile
        this.optimizeMobileLayout();
        
        // Apply mobile-specific CSS
        this.applyMobileCSS();
        
        // Optimize WebSocket client for mobile
        this.optimizeWebSocketForMobile();
    }
    
    optimizeViewport() {
        // Ensure proper viewport scaling
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';
        
        // Prevent zoom on input focus
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.style.fontSize = Math.max(16, parseInt(getComputedStyle(input).fontSize)) + 'px';
        });
    }
    
    enhanceTouchInteractions() {
        // Add touch feedback to buttons
        const buttons = document.querySelectorAll('button, .btn');
        buttons.forEach(button => {
            this.addTouchFeedback(button);
        });
        
        // Optimize touch targets
        this.optimizeTouchTargets();
        
        // Add swipe gestures for transcript navigation
        this.addSwipeGestures();
    }
    
    addTouchFeedback(element) {
        if (!this.mobileSettings.touchFeedbackEnabled) return;
        
        element.addEventListener('touchstart', (e) => {
            element.style.transform = 'scale(0.95)';
            element.style.transition = 'transform 0.1s ease';
            
            // Haptic feedback if available
            if (navigator.vibrate) {
                navigator.vibrate(10);
            }
        });
        
        element.addEventListener('touchend', (e) => {
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 100);
        });
        
        element.addEventListener('touchcancel', (e) => {
            element.style.transform = 'scale(1)';
        });
    }
    
    optimizeTouchTargets() {
        // Ensure minimum touch target size (44px recommended)
        const touchTargets = document.querySelectorAll('button, .btn, .clickable, [onclick]');
        touchTargets.forEach(target => {
            const rect = target.getBoundingClientRect();
            if (rect.width < 44 || rect.height < 44) {
                target.style.minWidth = '44px';
                target.style.minHeight = '44px';
                target.style.display = 'inline-flex';
                target.style.alignItems = 'center';
                target.style.justifyContent = 'center';
            }
        });
    }
    
    addSwipeGestures() {
        const transcriptContainer = document.querySelector('.live-transcript-container');
        if (!transcriptContainer) return;
        
        let startY = 0;
        let startX = 0;
        let isScrolling = false;
        
        transcriptContainer.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            startX = e.touches[0].clientX;
            isScrolling = false;
        });
        
        transcriptContainer.addEventListener('touchmove', (e) => {
            if (!startY || !startX) return;
            
            const currentY = e.touches[0].clientY;
            const currentX = e.touches[0].clientX;
            const diffY = startY - currentY;
            const diffX = startX - currentX;
            
            // Detect horizontal swipe for clearing transcript
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
                if (!isScrolling && diffX > 0) {
                    // Swipe left to clear (with confirmation)
                    this.handleSwipeToClear();
                }
                isScrolling = true;
            }
        });
    }
    
    handleSwipeToClear() {
        if (window.enhancedWebSocketClient && typeof window.clearTranscript === 'function') {
            // Show confirmation toast
            this.showMobileToast('Swipe left again to clear transcript', 'warning');
            
            // Allow actual clear on next swipe within 3 seconds
            this.swipeToClearTimeout = setTimeout(() => {
                this.swipeToClearTimeout = null;
            }, 3000);
            
            if (this.swipeToClearTimeout) {
                clearTimeout(this.swipeToClearTimeout);
                window.clearTranscript();
                this.showMobileToast('Transcript cleared', 'success');
            }
        }
    }
    
    optimizeMobileLayout() {
        // Adjust container spacing for mobile
        const containers = document.querySelectorAll('.container, .container-fluid');
        containers.forEach(container => {
            if (this.isMobile) {
                container.style.paddingLeft = '10px';
                container.style.paddingRight = '10px';
            }
        });
        
        // Optimize transcript display height for mobile
        const transcriptDisplay = document.querySelector('.live-transcript-container');
        if (transcriptDisplay && this.isMobile) {
            const viewportHeight = window.innerHeight;
            const maxHeight = Math.min(400, viewportHeight * 0.4);
            transcriptDisplay.style.maxHeight = maxHeight + 'px';
            transcriptDisplay.style.overflowY = 'auto';
            transcriptDisplay.style.webkitOverflowScrolling = 'touch'; // Smooth scrolling on iOS
        }
        
        // Stack elements vertically on mobile
        this.stackElementsForMobile();
    }
    
    stackElementsForMobile() {
        if (!this.isMobile) return;
        
        // Convert row layouts to column layouts on mobile
        const rows = document.querySelectorAll('.row');
        rows.forEach(row => {
            const cols = row.querySelectorAll('.col-md-3, .col-md-4, .col-md-6');
            if (cols.length > 2) {
                cols.forEach(col => {
                    col.className = col.className.replace(/col-md-\d+/, 'col-12 mb-2');
                });
            }
        });
    }
    
    applyMobileCSS() {
        const mobileStyles = document.createElement('style');
        mobileStyles.id = 'mobile-optimizations';
        mobileStyles.textContent = `
            @media (max-width: 768px) {
                /* Mobile-optimized button sizes */
                .btn-lg {
                    padding: 0.75rem 1.5rem;
                    font-size: 1.1rem;
                    min-height: 44px;
                }
                
                /* Improve readability on mobile */
                .card-body {
                    padding: 1rem 0.75rem;
                }
                
                /* Optimize transcript display */
                .transcript-segment {
                    margin-bottom: 0.75rem !important;
                    padding: 0.75rem !important;
                    font-size: 1rem;
                    line-height: 1.4;
                }
                
                /* Improve touch targets */
                .badge {
                    padding: 0.375rem 0.75rem;
                    font-size: 0.875rem;
                }
                
                /* Stack session statistics */
                .session-stats .col-md-3 {
                    margin-bottom: 0.5rem;
                }
                
                /* Optimize status alerts */
                .alert {
                    padding: 0.75rem;
                    margin-bottom: 1rem;
                    font-size: 0.95rem;
                }
                
                /* Improve modal dialogs on mobile */
                .modal-dialog {
                    margin: 1rem;
                    max-width: calc(100vw - 2rem);
                }
                
                /* Prevent horizontal scroll */
                body {
                    overflow-x: hidden;
                }
                
                /* Optimize navbar for mobile */
                .navbar-brand {
                    font-size: 1.1rem;
                }
                
                /* Better spacing for mobile */
                .mb-3 {
                    margin-bottom: 1rem !important;
                }
                
                /* Optimize transcript footer */
                .transcript-footer .col-md-3 {
                    text-align: center;
                    margin-bottom: 0.25rem;
                }
            }
            
            @media (max-width: 480px) {
                /* Extra small mobile optimizations */
                .container {
                    padding-left: 8px;
                    padding-right: 8px;
                }
                
                .card {
                    margin-bottom: 0.75rem;
                }
                
                .btn {
                    width: 100%;
                    margin-bottom: 0.5rem;
                }
                
                .btn + .btn {
                    margin-left: 0;
                }
            }
            
            /* iOS specific optimizations */
            @supports (-webkit-touch-callout: none) {
                .live-transcript-container {
                    -webkit-overflow-scrolling: touch;
                }
                
                /* Prevent zoom on input focus */
                input, textarea, select {
                    font-size: 16px !important;
                }
            }
            
            /* Android specific optimizations */
            @media (max-width: 768px) and (-webkit-min-device-pixel-ratio: 1.5) {
                .transcript-text {
                    text-rendering: optimizeLegibility;
                    -webkit-font-smoothing: antialiased;
                }
            }
        `;
        
        document.head.appendChild(mobileStyles);
    }
    
    optimizeWebSocketForMobile() {
        // Wait for WebSocket client to be available
        const checkForClient = () => {
            if (window.enhancedWebSocketClient) {
                this.applyMobileWebSocketOptimizations(window.enhancedWebSocketClient);
            } else {
                setTimeout(checkForClient, 100);
            }
        };
        
        checkForClient();
    }
    
    applyMobileWebSocketOptimizations(client) {
        console.log('📱 Applying mobile WebSocket optimizations...');
        
        // Adjust polling frequency for mobile
        if (client.pollingFrequency && this.isMobile) {
            client.pollingFrequency = this.mobileSettings.reducedPollingFrequency;
            console.log(`📱 Adjusted polling frequency to ${client.pollingFrequency}ms for mobile`);
        }
        
        // Override chunk size for mobile efficiency
        const originalGetBestMimeType = client.getBestMimeType;
        if (originalGetBestMimeType) {
            client.getBestMimeType = () => {
                // Prefer more efficient codecs on mobile
                const mobileTypes = [
                    'audio/webm;codecs=opus',
                    'audio/ogg;codecs=opus',
                    'audio/mp4'
                ];
                
                for (const type of mobileTypes) {
                    if (MediaRecorder.isTypeSupported(type)) {
                        return type;
                    }
                }
                
                return originalGetBestMimeType.call(client);
            };
        }
        
        // Add mobile-specific error handling
        const originalHandleConnectionError = client.handleConnectionError;
        if (originalHandleConnectionError) {
            client.handleConnectionError = (error) => {
                // Show mobile-friendly error messages
                this.showMobileToast(`Connection failed: ${error.message}`, 'error');
                
                // Call original error handler
                originalHandleConnectionError.call(client, error);
            };
        }
    }
    
    setupOrientationHandling() {
        const handleOrientationChange = () => {
            const newOrientation = window.orientation || 0;
            
            console.log(`📱 Orientation changed: ${this.orientation} → ${newOrientation}`);
            this.orientation = newOrientation;
            
            // Adjust layout for new orientation
            setTimeout(() => {
                this.optimizeMobileLayout();
                
                // Trigger resize event for WebSocket client
                window.dispatchEvent(new Event('resize'));
            }, 100);
        };
        
        window.addEventListener('orientationchange', handleOrientationChange);
        window.addEventListener('resize', handleOrientationChange);
    }
    
    setupTouchOptimizations() {
        // Prevent accidental zooms
        document.addEventListener('touchstart', (e) => {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
        
        // Prevent double-tap zoom on buttons
        const buttons = document.querySelectorAll('button, .btn');
        buttons.forEach(button => {
            button.addEventListener('touchend', (e) => {
                e.preventDefault();
                button.click();
            });
        });
        
        // Add long-press support for additional actions
        this.setupLongPressGestures();
    }
    
    setupLongPressGestures() {
        const recordButton = document.querySelector('button[data-enhanced-listener="true"]') || 
                           document.querySelector('#recordButton');
        
        if (recordButton) {
            let longPressTimer = null;
            
            recordButton.addEventListener('touchstart', (e) => {
                longPressTimer = setTimeout(() => {
                    // Long press action: show recording options
                    this.showMobileRecordingOptions();
                }, 800);
            });
            
            recordButton.addEventListener('touchend', (e) => {
                if (longPressTimer) {
                    clearTimeout(longPressTimer);
                }
            });
            
            recordButton.addEventListener('touchcancel', (e) => {
                if (longPressTimer) {
                    clearTimeout(longPressTimer);
                }
            });
        }
    }
    
    setupMobileAudioOptimizations() {
        // Optimize audio constraints for mobile
        if (window.enhancedWebSocketClient) {
            const originalStartRecording = window.enhancedWebSocketClient.startRecording;
            if (originalStartRecording) {
                window.enhancedWebSocketClient.startRecording = async function() {
                    // Override audio constraints for mobile
                    const mobileAudioConstraints = {
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true,
                            sampleRate: 16000,
                            channelCount: 1,
                            // Mobile-specific optimizations
                            googEchoCancellation: true,
                            googAutoGainControl: true,
                            googNoiseSuppression: true,
                            googHighpassFilter: true,
                            googTypingNoiseDetection: true
                        }
                    };
                    
                    // Temporarily override getUserMedia constraints
                    const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
                    navigator.mediaDevices.getUserMedia = (constraints) => {
                        if (constraints.audio && typeof constraints.audio === 'object') {
                            constraints.audio = mobileAudioConstraints.audio;
                        }
                        return originalGetUserMedia.call(navigator.mediaDevices, constraints);
                    };
                    
                    try {
                        const result = await originalStartRecording.call(this);
                        return result;
                    } finally {
                        // Restore original getUserMedia
                        navigator.mediaDevices.getUserMedia = originalGetUserMedia;
                    }
                };
            }
        }
    }
    
    setupBatteryOptimizations() {
        if (!this.mobileSettings.batteryOptimization) return;
        
        // Monitor battery status if available
        if ('getBattery' in navigator) {
            navigator.getBattery().then((battery) => {
                console.log(`📱 Battery level: ${Math.round(battery.level * 100)}%`);
                
                battery.addEventListener('levelchange', () => {
                    const level = Math.round(battery.level * 100);
                    console.log(`📱 Battery level changed: ${level}%`);
                    
                    if (level < 20) {
                        this.enablePowerSavingMode();
                    } else if (level > 30) {
                        this.disablePowerSavingMode();
                    }
                });
            });
        }
        
        // Monitor page visibility for battery saving
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.enableBackgroundMode();
            } else {
                this.disableBackgroundMode();
            }
        });
    }
    
    enablePowerSavingMode() {
        console.log('📱 Enabling power saving mode...');
        
        // Reduce polling frequency
        if (window.enhancedWebSocketClient && window.enhancedWebSocketClient.pollingFrequency) {
            window.enhancedWebSocketClient.pollingFrequency = 500; // Slower polling
        }
        
        // Reduce visual updates
        this.powerSavingMode = true;
        
        this.showMobileToast('Power saving mode enabled', 'info');
    }
    
    disablePowerSavingMode() {
        console.log('📱 Disabling power saving mode...');
        
        // Restore normal polling frequency
        if (window.enhancedWebSocketClient && window.enhancedWebSocketClient.pollingFrequency) {
            window.enhancedWebSocketClient.pollingFrequency = this.mobileSettings.reducedPollingFrequency;
        }
        
        this.powerSavingMode = false;
    }
    
    enableBackgroundMode() {
        console.log('📱 Enabling background mode...');
        
        // Reduce update frequency when in background
        this.backgroundMode = true;
        
        // Keep recording active but reduce UI updates
        if (window.enhancedWebSocketClient && window.enhancedWebSocketClient.isRecording) {
            console.log('📱 Maintaining recording in background...');
        }
    }
    
    disableBackgroundMode() {
        console.log('📱 Disabling background mode...');
        
        this.backgroundMode = false;
        
        // Resume normal operation
        if (window.enhancedWebSocketClient) {
            console.log('📱 Resuming foreground operation...');
        }
    }
    
    showMobileRecordingOptions() {
        // Show mobile-specific recording options
        const options = [
            'Quality: Auto',
            'Language: English',
            'Noise Reduction: On',
            'Battery Optimization: On'
        ];
        
        this.showMobileToast('Recording Options:\n' + options.join('\n'), 'info', 3000);
    }
    
    showMobileToast(message, type = 'info', duration = 2000) {
        // Create mobile-friendly toast notification
        const existingToast = document.getElementById('mobile-toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.id = 'mobile-toast';
        toast.className = `alert alert-${this.getToastClass(type)} mobile-toast`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            min-width: 250px;
            max-width: 90vw;
            text-align: center;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideInDown 0.3s ease;
            white-space: pre-line;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Add CSS animation
        if (!document.getElementById('mobile-toast-styles')) {
            const styles = document.createElement('style');
            styles.id = 'mobile-toast-styles';
            styles.textContent = `
                @keyframes slideInDown {
                    from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
                @keyframes slideOutUp {
                    from { transform: translateX(-50%) translateY(0); opacity: 1; }
                    to { transform: translateX(-50%) translateY(-100%); opacity: 0; }
                }
            `;
            document.head.appendChild(styles);
        }
        
        // Auto-remove toast
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOutUp 0.3s ease';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }
        }, duration);
    }
    
    getToastClass(type) {
        switch (type) {
            case 'success': return 'success';
            case 'error': return 'danger';
            case 'warning': return 'warning';
            case 'info': return 'info';
            default: return 'secondary';
        }
    }
    
    // Public API
    getOptimizationStatus() {
        return {
            isMobile: this.isMobile,
            isTouch: this.isTouch,
            orientation: this.orientation,
            powerSavingMode: this.powerSavingMode || false,
            backgroundMode: this.backgroundMode || false,
            initialized: this.initialized
        };
    }
}

// Initialize mobile optimizations
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 Initializing mobile enhanced optimizations...');
    window.mobileOptimizations = new MobileEnhancedOptimizations();
    
    // Global access for debugging
    window.getMobileOptimizationStatus = () => window.mobileOptimizations.getOptimizationStatus();
});

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
