"""
Audio Processor - Post-processing effects for TTS output
Provides pitch shifting, reverb, and normalization
"""

import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def process_audio(
    audio_bytes: bytes,
    pitch_shift: float = 0.0,
    reverb: float = 0.0,
    normalize: bool = True
) -> bytes:
    """
    Apply post-processing effects to audio.
    
    Args:
        audio_bytes: Raw WAV audio bytes
        pitch_shift: Semitones to shift pitch (-12 to +12)
        reverb: Reverb mix amount (0.0 to 1.0)
        normalize: Whether to normalize audio levels
        
    Returns:
        Processed audio bytes
    """
    try:
        from pydub import AudioSegment
        import numpy as np
        
        # Load audio from bytes
        audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
        
        # Apply normalization first if requested
        if normalize:
            audio = normalize_audio(audio)
        
        # Apply pitch shift if specified
        if pitch_shift != 0.0:
            audio = apply_pitch_shift(audio, pitch_shift)
        
        # Apply reverb if specified
        if reverb > 0.0:
            audio = apply_reverb(audio, reverb)
        
        # Export to bytes
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format="wav")
        return output_buffer.getvalue()
        
    except ImportError as e:
        logger.warning(f"Audio processing dependencies not available: {e}")
        return audio_bytes
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        return audio_bytes


def normalize_audio(audio) -> 'AudioSegment':
    """Normalize audio to consistent volume level"""
    from pydub import AudioSegment
    
    # Target dBFS (decibels relative to full scale)
    target_dBFS = -20.0
    
    # Calculate gain needed
    change_in_dBFS = target_dBFS - audio.dBFS
    
    # Apply gain (limit to prevent clipping)
    change_in_dBFS = max(-20, min(20, change_in_dBFS))
    
    return audio.apply_gain(change_in_dBFS)


def apply_pitch_shift(audio, semitones: float) -> 'AudioSegment':
    """
    Shift pitch by changing playback speed and resampling.
    
    Args:
        audio: AudioSegment to process
        semitones: Number of semitones to shift (-12 to +12)
    """
    from pydub import AudioSegment
    
    # Calculate rate change factor
    # Each semitone is 2^(1/12) ≈ 1.0595 times the frequency
    rate_change = 2 ** (semitones / 12.0)
    
    # Change sample rate to shift pitch
    new_sample_rate = int(audio.frame_rate * rate_change)
    
    # Create pitch-shifted audio
    shifted = audio._spawn(audio.raw_data, overrides={
        'frame_rate': new_sample_rate
    })
    
    # Resample back to original rate to maintain duration
    return shifted.set_frame_rate(audio.frame_rate)


def apply_reverb(audio, amount: float = 0.3) -> 'AudioSegment':
    """
    Apply simple reverb effect using delay-based approach.
    
    Args:
        audio: AudioSegment to process
        amount: Reverb mix (0.0 = dry, 1.0 = wet)
    """
    from pydub import AudioSegment
    
    # Clamp amount
    amount = max(0.0, min(1.0, amount))
    
    if amount == 0:
        return audio
    
    # Create multiple delayed copies for reverb effect
    delays = [
        (50, 0.4),   # 50ms delay, 40% volume
        (100, 0.25), # 100ms delay, 25% volume
        (150, 0.15), # 150ms delay, 15% volume
        (200, 0.08), # 200ms delay, 8% volume
    ]
    
    # Start with original at reduced level
    dry_level = 1.0 - (amount * 0.3)
    result = audio - (20 * (1 - dry_level))  # Reduce dry signal
    
    # Add delayed reflections
    for delay_ms, reflection_level in delays:
        # Create silent padding
        silence = AudioSegment.silent(duration=delay_ms, frame_rate=audio.frame_rate)
        
        # Calculate reflection volume
        reflection_volume = -20 * (1 - (reflection_level * amount))
        
        # Add delayed reflection
        delayed = silence + (audio + reflection_volume)
        
        # Overlay on result (trim to original length)
        result = result.overlay(delayed[:len(audio)])
    
    return result


# Emotion-based effect presets
EMOTION_EFFECTS = {
    "joy": {"pitch_shift": 0.5, "reverb": 0.1, "normalize": True},
    "anger": {"pitch_shift": -0.3, "reverb": 0.05, "normalize": True},
    "sadness": {"pitch_shift": -1.0, "reverb": 0.3, "normalize": True},
    "fear": {"pitch_shift": 0.8, "reverb": 0.4, "normalize": True},
    "surprise": {"pitch_shift": 1.5, "reverb": 0.2, "normalize": True},
    "disgust": {"pitch_shift": -0.5, "reverb": 0.1, "normalize": True},
    "neutral": {"pitch_shift": 0.0, "reverb": 0.0, "normalize": True},
}


def get_emotion_effects(emotion: str) -> dict:
    """Get effect preset for a given emotion"""
    return EMOTION_EFFECTS.get(emotion, EMOTION_EFFECTS["neutral"])
