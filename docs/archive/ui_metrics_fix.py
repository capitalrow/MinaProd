#!/usr/bin/env python3
"""
🔧 UI METRICS FIX IMPLEMENTATION
Critical fix for UI metrics not updating properly

ISSUE: Chunks, latency, and quality metrics show 0 during recording
CAUSE: Frontend updateStats() not properly updating all UI elements
"""

import json
from datetime import datetime

class UIMetricsFix:
    """Targeted fixes for UI metrics update issues"""
    
    def __init__(self):
        self.fixes_applied = []
        self.timestamp = datetime.now().isoformat()
    
    def identify_metrics_issue(self):
        """Identify the specific UI metrics update issues"""
        
        issues = {
            'chunks_processed_counter': {
                'element_id': 'chunksProcessed',
                'issue': 'Counter shows 0 even when chunks are being processed',
                'root_cause': 'updateStats() may not be incrementing chunkCount properly',
                'fix_needed': 'Ensure chunkCount increments on every successful chunk'
            },
            'latency_display': {
                'element_id': 'latencyMs',
                'issue': 'Shows 0ms despite processing taking 1200ms average',
                'root_cause': 'Latency not being calculated/displayed correctly',
                'fix_needed': 'Track and display actual processing latency'
            },
            'quality_score': {
                'element_id': 'qualityScore',
                'issue': 'Shows 0% despite having confidence scores',
                'root_cause': 'Quality calculation not implemented or not updating UI',
                'fix_needed': 'Map confidence scores to quality percentage'
            },
            'confidence_bars': {
                'element_id': 'confidenceFill',
                'issue': 'Progress bars not updating with confidence values',
                'root_cause': 'updateConfidenceIndicators may have element selection issues',
                'fix_needed': 'Fix element selection and bar width calculation'
            }
        }
        
        return issues
    
    def generate_javascript_fix(self):
        """Generate JavaScript fix for the metrics update issue"""
        
        js_fix = '''
/**
 * 🔧 CRITICAL FIX: UI Metrics Update
 * This addresses the core issue where UI metrics show 0 values
 */

// Add to FixedMinaTranscription class - enhanced updateStats method
updateStats(result) {
    console.log('🔢 Updating UI stats with:', result);
    
    // 🔧 FIX 1: Properly increment and display chunk count
    const chunksElement = document.getElementById('chunksProcessed');
    if (chunksElement) {
        chunksElement.textContent = this.chunkCount;
        console.log(`📊 Chunks processed: ${this.chunkCount}`);
    }
    
    // 🔧 FIX 2: Display actual latency from processing
    const latencyElement = document.getElementById('latencyMs');
    if (latencyElement && result.processing_time_ms) {
        const latencyMs = Math.round(result.processing_time_ms);
        latencyElement.textContent = `${latencyMs}ms`;
        console.log(`⚡ Latency: ${latencyMs}ms`);
    }
    
    // 🔧 FIX 3: Calculate and display quality score
    const qualityElement = document.getElementById('qualityScore');
    if (qualityElement && result.confidence !== undefined) {
        const qualityScore = Math.round(result.confidence * 100);
        qualityElement.textContent = `${qualityScore}%`;
        console.log(`🎯 Quality: ${qualityScore}%`);
    }
    
    // Update word count (this seems to be working)
    const words = this.cumulativeText.split(/\\s+/).filter(word => word.length > 0);
    this.totalWords = words.length;
    
    if (this.elements.wordCount) {
        this.elements.wordCount.textContent = this.totalWords;
    }
    
    // Update accuracy/confidence (this seems to be working)
    if (this.elements.accuracy) {
        const confidence = Math.round((result.confidence || 0.95) * 100);
        this.elements.accuracy.textContent = confidence + '%';
    }
    
    // 🔧 FIX 4: Update performance bars
    this.updatePerformanceBars(result);
}

// 🔧 NEW METHOD: Update performance bars with actual values
updatePerformanceBars(result) {
    const updates = {
        'confidenceFill': result.confidence ? Math.round(result.confidence * 100) : 0,
        'latencyFill': result.processing_time_ms ? Math.min(Math.round((5000 - result.processing_time_ms) / 5000 * 100), 100) : 0,
        'qualityFill': result.confidence ? Math.round(result.confidence * 100) : 0
    };
    
    Object.entries(updates).forEach(([elementId, percentage]) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.width = `${percentage}%`;
            console.log(`📊 ${elementId}: ${percentage}%`);
        }
    });
    
    // Update text values too
    const textUpdates = {
        'confidenceText': `${updates.confidenceFill}%`,
        'latencyText': result.processing_time_ms ? `${Math.round(result.processing_time_ms)}ms` : '0ms',
        'qualityText': `${updates.qualityFill}%`
    };
    
    Object.entries(textUpdates).forEach(([elementId, text]) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    });
}

// 🔧 ENHANCED: processAudioChunk method to provide better data to updateStats
async processAudioChunk(audioBlob) {
    try {
        const startTime = Date.now();
        
        // ... existing code ...
        
        const latency = Date.now() - startTime;
        
        if (response.ok) {
            const result = await response.json();
            
            // 🔧 CRITICAL FIX: Add processing time to result object
            result.processing_time_ms = latency;
            result.chunk_size_bytes = audioBlob.size;
            
            // Enhanced text validation
            if (result.text && result.text.trim() && 
                !result.text.includes('[No speech detected]') && 
                !result.text.includes('[Filtered]') &&
                !result.text.includes('[Audio chunk too small]') &&
                result.text.length > 1) {
                
                this.addTextToTranscript(result.text);
                
                // 🔧 CRITICAL: Call updateStats with complete result object
                this.updateUI(result);
                this.updateConnectionStatus('processing');
                
                console.log(`✅ Transcribed: "${result.text}" (${latency}ms, confidence: ${Math.round((result.confidence || 0.9) * 100)}%)`);
            } else {
                console.log(`⚠️ No valid speech in chunk ${this.chunkCount} (${latency}ms)`);
                
                // 🔧 NEW: Still update metrics even for failed chunks
                this.updateChunkMetrics({
                    processing_time_ms: latency,
                    confidence: 0,
                    chunk_size_bytes: audioBlob.size
                });
            }
        }
    } catch (error) {
        console.error('❌ Failed to process audio chunk:', error);
        this.updateConnectionStatus('error');
    }
}

// 🔧 NEW METHOD: Update chunk metrics even for non-speech chunks
updateChunkMetrics(metrics) {
    // Update chunks processed counter
    const chunksElement = document.getElementById('chunksProcessed');
    if (chunksElement) {
        chunksElement.textContent = this.chunkCount;
    }
    
    // Update latency even for failed chunks
    const latencyElement = document.getElementById('latencyMs');
    if (latencyElement && metrics.processing_time_ms) {
        latencyElement.textContent = `${Math.round(metrics.processing_time_ms)}ms`;
    }
    
    console.log(`📊 Metrics updated: chunk ${this.chunkCount}, latency ${Math.round(metrics.processing_time_ms)}ms`);
}
        '''
        
        return js_fix
    
    def generate_backend_response_fix(self):
        """Generate backend fix to ensure proper data in response"""
        
        python_fix = '''
# 🔧 BACKEND FIX: Ensure response includes all metrics needed by frontend
# Add to routes/audio_http.py in the transcribe_audio function

def transcribe_audio():
    request_start_time = time.time()
    
    # ... existing code ...
    
    # 🔧 CRITICAL FIX: Always include timing metrics in response
    processing_time_ms = (time.time() - request_start_time) * 1000
    
    # Successful transcription response
    if clean_text and clean_text.strip():
        response_data = {
            'session_id': session_id,
            'text': clean_text,
            'confidence': confidence,
            'chunk_number': chunk_number,
            'is_final': is_final,
            'status': 'success',
            
            # 🔧 NEW: Include metrics needed by frontend
            'processing_time_ms': processing_time_ms,
            'audio_quality': quality_metrics.get('quality_score', 0.0),
            'chunk_size_bytes': len(audio_bytes),
            'server_timestamp': time.time()
        }
    else:
        # No speech response - still include metrics
        response_data = {
            'session_id': session_id,
            'text': '[No valid speech]',
            'confidence': 0.0,
            'chunk_number': chunk_number,
            'is_final': is_final,
            'status': 'no_speech',
            
            # 🔧 NEW: Include metrics for UI updates
            'processing_time_ms': processing_time_ms,
            'audio_quality': quality_metrics.get('quality_score', 0.0),
            'chunk_size_bytes': len(audio_bytes),
            'reason': 'No valid speech detected'
        }
    
    return jsonify(response_data)
        '''
        
        return python_fix
    
    def create_implementation_plan(self):
        """Create step-by-step implementation plan"""
        
        plan = {
            'step_1_identify_elements': {
                'description': 'Verify all UI metric elements exist in HTML',
                'commands': [
                    'grep -n "chunksProcessed\\|latencyMs\\|qualityScore" templates/live.html'
                ],
                'expected': 'All metric element IDs found in template'
            },
            'step_2_update_javascript': {
                'description': 'Apply JavaScript fixes to fixed_transcription.js',
                'file': 'static/js/fixed_transcription.js',
                'changes': [
                    'Enhance updateStats() method',
                    'Add updatePerformanceBars() method',
                    'Fix processAudioChunk() to pass metrics',
                    'Add updateChunkMetrics() for non-speech chunks'
                ]
            },
            'step_3_update_backend': {
                'description': 'Ensure backend provides all required metrics',
                'file': 'routes/audio_http.py',
                'changes': [
                    'Include processing_time_ms in all responses',
                    'Include audio_quality metrics',
                    'Include chunk_size_bytes for analysis'
                ]
            },
            'step_4_test_metrics': {
                'description': 'Test metrics update in real-time',
                'test_procedure': [
                    '1. Start recording session',
                    '2. Speak for 10-15 seconds',
                    '3. Verify all metrics update in real-time',
                    '4. Check console logs for metric updates'
                ],
                'success_criteria': [
                    'Chunks counter increments with each chunk',
                    'Latency shows actual processing time',
                    'Quality reflects confidence scores',
                    'Progress bars update visually'
                ]
            }
        }
        
        return plan

