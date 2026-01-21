"""
Empathy Engine - Configuration Module
Handles environment variables and application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# TTS Engine Settings
USE_ELEVENLABS = os.getenv("USE_ELEVENLABS", "false").lower() == "true"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Audio Settings
AUDIO_FORMAT = os.getenv("AUDIO_FORMAT", "wav")

# Emotion Detection Model
EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"

# Emotion Colors (for frontend reference)
EMOTION_COLORS = {
    "joy": "#FFD700",
    "anger": "#FF4757",
    "sadness": "#5B7FFF",
    "fear": "#9B59B6",
    "surprise": "#00D9FF",
    "disgust": "#2ECC71",
    "neutral": "#A0A0A0"
}

# Emotion Emojis
EMOTION_EMOJIS = {
    "joy": "😊",
    "anger": "😠",
    "sadness": "😢",
    "fear": "😨",
    "surprise": "😲",
    "disgust": "🤢",
    "neutral": "😐"
}
