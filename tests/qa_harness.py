#!/usr/bin/env python3
"""
QA Harness for Mina Transcription System
Comparative analysis, WER calculation, and quality metrics
"""

import json
import difflib
import re
import time
from typing import Dict, List, Any, Tuple
from datetime import datetime
import hashlib

class TranscriptionQAHarness:
    """Quality assurance harness for transcription accuracy"""
    
    def __init__(self):
        self.qa_sessions = {}
        self.reference_audio = {}
        self.transcripts = {}
        self.quality_metrics = {}
    
    def start_qa_session(self, session_id: str, reference_text: str = None, audio_file: str = None):
        """Start a QA session with optional reference"""
        self.qa_sessions[session_id] = {
            'start_time': time.time(),
            'reference_text': reference_text,
            'audio_file': audio_file,
            'interim_transcripts': [],
            'final_transcript': None,
            'timestamps': [],
            'confidence_scores': [],
            'processing_events': []
        }
        
        print(f"🎯 QA Session started: {session_id}")
        if reference_text:
            print(f"📝 Reference text provided: {len(reference_text)} characters")
    
    def record_interim_transcript(self, session_id: str, text: str, confidence: float, timestamp: float = None):
        """Record interim transcript for analysis"""
        if session_id not in self.qa_sessions:
            return
        
        timestamp = timestamp or time.time()
        
        self.qa_sessions[session_id]['interim_transcripts'].append({
            'text': text,
            'confidence': confidence,
            'timestamp': timestamp,
            'word_count': len(text.split()),
            'char_count': len(text)
        })
        
        print(f"📝 Interim recorded: '{text[:50]}...' (conf: {confidence:.2f})")
    
    def record_final_transcript(self, session_id: str, text: str, confidence: float):
        """Record final transcript"""
        if session_id not in self.qa_sessions:
            return
        
        self.qa_sessions[session_id]['final_transcript'] = {
            'text': text,
            'confidence': confidence,
            'timestamp': time.time(),
            'word_count': len(text.split()),
            'char_count': len(text)
        }
        
        print(f"✅ Final transcript recorded: '{text[:50]}...' (conf: {confidence:.2f})")
    
    def calculate_wer(self, reference: str, hypothesis: str) -> Dict[str, Any]:
        """Calculate Word Error Rate (WER) and related metrics"""
        # Normalize text
        ref_words = self._normalize_text(reference).split()
        hyp_words = self._normalize_text(hypothesis).split()
        
        # Calculate edit distance
        distance_matrix = self._edit_distance_matrix(ref_words, hyp_words)
        distance = distance_matrix[-1][-1]
        
        # Calculate metrics
        wer = distance / max(len(ref_words), 1)
        
        # Detailed analysis
        alignment = self._get_alignment(ref_words, hyp_words, distance_matrix)
        
        substitutions = sum(1 for op, _, _ in alignment if op == 'substitute')
        insertions = sum(1 for op, _, _ in alignment if op == 'insert')
        deletions = sum(1 for op, _, _ in alignment if op == 'delete')
        
        return {
            'wer': wer,
            'wer_percentage': wer * 100,
            'total_words': len(ref_words),
            'errors': distance,
            'substitutions': substitutions,
            'insertions': insertions,
            'deletions': deletions,
            'accuracy': max(0, 1 - wer),
            'alignment': alignment[:10]  # First 10 for debugging
        }
    
    def detect_hallucinations(self, text: str, audio_duration: float) -> Dict[str, Any]:
        """Detect potential hallucinations in transcript"""
        words = text.split()
        
        # Calculate speaking rate
        speaking_rate = len(words) / max(audio_duration, 1) * 60  # words per minute
        
        # Detect repetitions
        repetitions = self._detect_repetitions(words)
        
        # Detect common hallucination patterns
        hallucination_patterns = [
            r'\b(thank you for watching|please subscribe|like and subscribe)\b',
            r'\b(um|uh|er){3,}',  # Excessive filler words
            r'\b(\w+)\s+\1\s+\1\b',  # Triple repetitions
        ]
        
        pattern_matches = []
        for pattern in hallucination_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                pattern_matches.extend(matches)
        
        return {
            'speaking_rate_wpm': speaking_rate,
            'excessive_rate': speaking_rate > 200,  # Unusually fast
            'repetitions': repetitions,
            'pattern_matches': pattern_matches,
            'hallucination_score': len(repetitions) + len(pattern_matches),
            'likely_hallucination': len(repetitions) > 3 or len(pattern_matches) > 2
        }
    
    def analyze_drift(self, session_id: str) -> Dict[str, Any]:
        """Analyze transcript drift over time"""
        if session_id not in self.qa_sessions:
            return {'error': 'Session not found'}
        
        interims = self.qa_sessions[session_id]['interim_transcripts']
        if len(interims) < 2:
            return {'drift': 0, 'analysis': 'insufficient_data'}
        
        # Calculate drift between consecutive interims
        drift_scores = []
        for i in range(1, len(interims)):
            prev_text = interims[i-1]['text']
            curr_text = interims[i]['text']
            
            # Calculate similarity
            similarity = difflib.SequenceMatcher(None, prev_text, curr_text).ratio()
            drift = 1 - similarity
            drift_scores.append(drift)
        
        avg_drift = sum(drift_scores) / len(drift_scores)
        max_drift = max(drift_scores)
        
        return {
            'average_drift': avg_drift,
            'maximum_drift': max_drift,
            'drift_events': len([d for d in drift_scores if d > 0.3]),
            'stability_score': 1 - avg_drift,
            'analysis': 'stable' if avg_drift < 0.1 else 'moderate' if avg_drift < 0.3 else 'unstable'
        }
    
    def detect_duplicates(self, transcripts: List[str]) -> Dict[str, Any]:
        """Detect duplicate or near-duplicate transcripts"""
        duplicates = []
        near_duplicates = []
        
        for i, text1 in enumerate(transcripts):
            for j, text2 in enumerate(transcripts[i+1:], i+1):
                similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
                
                if similarity == 1.0:
                    duplicates.append((i, j, text1))
                elif similarity > 0.8:
                    near_duplicates.append((i, j, similarity, text1, text2))
        
        return {
            'exact_duplicates': len(duplicates),
            'near_duplicates': len(near_duplicates),
            'duplicate_pairs': duplicates[:5],  # First 5 for analysis
            'near_duplicate_pairs': near_duplicates[:5],
            'duplication_rate': len(duplicates) / max(len(transcripts), 1)
        }
    
    def analyze_confidence_accuracy(self, session_id: str) -> Dict[str, Any]:
        """Analyze relationship between confidence scores and actual accuracy"""
        if session_id not in self.qa_sessions:
            return {'error': 'Session not found'}
        
        session = self.qa_sessions[session_id]
        interims = session['interim_transcripts']
        
        if not interims:
            return {'analysis': 'no_data'}
        
        confidence_scores = [interim['confidence'] for interim in interims]
        
        # Analyze confidence distribution
        high_conf = len([c for c in confidence_scores if c >= 0.8])
        medium_conf = len([c for c in confidence_scores if 0.5 <= c < 0.8])
        low_conf = len([c for c in confidence_scores if c < 0.5])
        
        return {
            'total_interims': len(confidence_scores),
            'average_confidence': sum(confidence_scores) / len(confidence_scores),
            'confidence_distribution': {
                'high': high_conf,
                'medium': medium_conf,
                'low': low_conf
            },
            'confidence_trend': self._calculate_trend(confidence_scores),
            'reliability_score': high_conf / len(confidence_scores)
        }
    
    def generate_qa_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive QA report"""
        if session_id not in self.qa_sessions:
            return {'error': 'Session not found'}
        
        session = self.qa_sessions[session_id]
        session_duration = time.time() - session['start_time']
        
        report = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'session_duration': session_duration,
            'summary': {
                'total_interims': len(session['interim_transcripts']),
                'has_final': session['final_transcript'] is not None,
                'session_complete': session['final_transcript'] is not None
            }
        }
        
        # WER Analysis (if reference available)
        if session['reference_text'] and session['final_transcript']:
            wer_analysis = self.calculate_wer(
                session['reference_text'],
                session['final_transcript']['text']
            )
            report['wer_analysis'] = wer_analysis
        
        # Hallucination Detection
        if session['final_transcript']:
            hallucination_analysis = self.detect_hallucinations(
                session['final_transcript']['text'],
                session_duration
            )
            report['hallucination_analysis'] = hallucination_analysis
        
        # Drift Analysis
        drift_analysis = self.analyze_drift(session_id)
        report['drift_analysis'] = drift_analysis
        
        # Duplicate Detection
        all_texts = [interim['text'] for interim in session['interim_transcripts']]
        if session['final_transcript']:
            all_texts.append(session['final_transcript']['text'])
        
        duplicate_analysis = self.detect_duplicates(all_texts)
        report['duplicate_analysis'] = duplicate_analysis
        
        # Confidence Analysis
        confidence_analysis = self.analyze_confidence_accuracy(session_id)
        report['confidence_analysis'] = confidence_analysis
        
        # Calculate overall quality score
        quality_score = self._calculate_overall_quality(report)
        report['quality_score'] = quality_score
        
        return report
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _edit_distance_matrix(self, ref_words: List[str], hyp_words: List[str]) -> List[List[int]]:
        """Calculate edit distance matrix for WER calculation"""
        m, n = len(ref_words), len(hyp_words)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize base cases
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # Fill the matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # deletion
                        dp[i][j-1],    # insertion
                        dp[i-1][j-1]   # substitution
                    )
        
        return dp
    
    def _get_alignment(self, ref_words: List[str], hyp_words: List[str], dp: List[List[int]]) -> List[Tuple[str, str, str]]:
        """Get alignment path for error analysis"""
        alignment = []
        i, j = len(ref_words), len(hyp_words)
        
        while i > 0 or j > 0:
            if i > 0 and j > 0 and ref_words[i-1] == hyp_words[j-1]:
                alignment.append(('match', ref_words[i-1], hyp_words[j-1]))
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                alignment.append(('substitute', ref_words[i-1], hyp_words[j-1]))
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                alignment.append(('delete', ref_words[i-1], ''))
                i -= 1
            else:
                alignment.append(('insert', '', hyp_words[j-1]))
                j -= 1
        
        return list(reversed(alignment))
    
    def _detect_repetitions(self, words: List[str]) -> List[Dict[str, Any]]:
        """Detect word repetitions"""
        repetitions = []
        i = 0
        
        while i < len(words) - 1:
            if words[i] == words[i + 1]:
                # Found repetition, count length
                count = 1
                j = i + 1
                while j < len(words) and words[j] == words[i]:
                    count += 1
                    j += 1
                
                if count >= 2:  # At least 2 repetitions
                    repetitions.append({
                        'word': words[i],
                        'count': count,
                        'position': i
                    })
                
                i = j
            else:
                i += 1
        
        return repetitions
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'stable'
        
        first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
        second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half_avg > first_half_avg + 0.1:
            return 'improving'
        elif second_half_avg < first_half_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_overall_quality(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall quality score"""
        score = 5.0  # Base score
        
        # WER contribution
        if 'wer_analysis' in report:
            wer = report['wer_analysis']['wer']
            wer_score = max(0, 5 - (wer * 10))  # 0-5 points
            score += wer_score
        
        # Confidence contribution
        if 'confidence_analysis' in report:
            reliability = report['confidence_analysis'].get('reliability_score', 0.5)
            conf_score = reliability * 2  # 0-2 points
            score += conf_score
        
        # Stability contribution
        if 'drift_analysis' in report:
            stability = report['drift_analysis'].get('stability_score', 0.5)
            stability_score = stability * 2  # 0-2 points
            score += stability_score
        
        # Hallucination penalty
        if 'hallucination_analysis' in report:
            if report['hallucination_analysis'].get('likely_hallucination', False):
                score -= 1
        
        # Duplicate penalty
        if 'duplicate_analysis' in report:
            dup_rate = report['duplicate_analysis'].get('duplication_rate', 0)
            score -= dup_rate * 2
        
        return {
            'overall_score': max(0, min(10, score)),
            'category': 'excellent' if score >= 8 else 'good' if score >= 6 else 'fair' if score >= 4 else 'poor'
        }

# Example usage
def run_qa_example():
    """Example QA session"""
    qa = TranscriptionQAHarness()
    
    # Start session with reference
    qa.start_qa_session(
        'test_session_001',
        reference_text="Hello world this is a test of the transcription system",
        audio_file="test_audio.wav"
    )
    
    # Record some interims
    qa.record_interim_transcript('test_session_001', "hello", 0.9)
    qa.record_interim_transcript('test_session_001', "hello world", 0.85)
    qa.record_interim_transcript('test_session_001', "hello world this is", 0.88)
    
    # Record final
    qa.record_final_transcript('test_session_001', "hello world this is a test of transcription", 0.92)
    
    # Generate report
    report = qa.generate_qa_report('test_session_001')
    
    print("🎯 QA REPORT")
    print("="*40)
    print(json.dumps(report, indent=2))
    
    return report

if __name__ == "__main__":
    run_qa_example()