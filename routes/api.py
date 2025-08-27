"""
API endpoints for advanced transcription features including GPT-4 transcript refinement.
"""
import os
import json
import openai
from flask import Blueprint, request, jsonify
from flask_login import login_required
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/refine-transcript', methods=['POST'])
def refine_transcript():
    """
    Refine raw transcript using GPT-4 for industry-standard quality.
    
    This endpoint takes a raw transcript and uses GPT-4 to:
    - Fix grammar and punctuation
    - Improve readability and structure  
    - Generate an executive summary
    - Maintain original meaning and context
    """
    try:
        data = request.get_json()
        
        if not data or 'raw_transcript' not in data:
            return jsonify({'error': 'raw_transcript is required'}), 400
            
        raw_transcript = data['raw_transcript'].strip()
        refinement_level = data.get('refinement_level', 'standard')
        segments = data.get('segments', [])
        
        if len(raw_transcript) < 10:
            return jsonify({'error': 'Transcript too short for refinement'}), 400
            
        logger.info(f"Refining transcript: {len(raw_transcript)} characters, {len(segments)} segments")
        
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OpenAI API key not configured - using raw transcript")
            return jsonify({
                'refined_transcript': raw_transcript,
                'summary': 'Raw transcript (OpenAI API not configured)',
                'method': 'fallback'
            })
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create refinement prompt based on level
        if refinement_level == 'professional':
            system_prompt = """You are a professional transcript editor. Refine the following speech-to-text transcript to:

1. Fix grammar, punctuation, and sentence structure
2. Remove filler words (um, uh, like) and false starts
3. Organize content into clear paragraphs
4. Maintain the original speaker's voice and meaning
5. Ensure professional readability

Keep the content factual and preserve all important information. Do not add content that wasn't spoken."""

        else:  # standard
            system_prompt = """You are a transcript editor. Clean up the following speech-to-text transcript by:

1. Fixing basic grammar and punctuation
2. Removing obvious filler words
3. Organizing into readable sentences
4. Preserving the original meaning

Keep changes minimal and maintain the speaker's natural voice."""

        user_prompt = f"Please refine this transcript:\n\n{raw_transcript}"
        
        # Call GPT-4 for transcript refinement
        try:
            refinement_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.1  # Low temperature for consistency
            )
            
            refined_transcript = refinement_response.choices[0].message.content.strip()
            
            # Generate summary
            summary_response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a summarization expert. Create a concise 2-3 sentence summary of the key points from this transcript."},
                    {"role": "user", "content": f"Summarize this transcript:\n\n{refined_transcript}"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            summary = summary_response.choices[0].message.content.strip()
            
            logger.info(f"Successfully refined transcript using GPT-4")
            
            return jsonify({
                'refined_transcript': refined_transcript,
                'summary': summary,
                'method': 'gpt4_refinement',
                'original_length': len(raw_transcript),
                'refined_length': len(refined_transcript),
                'segments_processed': len(segments)
            })
            
        except Exception as openai_error:
            logger.error(f"OpenAI API error: {openai_error}")
            
            # Fallback: Basic text cleanup
            cleaned_transcript = basic_transcript_cleanup(raw_transcript)
            
            return jsonify({
                'refined_transcript': cleaned_transcript,
                'summary': 'Basic cleanup applied (GPT-4 unavailable)',
                'method': 'basic_cleanup',
                'error': str(openai_error)
            })
            
    except Exception as e:
        logger.error(f"Transcript refinement error: {e}")
        return jsonify({'error': f'Refinement failed: {str(e)}'}), 500

def basic_transcript_cleanup(text):
    """
    Fallback transcript cleanup without AI.
    Applies basic text processing rules.
    """
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Basic sentence capitalization
    sentences = text.split('. ')
    cleaned_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Capitalize first letter
            sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            cleaned_sentences.append(sentence)
    
    # Join sentences back
    cleaned_text = '. '.join(cleaned_sentences)
    
    # Ensure proper ending punctuation
    if cleaned_text and not cleaned_text.endswith(('.', '!', '?')):
        cleaned_text += '.'
    
    return cleaned_text

@api_bp.route('/transcript-status/<session_id>', methods=['GET'])
def get_transcript_status(session_id):
    """Get the status of transcript processing for a session."""
    try:
        # This could be enhanced to track session status in database
        return jsonify({
            'session_id': session_id,
            'status': 'active',
            'segments_processed': 0,
            'last_activity': None
        })
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500