def generate_fix_summary():
    """Generate comprehensive fix summary"""
    
    summary = {
        'issue_analysis': {
            'root_cause': 'Frontend updateStats() not properly updating all UI metric elements',
            'impact': 'Users see 0 values for chunks, latency, quality despite successful processing',
            'severity': 'HIGH - affects user experience and monitoring'
        },
        'solution_approach': {
            'frontend_fixes': [
                'Enhanced updateStats() method with proper element selection',
                'New updatePerformanceBars() method for visual indicators',
                'Improved processAudioChunk() to pass complete metrics',
                'New updateChunkMetrics() for comprehensive metric updates'
            ],
            'backend_enhancements': [
                'Include processing_time_ms in all responses',
                'Add audio quality metrics to responses',
                'Provide chunk size information for analysis'
            ]
        },
        'verification_steps': [
            'Test metrics update during recording',
            'Verify console logs show metric calculations',
            'Check UI elements receive proper values',
            'Validate metrics accuracy against backend logs'
        ]
    }
    
    return summary

if __name__ == "__main__":
    fixer = UIMetricsFix()
    
    print("🔧 UI METRICS FIX IMPLEMENTATION")
    print("=" * 50)
    
    issues = fixer.identify_metrics_issue()
    print("IDENTIFIED ISSUES:")
    for issue_key, details in issues.items():
        print(f"  🔍 {issue_key}: {details['issue']}")
    
    js_fix = fixer.generate_javascript_fix()
    print(f"\\n✅ JavaScript fix generated ({len(js_fix)} characters)")
    
    py_fix = fixer.generate_backend_response_fix()
    print(f"✅ Python backend fix generated ({len(py_fix)} characters)")
    
    plan = fixer.create_implementation_plan()
    print(f"✅ Implementation plan created ({len(plan)} steps)")
    
    summary = generate_fix_summary()
    print("\\n📋 FIX SUMMARY:")
    print(f"Root Cause: {summary['issue_analysis']['root_cause']}")
    print(f"Impact: {summary['issue_analysis']['impact']}")
    print(f"Severity: {summary['issue_analysis']['severity']}")
    
    # Save fix details
    with open('ui_metrics_fix_details.json', 'w') as f:
        json.dump({
            'issues': issues,
            'javascript_fix': js_fix,
            'python_fix': py_fix,
            'implementation_plan': plan,
            'fix_summary': summary
        }, f, indent=2)
    
    print("\\n📊 Complete fix details saved to: ui_metrics_fix_details.json")