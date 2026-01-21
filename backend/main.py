"""
The Empathy Engine - FastAPI Backend
Main application with API endpoints for emotion-aware text-to-speech
"""

import os
import signal
import sys
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import HOST, PORT, DEBUG, OUTPUT_DIR, EMOTION_COLORS, EMOTION_EMOJIS
from emotion_detector import detect_emotion, get_emotion_info
from voice_mapper import map_emotion_to_voice, describe_voice_changes
from tts_engine import get_tts_engine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    logger.info("👋 Received shutdown signal, exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting The Empathy Engine...")
    
    # Pre-load the emotion model on startup
    logger.info("Pre-loading emotion detection model...")
    try:
        detect_emotion("Warming up the engine!")
        logger.info("✅ Emotion model loaded successfully!")
    except Exception as e:
        logger.warning(f"⚠️ Could not pre-load emotion model: {e}")
    
    yield
    
    logger.info("👋 Shutting down The Empathy Engine...")


# Create FastAPI app
app = FastAPI(
    title="The Empathy Engine",
    description="AI service that dynamically modulates synthesized speech based on detected text emotion",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ============== Pydantic Models ==============

class SynthesizeRequest(BaseModel):
    """Request model for speech synthesis"""
    text: str = Field(..., min_length=1, max_length=1000, description="Text to synthesize")
    model: Optional[str] = Field(None, description="TTS model ID (vits-female, vits-male)")
    voice_id: Optional[str] = Field(None, description="Optional ElevenLabs voice ID")
    apply_effects: Optional[bool] = Field(False, description="Apply audio post-processing")
    pitch_shift: Optional[float] = Field(0.0, description="Pitch shift in semitones")
    reverb_amount: Optional[float] = Field(0.0, description="Reverb amount 0-1")


class EmotionResult(BaseModel):
    """Emotion detection result"""
    label: str
    confidence: float
    all_scores: dict
    intensity: float
    emoji: str
    color: str
    name: str


class VoiceParamsResult(BaseModel):
    """Voice parameters applied"""
    rate_modifier: float
    pitch_modifier: float
    volume_modifier: float
    description: str


class SynthesizeResponse(BaseModel):
    """Response model for speech synthesis"""
    success: bool
    text: str
    emotion: EmotionResult
    voice_parameters: VoiceParamsResult
    audio_url: str
    audio_base64: str


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """Serve the main frontend page"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "The Empathy Engine"}


@app.get("/api/emotions")
async def get_emotions():
    """Get list of supported emotions with their visual properties"""
    emotions = []
    for emotion in ["joy", "anger", "sadness", "fear", "surprise", "disgust", "neutral"]:
        info = get_emotion_info(emotion)
        emotions.append({
            "label": emotion,
            "emoji": info["emoji"],
            "color": info["color"],
            "name": info["name"]
        })
    return {"emotions": emotions}


@app.get("/api/models")
async def get_models():
    """Get list of available TTS models"""
    from tts_engine import get_available_models, DEFAULT_MODEL
    
    models = get_available_models()
    return {
        "models": models,
        "default": DEFAULT_MODEL
    }


@app.post("/api/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(request: SynthesizeRequest):
    """
    Main endpoint: Analyze text emotion and generate modulated speech.
    
    1. Detects emotion from input text
    2. Maps emotion to voice parameters with intensity scaling
    3. Synthesizes speech with modulated voice
    4. Returns audio and analysis results
    """
    text = request.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    logger.info(f"Processing text: {text[:50]}...")
    
    try:
        # Step 1: Detect emotion
        emotion_result = detect_emotion(text)
        emotion_info = get_emotion_info(emotion_result["label"])
        
        logger.info(f"Detected emotion: {emotion_result['label']} ({emotion_result['confidence']:.0%})")
        
        # Step 2: Map emotion to voice parameters
        voice_params = map_emotion_to_voice(
            emotion_result["label"],
            emotion_result["intensity"]
        )
        voice_description = describe_voice_changes(emotion_result["label"], voice_params)
        
        logger.info(f"Voice modulation: {voice_description}")
        
        # Step 3: Enhance punctuation for expressiveness
        from text_preprocessor import enhance_punctuation
        enhanced_text = enhance_punctuation(
            text, 
            emotion_result["label"], 
            emotion_result["intensity"]
        )
        logger.info(f"Enhanced text: {enhanced_text}")
        
        # Step 4: Synthesize speech with enhanced text and emotion
        tts_engine = get_tts_engine()
        audio_path, audio_bytes = await tts_engine.synthesize_async(
            enhanced_text,
            voice_params,
            emotion=emotion_result["label"],
            model=request.model,
            apply_effects=request.apply_effects or False,
            pitch_shift=request.pitch_shift or 0.0,
            reverb_amount=request.reverb_amount or 0.0
        )
        
        # Get relative URL for audio
        audio_filename = Path(audio_path).name
        audio_url = f"/output/{audio_filename}"
        
        # Get base64 for embedding
        audio_base64 = tts_engine.get_audio_base64(audio_bytes)
        
        logger.info(f"Generated audio: {audio_path} ({len(audio_bytes)} bytes)")
        
        # Build response
        return SynthesizeResponse(
            success=True,
            text=text,
            emotion=EmotionResult(
                label=emotion_result["label"],
                confidence=emotion_result["confidence"],
                all_scores=emotion_result["all_scores"],
                intensity=emotion_result["intensity"],
                emoji=emotion_info["emoji"],
                color=emotion_info["color"],
                name=emotion_info["name"]
            ),
            voice_parameters=VoiceParamsResult(
                rate_modifier=voice_params.rate_modifier,
                pitch_modifier=voice_params.pitch_modifier,
                volume_modifier=voice_params.volume_modifier,
                description=voice_description
            ),
            audio_url=audio_url,
            audio_base64=audio_base64
        )
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@app.post("/api/analyze")
async def analyze_emotion(request: SynthesizeRequest):
    """
    Analyze text emotion without generating audio.
    Useful for real-time emotion preview.
    """
    text = request.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        # Detect emotion
        emotion_result = detect_emotion(text)
        emotion_info = get_emotion_info(emotion_result["label"])
        
        # Map to voice parameters
        voice_params = map_emotion_to_voice(
            emotion_result["label"],
            emotion_result["intensity"]
        )
        voice_description = describe_voice_changes(emotion_result["label"], voice_params)
        
        return {
            "emotion": {
                "label": emotion_result["label"],
                "confidence": emotion_result["confidence"],
                "all_scores": emotion_result["all_scores"],
                "intensity": emotion_result["intensity"],
                "emoji": emotion_info["emoji"],
                "color": emotion_info["color"],
                "name": emotion_info["name"]
            },
            "voice_parameters": {
                "rate_modifier": voice_params.rate_modifier,
                "pitch_modifier": voice_params.pitch_modifier,
                "volume_modifier": voice_params.volume_modifier,
                "description": voice_description
            }
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============== Error Handlers ==============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."}
    )


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        ✨ THE EMPATHY ENGINE ✨                           ║
    ║        Giving AI a Human Voice                            ║
    ║                                                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║   Server starting at: http://localhost:8000               ║
    ║                                                           ║
    ║   API Docs: http://localhost:8000/docs                    ║
    ║                                                           ║
    ║   Press Ctrl+C to stop                                    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,  # Disable reload to prevent issues
        log_level="info"
    )
