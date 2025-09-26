/**
 * 🎆 REVOLUTIONARY MOBILE OPTIMIZATION ENGINE
 * Breakthrough mobile performance with adaptive processing
 */

class MobileOptimizationEngine {
    constructor() {
        this.deviceMetrics = this.analyzeDevice();
        this.networkOptimizer = new NetworkOptimizer();
        this.batteryManager = new BatteryOptimizer();
        this.touchOptimizer = new TouchOptimizer();
        this.performanceMonitor = new PerformanceMonitor();
        
        this.initializeMobileOptimizations();
        console.log('🎆 Revolutionary Mobile Engine initialized');
    }
    
    analyzeDevice() {
        const metrics = {
            userAgent: navigator.userAgent,
            isMobile: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
            isAndroid: /Android/i.test(navigator.userAgent),
            isiOS: /iPhone|iPad|iPod/i.test(navigator.userAgent),
            screenSize: {
                width: window.screen.width,
                height: window.screen.height,
                pixelRatio: window.devicePixelRatio || 1
            },
            memory: navigator.deviceMemory || 4,
            cores: navigator.hardwareConcurrency || 2,
            connection: this.getConnectionInfo()
        };
        
        metrics.performanceClass = this.classifyDevicePerformance(metrics);
        return metrics;
    }
    
    getConnectionInfo() {
        if (!navigator.connection) {
            return { effectiveType: '4g', downlink: 10, rtt: 100 };
        }
        
        return {
            effectiveType: navigator.connection.effectiveType,
            downlink: navigator.connection.downlink,
            rtt: navigator.connection.rtt,
            saveData: navigator.connection.saveData
        };
    }
    
    classifyDevicePerformance(metrics) {
        let score = 0;
        
        // CPU cores
        if (metrics.cores >= 8) score += 3;
        else if (metrics.cores >= 4) score += 2;
        else score += 1;
        
        // Memory
        if (metrics.memory >= 8) score += 3;
        else if (metrics.memory >= 4) score += 2;
        else score += 1;
        
        // Screen quality (high resolution = more powerful device)
        const totalPixels = metrics.screenSize.width * metrics.screenSize.height * metrics.screenSize.pixelRatio;
        if (totalPixels > 2000000) score += 2;
        else if (totalPixels > 1000000) score += 1;
        
        // Connection quality
        const connection = metrics.connection;
        if (connection.effectiveType === '4g' && connection.downlink > 5) score += 2;
        else if (connection.effectiveType === '4g') score += 1;
        
        if (score >= 8) return 'high-end';
        if (score >= 5) return 'mid-range';
        return 'entry-level';
    }
    
    initializeMobileOptimizations() {
        if (this.deviceMetrics.isMobile) {
            this.optimizeForMobile();
        }
        
        // Prevent zoom on double tap
        this.preventZoom();
        
        // Optimize touch interactions
        this.touchOptimizer.initialize();
        
        // Monitor performance
        this.performanceMonitor.startMonitoring();
    }
    
    optimizeForMobile() {
        // Viewport optimizations
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover');
        }
        
        // Add mobile-specific CSS classes
        document.body.classList.add('mobile-optimized');
        document.body.classList.add(`performance-${this.deviceMetrics.performanceClass}`);
        
        // Optimize audio context for mobile
        this.optimizeAudioContextForMobile();
    }
    
    optimizeAudioContextForMobile() {
        // Mobile-specific audio optimizations
        const originalAudioContext = window.AudioContext || window.webkitAudioContext;
        if (!originalAudioContext) return;
        
        // Override with mobile-optimized settings
        window.OptimizedAudioContext = class extends originalAudioContext {
            constructor(options = {}) {
                const mobileOptions = {
                    ...options,
                    sampleRate: 44100, // Standard for mobile
                    latencyHint: 'interactive' // Prioritize low latency
                };
                
                super(mobileOptions);
                this.optimized = true;
            }
        };
        
        console.log('🎆 Mobile audio context optimized');
    }
    
    preventZoom() {
        // Prevent zoom on double tap while allowing pinch zoom
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (event) => {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, {passive: false});
    }
    
    getOptimizedSettings() {
        const settings = {
            chunkSize: 4000,
            processingThreads: 1,
            cacheSize: 10,
            retryAttempts: 3
        };
        
        switch (this.deviceMetrics.performanceClass) {
            case 'high-end':
                settings.chunkSize = 6000;
                settings.processingThreads = 2;
                settings.cacheSize = 20;
                break;
            case 'mid-range':
                settings.chunkSize = 4000;
                settings.processingThreads = 1;
                settings.cacheSize = 15;
                break;
            case 'entry-level':
                settings.chunkSize = 3000;
                settings.processingThreads = 1;
                settings.cacheSize = 5;
                settings.retryAttempts = 2;
                break;
        }
        
        // Network optimizations
        if (this.deviceMetrics.connection.saveData) {
            settings.chunkSize = Math.max(2000, settings.chunkSize - 1000);
            settings.cacheSize = Math.max(3, Math.floor(settings.cacheSize / 2));
        }
        
        return settings;
    }
}

