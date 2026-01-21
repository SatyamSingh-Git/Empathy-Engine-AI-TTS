"""
Empathy Engine - Voice Parameter Mapper
Maps detected emotions to TTS voice parameters with intensity scaling
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class VoiceParameters:
    """Voice parameters for TTS modulation"""
    rate_modifier: float  # Multiplier for speech rate (1.0 = normal)
    pitch_modifier: float  # Multiplier for pitch (1.0 = normal)
    volume_modifier: float  # Multiplier for volume (1.0 = normal)
    stability: float  # For ElevenLabs: voice stability (0-1)
    similarity_boost: float  # For ElevenLabs: similarity boost (0-1)
    style: float  # For ElevenLabs: style exaggeration (0-1)
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "rate_modifier": round(self.rate_modifier, 3),
            "pitch_modifier": round(self.pitch_modifier, 3),
            "volume_modifier": round(self.volume_modifier, 3),
            "stability": round(self.stability, 3),
            "similarity_boost": round(self.similarity_boost, 3),
            "style": round(self.style, 3)
        }


# Base voice parameters for each emotion (at 100% intensity)
EMOTION_VOICE_PROFILES = {
    "joy": {
        "rate_delta": 0.15,      # +15% faster
        "pitch_delta": 0.10,     # +10% higher pitch
        "volume_delta": 0.10,    # +10% louder
        "stability": 0.45,       # Lower stability = more expressive
        "similarity_boost": 0.75,
        "style": 0.7             # High style exaggeration
    },
    "anger": {
        "rate_delta": 0.10,      # +10% faster
        "pitch_delta": -0.05,    # -5% lower pitch
        "volume_delta": 0.20,    # +20% louder
        "stability": 0.30,       # Very expressive
        "similarity_boost": 0.80,
        "style": 0.8
    },
    "sadness": {
        "rate_delta": -0.20,     # -20% slower
        "pitch_delta": -0.15,    # -15% lower pitch
        "volume_delta": -0.15,   # -15% quieter
        "stability": 0.80,       # More stable, subdued
        "similarity_boost": 0.70,
        "style": 0.4
    },
    "fear": {
        "rate_delta": 0.20,      # +20% faster (anxious)
        "pitch_delta": 0.05,     # +5% higher (tense)
        "volume_delta": -0.05,   # Slightly quieter
        "stability": 0.35,       # Unstable, trembling
        "similarity_boost": 0.75,
        "style": 0.6
    },
    "surprise": {
        "rate_delta": 0.25,      # +25% faster
        "pitch_delta": 0.15,     # +15% higher (exclamatory)
        "volume_delta": 0.15,    # +15% louder
        "stability": 0.40,
        "similarity_boost": 0.70,
        "style": 0.8
    },
    "disgust": {
        "rate_delta": -0.10,     # -10% slower
        "pitch_delta": -0.08,    # -8% lower
        "volume_delta": 0.0,
        "stability": 0.60,
        "similarity_boost": 0.75,
        "style": 0.5
    },
    "neutral": {
        "rate_delta": 0.0,
        "pitch_delta": 0.0,
        "volume_delta": 0.0,
        "stability": 0.75,
        "similarity_boost": 0.75,
        "style": 0.0             # No style exaggeration
    }
}


def map_emotion_to_voice(emotion: str, intensity: float = 1.0) -> VoiceParameters:
    """
    Map an emotion to voice parameters with intensity scaling.
    
    Higher intensity means more pronounced voice modulation.
    
    Args:
        emotion: Detected emotion label
        intensity: Emotion intensity (0.0 - 1.0), scales the modulation
        
    Returns:
        VoiceParameters object with calculated values
    """
    # Get base profile for emotion (default to neutral)
    profile = EMOTION_VOICE_PROFILES.get(emotion, EMOTION_VOICE_PROFILES["neutral"])
    
    # Clamp intensity
    intensity = max(0.0, min(1.0, intensity))
    
    # Apply intensity scaling to deltas
    # At intensity 0, values are neutral (1.0 multipliers)
    # At intensity 1, values are fully applied
    rate_modifier = 1.0 + (profile["rate_delta"] * intensity)
    pitch_modifier = 1.0 + (profile["pitch_delta"] * intensity)
    volume_modifier = 1.0 + (profile["volume_delta"] * intensity)
    
    # For ElevenLabs parameters, interpolate towards neutral
    neutral_stability = 0.75
    neutral_similarity = 0.75
    
    stability = neutral_stability + (profile["stability"] - neutral_stability) * intensity
    similarity_boost = neutral_similarity + (profile["similarity_boost"] - neutral_similarity) * intensity
    style = profile["style"] * intensity
    
    return VoiceParameters(
        rate_modifier=rate_modifier,
        pitch_modifier=pitch_modifier,
        volume_modifier=volume_modifier,
        stability=stability,
        similarity_boost=similarity_boost,
        style=style
    )


def get_pyttsx3_params(voice_params: VoiceParameters, base_rate: int = 175) -> Dict[str, Any]:
    """
    Convert VoiceParameters to pyttsx3-specific settings.
    
    Args:
        voice_params: VoiceParameters object
        base_rate: Base speech rate in words per minute
        
    Returns:
        Dictionary with pyttsx3 property settings
    """
    return {
        "rate": int(base_rate * voice_params.rate_modifier),
        "volume": max(0.0, min(1.0, voice_params.volume_modifier)),
        # Note: pyttsx3 pitch control is limited and platform-dependent
        # We'll use the pitch_modifier as a reference for feedback
        "pitch_modifier": voice_params.pitch_modifier
    }


def get_elevenlabs_params(voice_params: VoiceParameters) -> Dict[str, Any]:
    """
    Convert VoiceParameters to ElevenLabs API voice settings.
    
    Args:
        voice_params: VoiceParameters object
        
    Returns:
        Dictionary with ElevenLabs voice settings
    """
    return {
        "stability": voice_params.stability,
        "similarity_boost": voice_params.similarity_boost,
        "style": voice_params.style,
        "use_speaker_boost": True
    }


def describe_voice_changes(emotion: str, voice_params: VoiceParameters) -> str:
    """
    Generate a human-readable description of voice changes.
    
    Args:
        emotion: Detected emotion
        voice_params: Applied voice parameters
        
    Returns:
        Description string
    """
    changes = []
    
    rate_change = (voice_params.rate_modifier - 1.0) * 100
    if abs(rate_change) > 1:
        direction = "faster" if rate_change > 0 else "slower"
        changes.append(f"Rate: {abs(rate_change):.0f}% {direction}")
    
    pitch_change = (voice_params.pitch_modifier - 1.0) * 100
    if abs(pitch_change) > 1:
        direction = "higher" if pitch_change > 0 else "lower"
        changes.append(f"Pitch: {abs(pitch_change):.0f}% {direction}")
    
    volume_change = (voice_params.volume_modifier - 1.0) * 100
    if abs(volume_change) > 1:
        direction = "louder" if volume_change > 0 else "softer"
        changes.append(f"Volume: {abs(volume_change):.0f}% {direction}")
    
    if not changes:
        return "No voice modulation (neutral)"
    
    return " | ".join(changes)


# Test function
if __name__ == "__main__":
    test_emotions = [
        ("joy", 0.95),
        ("anger", 0.80),
        ("sadness", 0.70),
        ("neutral", 0.90),
        ("surprise", 0.85),
        ("joy", 0.30),  # Low intensity joy
    ]
    
    print("Testing Voice Parameter Mapper")
    print("=" * 60)
    
    for emotion, intensity in test_emotions:
        params = map_emotion_to_voice(emotion, intensity)
        description = describe_voice_changes(emotion, params)
        
        print(f"\nEmotion: {emotion} (intensity: {intensity:.0%})")
        print(f"  {description}")
        print(f"  Rate: {params.rate_modifier:.2f}x | Pitch: {params.pitch_modifier:.2f}x | Volume: {params.volume_modifier:.2f}x")
