"""
Empathy Engine - Text Preprocessor
Enhances punctuation based on detected emotion to improve TTS expressiveness
"""

import re
import logging

logger = logging.getLogger(__name__)


# Emotion-specific punctuation patterns
EMOTION_PUNCTUATION = {
    "joy": {
        "end_punctuation": "!",  # Enthusiastic ending
        "add_emphasis": True,
        "ellipsis_chance": 0.2,  # Occasional anticipation pauses
        "comma_to_pause": False,
    },
    "anger": {
        "end_punctuation": "!",  # Forceful ending
        "add_emphasis": True,
        "use_dashes": True,  # Add dramatic pauses
        "short_sentences": True,  # Break into shorter phrases
    },
    "sadness": {
        "end_punctuation": "...",  # Trailing off
        "add_emphasis": False,
        "use_ellipses": True,  # Hesitation
        "slow_pauses": True,
    },
    "fear": {
        "end_punctuation": "...",
        "add_emphasis": False,
        "use_dashes": True,  # Interruptions
        "short_sentences": True,
    },
    "surprise": {
        "end_punctuation": "!",
        "add_emphasis": True,
        "use_question_exclaim": True,  # "What?!" style
    },
    "disgust": {
        "end_punctuation": ".",
        "add_emphasis": False,
        "use_dashes": True,
        "contempt_pauses": True,
    },
    "neutral": {
        "end_punctuation": ".",
        "add_emphasis": False,
    },
}


def enhance_punctuation(text: str, emotion: str, intensity: float = 0.5) -> str:
    """
    Enhance text punctuation based on detected emotion.
    
    Args:
        text: Original text to enhance
        emotion: Detected emotion label
        intensity: Emotion intensity (0-1), affects how much enhancement to apply
        
    Returns:
        Enhanced text with emotion-appropriate punctuation
    """
    if not text or not text.strip():
        return text
    
    emotion = emotion.lower()
    config = EMOTION_PUNCTUATION.get(emotion, EMOTION_PUNCTUATION["neutral"])
    
    # Define pause separators based on emotion
    PAUSE_MAP = {
        "joy": "  ",          # Slight breath
        "anger": " — ",       # Dramatic pause
        "sadness": "... ",    # Long trailing pause
        "fear": "... ",       # Hesitant pause
        "surprise": "  ",     # Quick breath
        "disgust": " — ",     # Disgusted pause
        "neutral": ". ",      # Standard
    }
    
    # Split into sentences to handle them individually
    # Split by . ! ? but keep the punctuation
    sentences = re.split(r'([.!?]+)', text)
    processed_sentences = []
    
    # Iterate through chunks (text, punctuation, text, punctuation...)
    for i in range(0, len(sentences)-1, 2):
        sentence = sentences[i].strip()
        punct = sentences[i+1] if i+1 < len(sentences) else ""
        
        if not sentence:
            continue
            
        # Enhance the sentence content
        if emotion == "joy":
            sentence = _enhance_joy(sentence, intensity)
        elif emotion == "anger":
            sentence = _enhance_anger(sentence, intensity)
        elif emotion == "sadness":
            sentence = _enhance_sadness(sentence, intensity)
        elif emotion == "fear":
            sentence = _enhance_fear(sentence, intensity)
        elif emotion == "surprise":
            sentence = _enhance_surprise(sentence, intensity)
        elif emotion == "disgust":
            sentence = _enhance_disgust(sentence, intensity)
        else:
            sentence = _clean_punctuation(sentence)
            
        # Ensure it ends with punctuation if the enhancer stripped it
        if not sentence[-1] in ".!?":
            sentence += punct if punct else "."
            
        processed_sentences.append(sentence)
        
    # Handle remaining text if no punctuation split
    if len(sentences) == 1 and sentences[0].strip():
        # Single sentence case
        s = sentences[0].strip()
        if emotion == "neutral":
            s = _clean_punctuation(s)
        # ... (call other enhancers) ...
        # Simplified: just use the main logic recursively or inline
        # For safety/simplicity, just run the cleaner on the whole block if single line
        if emotion == "joy": s = _enhance_joy(s, intensity)
        elif emotion == "anger": s = _enhance_anger(s, intensity)
        elif emotion == "sadness": s = _enhance_sadness(s, intensity)
        elif emotion == "fear": s = _enhance_fear(s, intensity)
        elif emotion == "surprise": s = _enhance_surprise(s, intensity)
        elif emotion == "disgust": s = _enhance_disgust(s, intensity)
        else: s = _clean_punctuation(s)
        processed_sentences.append(s)

    # Join with emotion-specific pauses
    pause = PAUSE_MAP.get(emotion, ". ")
    enhanced = pause.join(processed_sentences)
    
    logger.debug(f"Punctuation enhanced: '{text}' -> '{enhanced}' (emotion: {emotion})")
    return enhanced