class NetworkOptimizer {
    constructor() {
        this.connectionMonitor = this.createConnectionMonitor();
        this.adaptiveSettings = {
            lowBandwidth: false,
            saveDataMode: false,
            connectionQuality: 'good'
        };
    }
    
    createConnectionMonitor() {
        if (!navigator.connection) return null;
        
        const monitor = {
            connection: navigator.connection,
            callbacks: []
        };
        
        navigator.connection.addEventListener('change', () => {
            this.updateConnectionStatus();
            monitor.callbacks.forEach(callback => callback(this.adaptiveSettings));
        });
        
        return monitor;
    }
    
    updateConnectionStatus() {
        if (!navigator.connection) return;
        
        const connection = navigator.connection;
        
        this.adaptiveSettings.saveDataMode = connection.saveData || false;
        this.adaptiveSettings.lowBandwidth = connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g';
        
        if (connection.downlink < 1.5) {
            this.adaptiveSettings.connectionQuality = 'poor';
        } else if (connection.downlink < 5) {
            this.adaptiveSettings.connectionQuality = 'fair';
        } else {
            this.adaptiveSettings.connectionQuality = 'good';
        }
        
        console.log('🎆 Network status updated:', this.adaptiveSettings);
    }
    
    getOptimizedRequest(originalOptions) {
        const optimized = { ...originalOptions };
        
        if (this.adaptiveSettings.lowBandwidth) {
            optimized.timeout = (optimized.timeout || 30000) * 1.5;
            optimized.retries = Math.max(1, (optimized.retries || 3) - 1);
        }
        
        if (this.adaptiveSettings.saveDataMode) {
            optimized.compression = 'high';
            optimized.quality = 'compressed';
        }
        
        return optimized;
    }
}

class BatteryOptimizer {
    constructor() {
        this.batteryInfo = null;
        this.optimizationLevel = 'normal';
        
        this.initializeBatteryOptimization();
    }
    
    async initializeBatteryOptimization() {
        try {
            if ('getBattery' in navigator) {
                this.batteryInfo = await navigator.getBattery();
                this.setupBatteryMonitoring();
            }
        } catch (error) {
            console.log('🎆 Battery API not available, using default optimizations');
        }
    }
    
    setupBatteryMonitoring() {
        if (!this.batteryInfo) return;
        
        const updateOptimization = () => {
            const battery = this.batteryInfo;
            
            if (battery.level < 0.2 && !battery.charging) {
                this.optimizationLevel = 'aggressive';
            } else if (battery.level < 0.5 && !battery.charging) {
                this.optimizationLevel = 'moderate';
            } else {
                this.optimizationLevel = 'normal';
            }
            
            console.log(`🎆 Battery optimization level: ${this.optimizationLevel}`);
        };
        
        this.batteryInfo.addEventListener('levelchange', updateOptimization);
        this.batteryInfo.addEventListener('chargingchange', updateOptimization);
        
        updateOptimization();
    }
    
    getOptimizedSettings() {
        const settings = {
            processingInterval: 4000,
            backgroundProcessing: true,
            screenWakeLock: true
        };
        
        switch (this.optimizationLevel) {
            case 'aggressive':
                settings.processingInterval = 6000;
                settings.backgroundProcessing = false;
                settings.screenWakeLock = false;
                break;
            case 'moderate':
                settings.processingInterval = 5000;
                settings.backgroundProcessing = true;
                settings.screenWakeLock = false;
                break;
        }
        
        return settings;
    }
}

class TouchOptimizer {
    constructor() {
        this.touchAreas = [];
        this.gestureRecognizer = new GestureRecognizer();
    }
    
    initialize() {
        this.optimizeTouchTargets();
        this.setupGestureHandling();
        this.addTouchFeedback();
    }
    
    optimizeTouchTargets() {
        // Ensure minimum touch target size (44px iOS, 48dp Android)
        const minSize = 44;
        
        const buttons = document.querySelectorAll('button, .btn, [role="button"]');
        buttons.forEach(button => {
            const rect = button.getBoundingClientRect();
            
            if (rect.width < minSize || rect.height < minSize) {
                button.style.minWidth = `${minSize}px`;
                button.style.minHeight = `${minSize}px`;
                button.classList.add('touch-optimized');
            }
        });
    }
    
    setupGestureHandling() {
        let touchStartY = 0;
        let touchStartX = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
            touchStartX = e.touches[0].clientX;
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            if (!e.changedTouches[0]) return;
            
            const touchEndY = e.changedTouches[0].clientY;
            const touchEndX = e.changedTouches[0].clientX;
            
            const deltaY = touchStartY - touchEndY;
            const deltaX = touchStartX - touchEndX;
            
            // Detect swipe gestures
            if (Math.abs(deltaY) > 50 || Math.abs(deltaX) > 50) {
                const gesture = this.gestureRecognizer.recognize(deltaX, deltaY);
                if (gesture) {
                    this.handleGesture(gesture);
                }
            }
        }, { passive: true });
    }
    
    addTouchFeedback() {
        const buttons = document.querySelectorAll('button, .btn');
        
        buttons.forEach(button => {
            button.addEventListener('touchstart', () => {
                button.classList.add('touch-active');
            }, { passive: true });
            
            button.addEventListener('touchend', () => {
                setTimeout(() => {
                    button.classList.remove('touch-active');
                }, 150);
            }, { passive: true });
        });
    }
    
    handleGesture(gesture) {
        console.log('🎆 Gesture detected:', gesture.type, gesture.direction);
        
        // Custom gesture handling can be added here
        const event = new CustomEvent('mobileGesture', {
            detail: gesture
        });
        
        document.dispatchEvent(event);
    }
}

