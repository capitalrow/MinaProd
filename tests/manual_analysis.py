#!/usr/bin/env python3
"""
Manual Live Session Analysis
Analyzes session data from browser console logs
"""

import time
import json
from datetime import datetime

def analyze_session_manually():
    """Guide user through manual session analysis"""
    
    print("📊 MANUAL LIVE SESSION ANALYSIS TOOL")
    print("="*50)
    print()
    print("🎤 LIVE TESTING PROTOCOL:")
    print("="*30)
    print()
    print("1️⃣ BEFORE RECORDING:")
    print("   • Open browser developer console (F12)")
    print("   • Navigate to /live page")
    print("   • Note the current time")
    print()
    print("2️⃣ DURING RECORDING:")
    print("   • Click 'Start Recording'")
    print("   • Speak clearly for 1-2 minutes")
    print("   • Watch console for transcription events")
    print("   • Note first text appearance time")
    print()
    print("3️⃣ RECORD THESE METRICS:")
    
    # Collect manual metrics
    print("\n📝 Please provide these details after your test:")
    print()
    
    session_id = input("🆔 Session ID (from console): ").strip()
    first_response_time = input("⚡ First response time (seconds): ").strip()
    total_interims = input("📝 Number of interim transcripts: ").strip()
    total_finals = input("✅ Number of final transcripts: ").strip()
    final_transcript = input("📄 Final transcript text: ").strip()
    perceived_accuracy = input("🎯 Accuracy (1-10 scale): ").strip()
    
    # Calculate quality score
    score = calculate_manual_quality_score(
        first_response_time, total_interims, total_finals, 
        final_transcript, perceived_accuracy
    )
    
    # Generate report
    generate_manual_report(
        session_id, first_response_time, total_interims, 
        total_finals, final_transcript, perceived_accuracy, score
    )

def calculate_manual_quality_score(first_response, interims, finals, transcript, accuracy):
    """Calculate quality score from manual inputs"""
    score = 5
    
    try:
        # Response time scoring
        if first_response and float(first_response) <= 2.0:
            score += 2
        elif first_response and float(first_response) <= 3.0:
            score += 1
        
        # Activity scoring
        if interims and int(interims) >= 10:
            score += 2
        elif interims and int(interims) >= 5:
            score += 1
        
        # Transcript quality
        if transcript and len(transcript) > 50:
            score += 1
        
        # User perceived accuracy
        if accuracy and int(accuracy) >= 8:
            score += 1
    except:
        pass
    
    return min(10, max(1, score))

def generate_manual_report(session_id, first_response, interims, finals, transcript, accuracy, score):
    """Generate comprehensive manual analysis report"""
    
    print("\n" + "="*60)
    print("📊 LIVE SESSION ANALYSIS REPORT")
    print("="*60)
    
    print(f"\n🎯 SESSION OVERVIEW:")
    print(f"   Session ID: {session_id}")
    print(f"   Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n⚡ PERFORMANCE METRICS:")
    print(f"   First Response Time: {first_response}s")
    print(f"   Interim Transcripts: {interims}")
    print(f"   Final Transcripts: {finals}")
    print(f"   User Perceived Accuracy: {accuracy}/10")
    
    print(f"\n📄 TRANSCRIPT:")
    print(f"   '{transcript}'")
    
    print(f"\n⭐ QUALITY ASSESSMENT:")
    print(f"   Overall Score: {score}/10")
    print(f"   Status: {get_quality_status(score)}")
    
    # Improvement suggestions
    suggestions = get_improvement_suggestions(score, first_response, interims)
    if suggestions:
        print(f"\n🔧 IMPROVEMENT SUGGESTIONS:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    # Iteration planning
    if score < 9:
        print(f"\n🔁 ITERATION RECOMMENDED:")
        print(f"   Current score ({score}/10) is below target (9/10)")
        print(f"   Recommended next steps:")
        print(f"   1. Implement suggested improvements")
        print(f"   2. Rerun live test")
        print(f"   3. Compare results")
    else:
        print(f"\n🎉 EXCELLENT PERFORMANCE!")
        print(f"   Score {score}/10 meets quality target")
        print(f"   System ready for production use")

def get_quality_status(score):
    """Get quality status description"""
    if score >= 9:
        return "Excellent - Production Ready"
    elif score >= 7:
        return "Good - Minor Improvements Needed"
    elif score >= 5:
        return "Average - Optimization Required"
    else:
        return "Poor - Major Improvements Needed"

def get_improvement_suggestions(score, first_response, interims):
    """Get specific improvement suggestions"""
    suggestions = []
    
    try:
        if first_response and float(first_response) > 3.0:
            suggestions.append("Reduce first response latency by optimizing VAD settings")
        
        if interims and int(interims) < 5:
            suggestions.append("Increase interim frequency by reducing throttle timing")
        
        if score < 6:
            suggestions.append("Consider more aggressive buffering strategy")
            
    except:
        suggestions.append("Verify transcription system configuration")
    
    return suggestions

if __name__ == "__main__":
    analyze_session_manually()