def _enhance_joy(text: str, intensity: float) -> str:
    """Add joyful punctuation - exclamations, enthusiasm"""
    # Remove existing end punctuation if plain period
    text = re.sub(r'\.+$', '', text.strip())
    
    # Add exclamation based on intensity
    if intensity > 0.7:
        text += "!!"
    elif intensity > 0.4:
        text += "!"
    else:
        text += "."
    
    # Add enthusiasm markers
    if intensity > 0.6:
        # Emphasize positive words
        positive_words = ["love", "great", "amazing", "wonderful", "happy", "excited", "fantastic"]
        for word in positive_words:
            pattern = rf'\b({word})\b'
            text = re.sub(pattern, r'\1!', text, count=1, flags=re.IGNORECASE)
    
    return text


def _enhance_anger(text: str, intensity: float) -> str:
    """Add angry punctuation - forceful, dramatic pauses"""
    text = text.strip()
    
    # Remove trailing periods
    text = re.sub(r'\.+$', '', text)
    
    # Add dramatic dashes for high intensity
    if intensity > 0.6:
        # Add pause before key negative words
        negative_words = ["never", "always", "can't", "won't", "hate", "sick", "tired"]
        for word in negative_words:
            pattern = rf'\b({word})\b'
            text = re.sub(pattern, rf'— \1', text, count=1, flags=re.IGNORECASE)
    
    # Forceful ending
    if intensity > 0.7:
        text += "!"
    elif intensity > 0.4:
        text += "!"
    else:
        text += "."
    
    # Clean up double spaces and dashes
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'—\s*—', '—', text)
    
    return text


def _enhance_sadness(text: str, intensity: float) -> str:
    """Add sad punctuation - ellipses, trailing off, hesitation"""
    text = text.strip()
    
    # Remove existing end punctuation
    text = re.sub(r'[.!?]+$', '', text)
    
    # Add hesitation with ellipses
    if intensity > 0.6:
        # Add ellipsis before sad words
        sad_words = ["lost", "gone", "never", "miss", "wish", "sorry", "alone"]
        for word in sad_words:
            pattern = rf'\b({word})\b'
            text = re.sub(pattern, rf'... \1', text, count=1, flags=re.IGNORECASE)
    
    # Trailing ending
    if intensity > 0.5:
        text += "..."
    else:
        text += "."
    
    # Clean up multiple ellipses
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text


def _enhance_fear(text: str, intensity: float) -> str:
    """Add fearful punctuation - interruptions, broken speech"""
    text = text.strip()
    
    # Remove existing end punctuation
    text = re.sub(r'[.!?]+$', '', text)
    
    # Add breaks for high intensity
    if intensity > 0.6:
        # Add dashes for interruptions
        fear_words = ["don't", "can't", "won't", "what", "please", "help", "stop"]
        for word in fear_words:
            pattern = rf'\b({word})\b'
            text = re.sub(pattern, rf'\1 —', text, count=1, flags=re.IGNORECASE)
    
    # Uncertain ending
    if intensity > 0.5:
        text += "..."
    else:
        text += "."
    
    # Clean up
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'—\s*—', '—', text)
    
    return text


def _enhance_surprise(text: str, intensity: float) -> str:
    """Add surprised punctuation - exclamations, question marks"""
    text = text.strip()
    
    # Remove existing end punctuation
    text = re.sub(r'[.!?]+$', '', text)
    
    # Check if it's a question
    is_question = any(text.lower().startswith(w) for w in ["what", "how", "why", "when", "where", "who", "is", "are", "did", "do", "can"])
    
    # Add emphatic ending
    if is_question:
        if intensity > 0.6:
            text += "?!"
        else:
            text += "?"
    else:
        if intensity > 0.6:
            text += "!!"
        else:
            text += "!"
    
    return text


def _enhance_disgust(text: str, intensity: float) -> str:
    """Add disgust punctuation - contemptuous pauses"""
    text = text.strip()
    
    # Remove existing end punctuation
    text = re.sub(r'[.!?]+$', '', text)
    
    # Add contemptuous pauses
    if intensity > 0.6:
        disgust_words = ["hate", "disgusting", "awful", "terrible", "gross", "sick"]
        for word in disgust_words:
            pattern = rf'\b({word})\b'
            text = re.sub(pattern, rf'— \1 —', text, count=1, flags=re.IGNORECASE)
    
    # Dismissive ending
    text += "."
    
    # Clean up
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'—\s*—', '—', text)
    
    return text


def _clean_punctuation(text: str) -> str:
    """Clean up punctuation for neutral emotion"""
    text = text.strip()
    
    # Ensure proper ending
    if not text[-1] in '.!?':
        text += '.'
    
    return text


# Quick test
if __name__ == "__main__":
    test_text = "I can't believe this happened"
    
    print("Original:", test_text)
    print("Joy:", enhance_punctuation(test_text, "joy", 0.8))
    print("Anger:", enhance_punctuation(test_text, "anger", 0.8))
    print("Sadness:", enhance_punctuation(test_text, "sadness", 0.8))
    print("Fear:", enhance_punctuation(test_text, "fear", 0.8))
    print("Surprise:", enhance_punctuation(test_text, "surprise", 0.8))
