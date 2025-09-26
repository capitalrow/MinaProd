/**
 * Critical Error Handling and UI State Management Fixes
 * Addresses the "Error Error" display and empty error objects
 */

// Add these methods to the FixedMinaTranscription class

// Method 1: Clear error state
clearErrorState() {
    // Remove error displays from UI
    const errorElements = document.querySelectorAll('.error-display, .error-message, .alert-danger');
    errorElements.forEach(element => {
        element.remove();
    });
    
    // Clear error state from main error display
    const mainError = document.getElementById('mainError');
    if (mainError) {
        mainError.innerHTML = '';
        mainError.style.display = 'none';
    }
    
    // Clear error from system health
    const systemHealth = document.querySelector('.system-health');
    if (systemHealth) {
        systemHealth.classList.remove('error-state');
    }
    
    console.log('🧹 Error state cleared');
}

// Method 2: Show specific error state
showErrorState(errorMessage) {
    const mainError = document.getElementById('mainError');
    if (mainError) {
        mainError.innerHTML = `
            <div class="alert alert-warning alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Processing Issue:</strong> ${errorMessage}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        mainError.style.display = 'block';
    }
    
    console.log('⚠️ Error state shown:', errorMessage);
}

// Method 3: Show processing state
showProcessingState(chunkNumber) {
    const statusElement = document.querySelector('.processing-status');
    if (statusElement) {
        statusElement.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                <span>Processing chunk ${chunkNumber}...</span>
            </div>
        `;
    }
    
    console.log(`🔄 Processing state shown for chunk ${chunkNumber}`);
}

// Method 4: Clear processing state
clearProcessingState() {
    const statusElement = document.querySelector('.processing-status');
    if (statusElement) {
        statusElement.innerHTML = '';
    }
    
    console.log('✅ Processing state cleared');
}

// Method 5: Enhanced performance display
updatePerformanceDisplay(result) {
    // Update chunks processed
    const chunksElement = document.getElementById('chunksProcessed');
    if (chunksElement) {
        chunksElement.textContent = this.chunkCount;
        console.log(`📊 Chunks processed: ${this.chunkCount}`);
    }
    
    // Update latency
    const latencyElement = document.getElementById('latencyMs');
    if (latencyElement && result.processing_time_ms) {
        const latencyMs = Math.round(result.processing_time_ms);
        latencyElement.textContent = `${latencyMs}ms`;
        console.log(`⚡ Latency: ${latencyMs}ms`);
    }
    
    // Update quality score
    const qualityElement = document.getElementById('qualityScore');
    if (qualityElement && result.confidence !== undefined) {
        const qualityScore = Math.round(result.confidence * 100);
        qualityElement.textContent = `${qualityScore}%`;
        console.log(`🎯 Quality: ${qualityScore}%`);
        
        // Update quality indicator color
        qualityElement.className = `stat-value ${
            qualityScore >= 90 ? 'text-success' :
            qualityScore >= 70 ? 'text-warning' : 'text-danger'
        }`;
    }
    
    // Update word count from actual transcript
    const words = this.cumulativeText.split(/\s+/).filter(word => word.trim().length > 0);
    const wordCount = words.length;
    
    const wordsElement = document.getElementById('wordsCount');
    if (wordsElement) {
        wordsElement.textContent = wordCount;
        console.log(`📝 Words: ${wordCount}`);
    }
    
    // Calculate and display accuracy
    const accuracyElement = document.getElementById('accuracyPercentage');
    if (accuracyElement && result.confidence !== undefined) {
        const accuracy = Math.round(result.confidence * 100);
        accuracyElement.textContent = `${accuracy}%`;
        
        // Update accuracy indicator
        accuracyElement.className = `stat-value ${
            accuracy >= 90 ? 'text-success' :
            accuracy >= 70 ? 'text-warning' : 'text-danger'
        }`;
    }
    
    console.log('📊 Performance display updated successfully');
}

// Method 6: Enhanced error recovery
attemptRecovery(error) {
    const errorMessage = error.message.toLowerCase();
    
    if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
        console.log('🔄 Attempting recovery: network_retry');
        setTimeout(() => this.testConnection(), 2000);
    } else if (errorMessage.includes('timeout')) {
        console.log('🔄 Attempting recovery: timeout_retry');
        // Increase chunk size to reduce frequency
        this.adaptiveQuality.adjustForTimeout();
    } else if (errorMessage.includes('400') || errorMessage.includes('validation')) {
        console.log('🔄 Attempting recovery: format_retry');
        // Try different audio format
        this.streamingOptimizer.adjustFormat();
    } else {
        console.log('🔄 Attempting recovery: general_retry');
        // General recovery - wait and retry
        setTimeout(() => this.clearErrorState(), 3000);
    }
}

// Method 7: Connection testing
async testConnection() {
    try {
        const response = await fetch('/health', { method: 'GET', timeout: 5000 });
        if (response.ok) {
            console.log('✅ Connection test successful');
            this.clearErrorState();
            this.updateConnectionStatus('ready');
        } else {
            throw new Error(`Connection test failed: ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Connection test failed:', error);
        this.showErrorState('Connection issues detected');
        this.updateConnectionStatus('error');
    }
}

// Export for integration
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        clearErrorState,
        showErrorState,
        showProcessingState,
        clearProcessingState,
        updatePerformanceDisplay,
        attemptRecovery,
        testConnection
    };
}