class GestureRecognizer {
    recognize(deltaX, deltaY) {
        const threshold = 50;
        const gesture = { type: null, direction: null };
        
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            // Horizontal swipe
            if (Math.abs(deltaX) > threshold) {
                gesture.type = 'swipe';
                gesture.direction = deltaX > 0 ? 'left' : 'right';
            }
        } else {
            // Vertical swipe
            if (Math.abs(deltaY) > threshold) {
                gesture.type = 'swipe';
                gesture.direction = deltaY > 0 ? 'up' : 'down';
            }
        }
        
        return gesture.type ? gesture : null;
    }
}

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            frameRate: 0,
            memoryUsage: 0,
            processingLatency: [],
            networkLatency: []
        };
        
        this.isMonitoring = false;
    }
    
    startMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        
        // Monitor frame rate
        this.startFrameRateMonitoring();
        
        // Monitor memory (if available)
        this.startMemoryMonitoring();
        
        // Performance observer
        this.startPerformanceObserving();
        
        console.log('🎆 Performance monitoring started');
    }
    
    startFrameRateMonitoring() {
        let frames = 0;
        let lastTime = performance.now();
        
        const measureFPS = (currentTime) => {
            frames++;
            
            if (currentTime >= lastTime + 1000) {
                this.metrics.frameRate = Math.round((frames * 1000) / (currentTime - lastTime));
                frames = 0;
                lastTime = currentTime;
            }
            
            if (this.isMonitoring) {
                requestAnimationFrame(measureFPS);
            }
        };
        
        requestAnimationFrame(measureFPS);
    }
    
    startMemoryMonitoring() {
        if (!performance.memory) return;
        
        setInterval(() => {
            if (!this.isMonitoring) return;
            
            this.metrics.memoryUsage = {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
            };
        }, 5000);
    }
    
    startPerformanceObserving() {
        if (!window.PerformanceObserver) return;
        
        try {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.entryType === 'navigation') {
                        console.log('🎆 Page load performance:', Math.round(entry.loadEventEnd));
                    }
                });
            });
            
            observer.observe({ entryTypes: ['navigation', 'resource'] });
        } catch (error) {
            console.log('🎆 Performance observer not fully supported');
        }
    }
    
    recordProcessingLatency(latency) {
        this.metrics.processingLatency.push(latency);
        if (this.metrics.processingLatency.length > 50) {
            this.metrics.processingLatency = this.metrics.processingLatency.slice(-25);
        }
    }
    
    getPerformanceReport() {
        const avgProcessingLatency = this.metrics.processingLatency.length > 0
            ? this.metrics.processingLatency.reduce((a, b) => a + b, 0) / this.metrics.processingLatency.length
            : 0;
        
        return {
            frameRate: this.metrics.frameRate,
            memoryUsage: this.metrics.memoryUsage,
            averageProcessingLatency: Math.round(avgProcessingLatency),
            performanceScore: this.calculatePerformanceScore()
        };
    }
    
    calculatePerformanceScore() {
        let score = 100;
        
        // Frame rate penalty
        if (this.metrics.frameRate < 30) score -= 20;
        else if (this.metrics.frameRate < 45) score -= 10;
        
        // Memory usage penalty
        if (this.metrics.memoryUsage && this.metrics.memoryUsage.used > 100) {
            score -= 15;
        }
        
        // Processing latency penalty
        const avgLatency = this.metrics.processingLatency.length > 0
            ? this.metrics.processingLatency.reduce((a, b) => a + b, 0) / this.metrics.processingLatency.length
            : 1000;
        
        if (avgLatency > 3000) score -= 25;
        else if (avgLatency > 2000) score -= 15;
        else if (avgLatency > 1500) score -= 10;
        
        return Math.max(0, score);
    }
}

// Global initialization
window.MobileOptimizationEngine = MobileOptimizationEngine;

// Auto-initialize on mobile devices
document.addEventListener('DOMContentLoaded', () => {
    window.mobileOptimizer = new MobileOptimizationEngine();
});

console.log('🎆 Revolutionary Mobile Optimization Engine loaded!');

// [CTO] Defaults to ensure live interim is visible & frequent
window.MINA_FEATURES = Object.assign({
  ENABLE_INTERIM: true,
  SHOW_INTERIM: true,
  REPLACE_INTERIM_ON_FINAL: true,
  INTERIM_THROTTLE_MS: 250,
  RECORDER_TIMESLICE_MS: 250,
}, window.MINA_FEATURES || {});
