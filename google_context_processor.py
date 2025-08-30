"""
🎯 GOOGLE-QUALITY CONTEXT PROCESSOR
Based on reference screenshots showing Google's superior transcription quality
"""

import logging
from typing import Dict, List
import time
import re

logger = logging.getLogger(__name__)

# Session context storage for Google-style sentence building
session_contexts: Dict[str, Dict] = {}

def apply_google_style_processing(text: str, session_id: str) -> str:
    """
    🎯 ENHANCED: Google-quality context processing for natural speech flow
    Builds complete, coherent sentences like Google Recorder
    """
    if not text or len(text.strip()) < 1:
        return text
    
    # Initialize session context if needed
    if session_id not in session_contexts:
        session_contexts[session_id] = {
            'sentence_buffer': '',
            'last_update': time.time(),
            'context_words': [],
            'word_repetition_count': {},
            'last_meaningful_text': '',
            'sentence_count': 0
        }
    
    context = session_contexts[session_id]
    current_time = time.time()
    clean_text = text.strip()
    word_lower = clean_text.lower()
    
    # Track word repetitions
    if word_lower in context['word_repetition_count']:
        context['word_repetition_count'][word_lower] += 1
    else:
        context['word_repetition_count'][word_lower] = 1
    
    # Google-style processing rules:
    
    # 🔥 CRITICAL FIX: Smart repetition detection for Google Recorder accuracy
    consecutive_count = 1
    if 'last_words' not in context:
        context['last_words'] = []
    
    # Count consecutive occurrences
    for prev_word in reversed(context['last_words'][-5:]):  # Check last 5 words
        if prev_word.lower() == word_lower:
            consecutive_count += 1
        else:
            break
    
    # Only filter excessive consecutive repetition (5+ times)
    if consecutive_count >= 5:
        logger.info(f"🔄 GOOGLE-QUALITY: Filtering excessive repetition '{word_lower}' ({consecutive_count}x consecutive)")
        return context.get('sentence_buffer', clean_text)  # Return existing buffer
    
    # 2. SENTENCE BUILDING: Build progressive sentences like Google
    time_since_last = current_time - context['last_update']
    
    if time_since_last < 3.0:  # Within 3 seconds - likely same sentence
        if context['sentence_buffer']:
            # Smart concatenation - avoid duplicate words
            buffer_words = context['sentence_buffer'].lower().split()
            if word_lower not in buffer_words[-2:]:  # Not in last 2 words
                enhanced_text = f"{context['sentence_buffer']} {clean_text}"
            else:
                enhanced_text = context['sentence_buffer']  # Skip duplicate
        else:
            enhanced_text = clean_text.capitalize()
    else:
        # New sentence - start fresh
        enhanced_text = clean_text.capitalize()
        context['sentence_count'] += 1
    
    # 3. CAPITALIZATION & PUNCTUATION: Like Google's professional output
    if enhanced_text and not enhanced_text[0].isupper():
        enhanced_text = enhanced_text[0].upper() + enhanced_text[1:]
    
    # Add periods for readability every 15-20 words
    word_count = len(enhanced_text.split())
    if word_count > 0 and word_count % 15 == 0 and not enhanced_text.endswith(('.',  '!', '?')):
        enhanced_text += '.'
    
    # Update context
    context['sentence_buffer'] = enhanced_text
    context['last_update'] = current_time
    context['context_words'].append(word_lower)
    context['last_word'] = clean_text
    context['last_meaningful_text'] = clean_text
    
    # 🔥 Track last words for consecutive detection
    if 'last_words' not in context:
        context['last_words'] = []
    context['last_words'].append(clean_text)
    if len(context['last_words']) > 10:
        context['last_words'] = context['last_words'][-5:]  # Keep only last 5
    
    # Keep context manageable
    if len(context['context_words']) > 50:
        context['context_words'] = context['context_words'][-30:]
    
    logger.debug(f"✅ GOOGLE-ENHANCED: '{text}' → '{enhanced_text[:100]}{'...' if len(enhanced_text) > 100 else ''}' ({word_count} words)")
    return enhanced_text

def get_session_context(session_id: str) -> str:
    """Get the current sentence context for a session (like Google's continuous text)"""
    if session_id in session_contexts:
        return session_contexts[session_id].get('sentence_buffer', '')
    return ''

def clear_session_context(session_id: str):
    """Clear context when recording stops"""
    if session_id in session_contexts:
        del session_contexts[session_id]
        logger.info(f"🧹 Cleared Google-style context for session {session_id}")