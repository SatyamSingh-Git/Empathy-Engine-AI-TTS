"""
Empathy Engine - Emotion Detection Module
Uses Hugging Face transformers for 7-emotion classification with intensity scoring
"""

from transformers import pipeline
from functools import lru_cache
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Emotion labels from the model
EMOTION_LABELS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]


@lru_cache(maxsize=1)
def get_emotion_classifier():
    """
    Lazy-load and cache the emotion classification model.
    Uses j-hartmann/emotion-english-distilroberta-base for 7 emotions.
    """
    logger.info("Loading emotion classification model...")
    try:
        classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,  # Return all emotion scores
            device=-1  # Use CPU (change to 0 for GPU)
        )
        logger.info("Emotion model loaded successfully!")
        return classifier
    except Exception as e:
        logger.error(f"Failed to load emotion model: {e}")
        raise


def detect_emotion(text: str) -> Dict[str, Any]:
    """
    Analyze the input text and classify it into emotional categories.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary containing:
        - label: Primary emotion detected (str)
        - confidence: Confidence score for primary emotion (float 0-1)
        - all_scores: Dictionary of all emotion scores
        - intensity: Scaled intensity for voice modulation (float 0-1)
    """
    if not text or not text.strip():
        return {
            "label": "neutral",
            "confidence": 1.0,
            "all_scores": {label: 0.0 for label in EMOTION_LABELS},
            "intensity": 0.0
        }
    
    # Get classifier
    classifier = get_emotion_classifier()
    
    # Run classification
    try:
        results = classifier(text[:512])  # Limit text length for model
        
        # Parse results - model returns list of dicts with 'label' and 'score'
        if results and len(results) > 0:
            scores_list = results[0] if isinstance(results[0], list) else results
            
            # Convert to dictionary
            all_scores = {item['label']: item['score'] for item in scores_list}
            
            # Find primary emotion (highest score)
            primary_emotion = max(all_scores, key=all_scores.get)
            confidence = all_scores[primary_emotion]
            
            # Calculate intensity based on confidence and how much it differs from neutral
            neutral_score = all_scores.get('neutral', 0)
            intensity = min(1.0, confidence * (1 - neutral_score * 0.5))
            
            return {
                "label": primary_emotion,
                "confidence": round(confidence, 4),
                "all_scores": {k: round(v, 4) for k, v in all_scores.items()},
                "intensity": round(intensity, 4)
            }
    except Exception as e:
        logger.error(f"Emotion detection failed: {e}")
    
    # Fallback to neutral
    return {
        "label": "neutral",
        "confidence": 1.0,
        "all_scores": {label: 0.0 for label in EMOTION_LABELS},
        "intensity": 0.0
    }


def get_emotion_info(emotion: str) -> Dict[str, str]:
    """
    Get display information for an emotion.
    
    Args:
        emotion: Emotion label
        
    Returns:
        Dictionary with emoji and color for the emotion
    """
    EMOTION_INFO = {
        "joy": {"emoji": "😊", "color": "#FFD700", "name": "Joy"},
        "anger": {"emoji": "😠", "color": "#FF4757", "name": "Anger"},
        "sadness": {"emoji": "😢", "color": "#5B7FFF", "name": "Sadness"},
        "fear": {"emoji": "😨", "color": "#9B59B6", "name": "Fear"},
        "surprise": {"emoji": "😲", "color": "#00D9FF", "name": "Surprise"},
        "disgust": {"emoji": "🤢", "color": "#2ECC71", "name": "Disgust"},
        "neutral": {"emoji": "😐", "color": "#A0A0A0", "name": "Neutral"}
    }
    
    return EMOTION_INFO.get(emotion, EMOTION_INFO["neutral"])


# Test function
if __name__ == "__main__":
    test_texts = [
        "I'm so excited about this news! This is the best day ever!",
        "This is terrible, I'm so frustrated and angry!",
        "I feel so sad and lonely today...",
        "The meeting is scheduled for 3 PM tomorrow.",
        "Oh wow, I can't believe this happened!",
        "That's disgusting, I can't stand it.",
        "I'm really scared about what might happen."
    ]
    
    print("Testing Emotion Detection Module")
    print("=" * 50)
    
    for text in test_texts:
        result = detect_emotion(text)
        info = get_emotion_info(result["label"])
        print(f"\nText: {text[:50]}...")
        print(f"  Emotion: {info['emoji']} {result['label']} ({result['confidence']:.0%})")
        print(f"  Intensity: {result['intensity']:.0%}")
