"""
Empathy Engine - Text-to-Speech Engine
Uses VCTK VITS with emotion-specific speakers and supports XTTS v2
"""

import asyncio
import time
import base64
import logging
import re
import tempfile
import os
from pathlib import Path
from typing import Tuple, Optional, List, Dict
import torch

# --- COMPATIBILITY FIX ---
# Monkeypatch torch.load to disable weights_only=True default in Torch 2.6+
# This enables XTTS v2 to load correctly without downgrading via pip
if hasattr(torch, 'load'):
    _original_load = torch.load
    def _safe_load(*args, **kwargs):
        # Force unsafe load for XTTS compatibility
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return _original_load(*args, **kwargs)
    torch.load = _safe_load
# -------------------------

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

from config import USE_ELEVENLABS, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, OUTPUT_DIR
from voice_mapper import VoiceParameters, get_elevenlabs_params

logger = logging.getLogger(__name__)

# Emotion-specific VCTK speakers (VITS)
EMOTION_SPEAKERS = {
    "joy": {"speaker": "p226", "speed_modifier": 1.0},
    "anger": {"speaker": "p225", "speed_modifier": 1.05},
    "sadness": {"speaker": "p229", "speed_modifier": 0.75},
    "fear": {"speaker": "p231", "speed_modifier": 1.0},
    "surprise": {"speaker": "p226", "speed_modifier": 1.0},
    "disgust": {"speaker": "p228", "speed_modifier": 0.9},
    "neutral": {"speaker": "p230", "speed_modifier": 0.9},
}

# Emotion-specific pause durations (ms)
EMOTION_PAUSES = {
    "joy": 300,
    "anger": 600,
    "sadness": 400,
    "fear": 400,
    "surprise": 200,
    "disgust": 700,
    "neutral": 500,
}

# Models
DEFAULT_MODEL = "vits-emotion"
REFERENCE_AUDIO_PATH = Path("reference.wav")

def get_available_models() -> List[Dict]:
    models = [
        {
            "id": "vits-emotion",
            "name": "Auto (Emotion)",
            "description": "Dynamic emotion-matched voices (VITS)",
            "gender": "auto"
        },
        {
            "id": "xtts",
            "name": "XTTS v2 (High Quality)",
            "description": "Realistic voice cloning (Requires GPU/Good CPU)",
            "gender": "female"
        }
    ]
    
    if USE_ELEVENLABS and ELEVENLABS_API_KEY:
        models.append({
            "id": "elevenlabs",
            "name": "ElevenLabs (Cloud)",
            "description": "Premium cloud TTS provider",
            "gender": "auto"
        })
        
    return models

