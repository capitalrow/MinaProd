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
    Apply Google-level context processing to build complete sentences
    Based on analysis of Google's voice recording app screenshots
    """
    if not text or len(text.strip()) < 2:
        return text
    
    # Initialize session context if needed
    if session_id not in session_contexts:
        session_contexts[session_id] = {
            'sentence_buffer': '',
            'last_update': time.time(),
            'context_words': [],
            'completion_confidence': 0.0
        }
    
    context = session_contexts[session_id]
    current_time = time.time()
    
    # Google-style processing rules based on screenshots:
    
    # 1. Context building - Don't repeat the same word endlessly
    if text.lower().strip() == 'you' and 'you' in context['context_words'][-3:]:
        logger.info(f"🔄 GOOGLE-STYLE: Skipping repeated 'you' - building context instead")
        
        # Try to build meaningful context from repeated attempts
        if context['sentence_buffer']:
            enhanced_text = context['sentence_buffer'] + " "
            context['sentence_buffer'] = enhanced_text.strip()
            return enhanced_text
        else:
            # Start a sentence context
            context['sentence_buffer'] = "You"
            context['context_words'] = ['you']
            return "You"
    
    # 2. Sentence building - like Google's progressive text
    if text.lower().strip() not in ['you', 'the', 'a', 'an']:
        # This looks like meaningful content
        if context['sentence_buffer']:
            enhanced_text = f"{context['sentence_buffer']} {text}"
        else:
            enhanced_text = text
        
        context['sentence_buffer'] = enhanced_text.strip()
        context['context_words'].append(text.lower())
        context['last_update'] = current_time
        
        logger.info(f"✅ GOOGLE-STYLE: Built sentence context: '{enhanced_text}'")
        return enhanced_text
    
    # 3. Handle common words with context
    if context['sentence_buffer'] and (current_time - context['last_update']) < 5.0:
        enhanced_text = f"{context['sentence_buffer']} {text}"
        context['sentence_buffer'] = enhanced_text.strip()
        return enhanced_text
    
    # 4. Default: return as-is but update context
    context['context_words'].append(text.lower())
    if len(context['context_words']) > 10:
        context['context_words'] = context['context_words'][-10:]
    
    return text

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