"""
The Empathy Engine - Hugging Face Space
AI-powered emotion-aware Text-to-Speech
"""

import gradio as gr
import torch
import re
import tempfile
import os
from transformers import pipeline

# Global models (lazy loaded)
emotion_classifier = None
tts_model = None

# Emotion info mapping
EMOTION_INFO = {
    "joy": {"emoji": "😊", "color": "#FFD93D"},
    "anger": {"emoji": "😠", "color": "#FF6B6B"},
    "sadness": {"emoji": "😢", "color": "#74B9FF"},
    "fear": {"emoji": "😨", "color": "#A29BFE"},
    "surprise": {"emoji": "😲", "color": "#FFEAA7"},
    "disgust": {"emoji": "🤢", "color": "#81C784"},
    "neutral": {"emoji": "😐", "color": "#B0BEC5"},
}

# Emotion punctuation enhancement
def enhance_punctuation(text: str, emotion: str, intensity: float) -> str:
    """Enhance text punctuation based on emotion"""
    text = text.strip()
    text = re.sub(r'[.!?]+$', '', text)  # Remove existing ending
    
    if emotion == "joy":
        if intensity > 0.7:
            text += "!!"
        else:
            text += "!"
    elif emotion == "sadness":
        text += "..."
    elif emotion == "anger":
        text += "!"
    elif emotion == "fear":
        text += "..."
    elif emotion == "surprise":
        text += "?!" if any(text.lower().startswith(w) for w in ["what", "how", "why"]) else "!!"
    else:
        text += "."
    
    return text

def load_emotion_model():
    """Load emotion detection model"""
    global emotion_classifier
    if emotion_classifier is None:
        emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
            device=-1  # CPU
        )
    return emotion_classifier

def load_tts_model():
    """Load TTS model"""
    global tts_model
    if tts_model is None:
        from TTS.api import TTS
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts_model = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            progress_bar=False
        ).to(device)
    return tts_model

def detect_emotion(text: str):
    """Detect emotion from text"""
    classifier = load_emotion_model()
    results = classifier(text)[0]
    
    # Get top emotion
    top_result = max(results, key=lambda x: x['score'])
    emotion = top_result['label']
    confidence = top_result['score']
    
    return emotion, confidence

def generate_speech(text: str, speed: float = 1.0):
    """Main function: detect emotion and generate speech"""
    if not text or not text.strip():
        return None, "Please enter some text.", "", ""
    
    text = text.strip()
    
    # Step 1: Detect emotion
    emotion, confidence = detect_emotion(text)
    emotion_info = EMOTION_INFO.get(emotion, EMOTION_INFO["neutral"])
    
    # Step 2: Enhance punctuation
    intensity = min(1.0, confidence * 1.2)
    enhanced_text = enhance_punctuation(text, emotion, intensity)
    
    # Step 3: Calculate speed based on emotion
    speed_modifier = {
        "joy": 1.15,
        "anger": 1.20,
        "sadness": 0.85,
        "fear": 1.25,
        "surprise": 1.20,
        "disgust": 0.95,
        "neutral": 1.0,
    }.get(emotion, 1.0)
    
    final_speed = speed * speed_modifier
    final_speed = max(0.8, min(1.5, final_speed))
    
    # Step 4: Generate speech
    try:
        tts = load_tts_model()
        
        # Create temp file for audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name
        
        tts.tts_to_file(
            text=enhanced_text,
            file_path=output_path,
            language="en",
            speed=final_speed,
            split_sentences=True
        )
        
        # Build result
        emotion_display = f"{emotion_info['emoji']} {emotion.capitalize()} ({confidence:.0%})"
        processing_info = f"Enhanced: \"{enhanced_text}\" | Speed: {final_speed:.2f}x"
        
        return output_path, emotion_display, processing_info, ""
        
    except Exception as e:
        return None, f"Error: {str(e)}", "", str(e)

# Create Gradio interface
def create_interface():
    with gr.Blocks(
        title="The Empathy Engine",
        theme=gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="pink",
        ),
        css="""
        .emotion-display { font-size: 1.5em; font-weight: bold; }
        .gradio-container { max-width: 800px !important; }
        """
    ) as demo:
        gr.Markdown(
            """
            # 🎭 The Empathy Engine
            ### AI-Powered Emotion-Aware Text-to-Speech
            
            Enter text below and the AI will:
            1. **Detect** the emotional tone
            2. **Enhance** punctuation for expressiveness
            3. **Generate** speech with appropriate emotion
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Enter your text",
                    placeholder="Type something emotional... e.g., 'I'm so excited about this news!' or 'This is really frustrating...'",
                    lines=3,
                    max_lines=5,
                )
                
                with gr.Row():
                    speed_slider = gr.Slider(
                        minimum=0.8,
                        maximum=1.3,
                        value=1.0,
                        step=0.1,
                        label="Base Speed",
                    )
                    generate_btn = gr.Button("🎙️ Generate Speech", variant="primary", size="lg")
        
        with gr.Row():
            with gr.Column():
                emotion_output = gr.Textbox(
                    label="Detected Emotion",
                    interactive=False,
                    elem_classes=["emotion-display"]
                )
                
                processing_output = gr.Textbox(
                    label="Processing Details",
                    interactive=False,
                )
        
        audio_output = gr.Audio(
            label="Generated Speech",
            type="filepath",
        )
        
        error_output = gr.Textbox(
            label="Errors",
            visible=False,
        )
        
        # Example inputs
        gr.Examples(
            examples=[
                ["I'm so excited about this amazing news!"],
                ["This is really frustrating and I've had enough."],
                ["I miss you so much..."],
                ["What was that sound? Did you hear it?"],
                ["I can't believe this actually happened!"],
            ],
            inputs=[text_input],
        )
        
        # Connect button
        generate_btn.click(
            fn=generate_speech,
            inputs=[text_input, speed_slider],
            outputs=[audio_output, emotion_output, processing_output, error_output],
        )
        
        gr.Markdown(
            """
            ---
            **Technology**: Coqui XTTS v2 • DistilRoBERTa Emotion Detection • Gradio
            
            Made with ❤️ by The Empathy Engine Team
            """
        )
    
    return demo

# Launch
if __name__ == "__main__":
    demo = create_interface()
    demo.launch()