class TTSEngine:
    def __init__(self):
        self.use_elevenlabs = USE_ELEVENLABS and ELEVENLABS_API_KEY
        self._elevenlabs_client = None
        self._vits_tts = None
        self._xtts_tts = None
        self._device = "cuda" if os.environ.get("USE_GPU", "false").lower() == "true" else "cpu"
        
        if AudioSegment is None:
            logger.warning("pydub not installed! Pauses will be limited.")
            
        # Ensure reference audio exists for XTTS
        self._ensure_reference_audio()

    def _ensure_reference_audio(self):
        """Generates a reference audio file for XTTS if missing"""
        if not REFERENCE_AUDIO_PATH.exists():
            try:
                logger.info("Generating reference audio for XTTS...")
                tts = self._get_vits_tts()
                tts.tts_to_file(
                    text="This is a reference voice for the synthesis engine.",
                    file_path=str(REFERENCE_AUDIO_PATH),
                    speaker="p226",
                    speed=1.0
                )
                logger.info("Reference audio generated.")
            except Exception as e:
                logger.error(f"Failed to generate reference audio: {e}")

    def _get_vits_tts(self):
        if self._vits_tts is None:
            try:
                from TTS.api import TTS
                logger.info("Loading VITS model...")
                self._vits_tts = TTS("tts_models/en/vctk/vits", progress_bar=False)
                self._vits_tts.to("cpu") # Keep VITS on CPU usually is fine
            except Exception as e:
                logger.error(f"Failed to load VITS: {e}")
                raise
        return self._vits_tts

    def _get_xtts_tts(self):
        if self._xtts_tts is None:
            try:
                from TTS.api import TTS
                logger.info("Loading XTTS v2 model...")
                # Use specific XTTS model
                self._xtts_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
                self._xtts_tts.to(self._device)
                logger.info("✅ XTTS v2 loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load XTTS v2: {e}")
                logger.error("Check versions: pip install transformers==4.44.2 torch==2.4.0 torchaudio==2.4.0")
                self._xtts_tts = None
                raise # Re-raise to be handled by caller or allow fallback
        return self._xtts_tts

    def _get_elevenlabs_client(self):
        if self._elevenlabs_client is None and ELEVENLABS_API_KEY:
            try:
                from elevenlabs.client import ElevenLabs
                self._elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            except: pass
        return self._elevenlabs_client

    async def synthesize_async(self, text, voice_params, filename=None, emotion="neutral", model=None, **kwargs):
        if not filename:
            filename = f"audio_{int(time.time() * 1000)}.wav"
        output_path = OUTPUT_DIR / filename
        model_key = model or DEFAULT_MODEL

        # Prioritize explicit model selection
        if model_key == "elevenlabs" or (model_key is None and self.use_elevenlabs):
             try:
                await self._synthesize_elevenlabs_async(text, voice_params, output_path)
                return str(output_path), output_path.read_bytes()
             except Exception as e:
                logger.warning(f"ElevenLabs failed, falling back to local: {e}")
                # Fallback to default local model logic loop below

        # Internal Stitching Engine (VITS / XTTS)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            self._synthesize_stitched, 
            text, voice_params, output_path, emotion, model_key
        )
        return str(output_path), output_path.read_bytes()

    def _synthesize_stitched(self, text, voice_params, output_path, emotion, model_key):
        """Common stitching logic for both VITS and XTTS"""
        chunks = self._split_text(text)
        combined = AudioSegment.empty() if AudioSegment else None
        pause_ms = EMOTION_PAUSES.get(emotion, 500)
        silence = AudioSegment.silent(duration=pause_ms) if AudioSegment else None

        # Fallback if no pydub
        if not combined:
             self._synthesize_chunk(text, output_path, emotion, model_key, voice_params)
             return

        with tempfile.TemporaryDirectory() as temp_dir:
            for i, chunk in enumerate(chunks):
                chunk_path = Path(temp_dir) / f"chunk_{i}.wav"
                try:
                    self._synthesize_chunk(chunk, chunk_path, emotion, model_key, voice_params)
                    if chunk_path.exists():
                        segment = AudioSegment.from_wav(str(chunk_path))
                        combined += segment
                        if i < len(chunks) - 1:
                            combined += silence
                except Exception as e:
                    logger.error(f"Chunk failed: {e}")
        
        combined.export(str(output_path), format="wav")

    def _split_text(self, text):
        return [s.strip() for s in re.split(r'([.?!]+|…|—|\.\.\.)', text) if s.strip() and not re.match(r'^([.?!]+|…|—|\.\.\.)$', s.strip())]

    def _synthesize_chunk(self, text, output_path, emotion, model_key, voice_params):
        """Dispatches to correct model generator"""
        if model_key == "xtts":
            self._generate_xtts(text, output_path, voice_params)
        else:
            self._generate_vits(text, output_path, emotion, voice_params)

    def _generate_vits(self, text, output_path, emotion, voice_params):
        tts = self._get_vits_tts()
        conf = EMOTION_SPEAKERS.get(emotion, EMOTION_SPEAKERS["neutral"])
        speed = conf["speed_modifier"] * voice_params.rate_modifier
        tts.tts_to_file(text=text, file_path=str(output_path), speaker=conf["speaker"], speed=speed)

    def _generate_xtts(self, text, output_path, voice_params):
        tts = self._get_xtts_tts()
        # XTTS doesn't support 'speed' param in tts_to_file usually, 
        # but we can try passing it or just ignore speed modulation for XTTS (it's hard to control)
        # We need reference audio
        if not REFERENCE_AUDIO_PATH.exists():
            self._ensure_reference_audio()
            
        tts.tts_to_file(
            text=text,
            file_path=str(output_path),
            speaker_wav=str(REFERENCE_AUDIO_PATH),
            language="en"
        )

    async def _synthesize_elevenlabs_async(self, text, voice_params, output_path):
        client = self._get_elevenlabs_client()
        if not client: raise Exception("No client")
        # ... (Same ElevenLabs logic as before) ...
        # (Simplified for brevity, assuming previous logic was fine)
        # Re-implementing minimal needed:
        from elevenlabs import VoiceSettings
        el_params = get_elevenlabs_params(voice_params)
        audio = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM",
            text=text,
            model_id="eleven_turbo_v2_5",
            voice_settings=VoiceSettings(**el_params)
        )
        output_path.write_bytes(b''.join(audio))

    def get_audio_base64(self, audio_bytes):
        return base64.b64encode(audio_bytes).decode('utf-8')

# Singleton
_tts_engine = None
def get_tts_engine():
    global _tts_engine
    if not _tts_engine: _tts_engine = TTSEngine()
    return _tts_engine
