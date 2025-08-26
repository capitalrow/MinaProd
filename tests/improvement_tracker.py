#!/usr/bin/env python3
"""
Improvement Tracker for Iterative Testing
Tracks improvements across testing iterations
"""

import json
from datetime import datetime
from typing import List, Dict, Any

class ImprovementTracker:
    """Tracks improvements and iterations in live testing"""
    
    def __init__(self):
        self.iterations = []
        self.improvements_implemented = []
    
    def record_iteration(self, iteration_num: int, results: Dict[str, Any], 
                        improvements_planned: List[str] = None, 
                        reflections: List[str] = None):
        """Record results from a testing iteration"""
        
        iteration_data = {
            'iteration': iteration_num,
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'quality_score': results.get('quality_score', 0),
            'improvements_planned': improvements_planned or [],
            'reflections': reflections or [],
            'performance_summary': {
                'first_response_latency': results.get('performance_metrics', {}).get('first_response_latency'),
                'total_interims': results.get('performance_metrics', {}).get('total_interims', 0),
                'total_finals': results.get('performance_metrics', {}).get('total_finals', 0),
                'transcript_length': len(results.get('final_transcript', ''))
            }
        }
        
        self.iterations.append(iteration_data)
        
        print(f"\n📊 ITERATION {iteration_num} RECORDED")
        print(f"   Quality Score: {results.get('quality_score', 0)}/10")
        print(f"   Duration: {results.get('duration', 0):.1f}s")
        print(f"   Interims: {results.get('performance_metrics', {}).get('total_interims', 0)}")
        print(f"   Finals: {results.get('performance_metrics', {}).get('total_finals', 0)}")
    
    def suggest_improvements(self, current_results: Dict[str, Any]) -> List[str]:
        """Suggest concrete improvements based on current performance"""
        improvements = []
        
        metrics = current_results.get('performance_metrics', {})
        quality_score = current_results.get('quality_score', 0)
        
        # Latency improvements
        first_response = metrics.get('first_response_latency')
        if first_response and first_response > 3.0:
            improvements.append("Optimize first response latency by reducing VAD min_speech_duration further")
        
        # Interim frequency
        interims = metrics.get('total_interims', 0)
        duration = current_results.get('duration', 1)
        interim_rate = interims / duration if duration > 0 else 0
        
        if interim_rate < 0.3:  # Less than 1 interim per 3 seconds
            improvements.append("Increase interim frequency by reducing interim_throttle_ms")
        
        # Transcription completeness
        transcript_length = len(current_results.get('final_transcript', ''))
        if transcript_length < 50:
            improvements.append("Improve transcription capture by adjusting confidence thresholds")
        
        # Quality-based suggestions
        if quality_score < 6:
            improvements.append("Implement more aggressive buffering strategy for better responsiveness")
        
        if not improvements:
            improvements.append("Fine-tune existing parameters for marginal performance gains")
        
        return improvements
    
    def get_improvement_summary(self) -> Dict[str, Any]:
        """Get summary of improvements across iterations"""
        if not self.iterations:
            return {}
        
        summary = {
            'total_iterations': len(self.iterations),
            'quality_progression': [it['quality_score'] for it in self.iterations],
            'best_iteration': max(self.iterations, key=lambda x: x['quality_score']),
            'improvements_attempted': [],
            'performance_trends': {}
        }
        
        # Collect all improvements
        for iteration in self.iterations:
            summary['improvements_attempted'].extend(iteration.get('improvements_planned', []))
        
        # Calculate trends
        if len(self.iterations) > 1:
            first_score = self.iterations[0]['quality_score']
            last_score = self.iterations[-1]['quality_score']
            summary['quality_improvement'] = last_score - first_score
            
            # Latency trend
            latencies = [it['performance_summary']['first_response_latency'] 
                        for it in self.iterations 
                        if it['performance_summary']['first_response_latency']]
            if len(latencies) > 1:
                summary['latency_trend'] = latencies[-1] - latencies[0]
        
        return summary
    
    def generate_final_report(self) -> str:
        """Generate final report with recommendations"""
        if not self.iterations:
            return "No iterations recorded"
        
        summary = self.get_improvement_summary()
        best = summary['best_iteration']
        
        report = f"""
🎯 FINAL TESTING REPORT
=====================

📈 ITERATION SUMMARY:
   Total Iterations: {summary['total_iterations']}
   Quality Scores: {' → '.join(map(str, summary['quality_progression']))}
   Best Score: {best['quality_score']}/10 (Iteration {best['iteration']})

🏆 BEST PERFORMANCE:
   Session: {best['results']['session_id']}
   Duration: {best['results']['duration']:.1f}s
   First Response: {best['performance_summary']['first_response_latency']:.2f}s
   Interims: {best['performance_summary']['total_interims']}
   Finals: {best['performance_summary']['total_finals']}
   Transcript: "{best['results']['final_transcript'][:100]}..."

🔧 IMPROVEMENTS ATTEMPTED:
"""
        
        for i, iteration in enumerate(self.iterations, 1):
            if iteration.get('improvements_planned'):
                report += f"\n   Iteration {i}:"
                for improvement in iteration['improvements_planned']:
                    report += f"\n     • {improvement}"
        
        # Final recommendation
        final_score = self.iterations[-1]['quality_score']
        if final_score >= 9:
            recommendation = "Excellent performance achieved. Focus on maintaining stability and monitoring production metrics."
        elif final_score >= 7:
            recommendation = "Good performance. Consider fine-tuning confidence thresholds and implementing user feedback mechanisms."
        else:
            recommendation = "Performance needs improvement. Focus on latency optimization, better VAD tuning, and enhanced audio preprocessing."
        
        report += f"""

💡 DEVELOPER RECOMMENDATION:
{recommendation}

For your Mina transcription engine, I recommend:
1. Implementing adaptive configuration based on audio environment detection
2. Adding user-configurable sensitivity settings for different use cases
3. Enhancing the interim/final decision logic with better punctuation boundary detection
4. Consider implementing audio quality preprocessing to improve Whisper API performance
        """
        
        return report

# Global tracker instance
improvement_tracker = ImprovementTracker()

if __name__ == "__main__":
    print("🔧 Improvement Tracker Ready")
    print("Use this to track testing iterations and improvements")