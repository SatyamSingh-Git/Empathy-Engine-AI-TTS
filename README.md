---
title: Empathy Engine
emoji: 🎙️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
short_description: AI TTS that modulates voice based on emotion (VITS/XTTS)
---

# 🎙️ The Empathy Engine

> **Giving AI a Human Voice** — Bridging the gap between robotic text and emotional expression.

[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-md.svg)](https://huggingface.co/spaces/Automate-GPT/Empathy-Engine-AI-TTS-Generator)

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

---

## 🌟 Vision & Context

In the rapidly evolving world of AI, text generation has mastered the "what," but voice synthesis often struggles with the "how." Standard Text-to-Speech (TTS) systems are functional yet frequently robotic, lacking the prosody and emotional nuance that define human connection.

**The Empathy Engine** solves this by dynamically modulating vocal characteristics—pitch, speed, and pausing—based on the *detected emotion* of the text. Whether it's the breathless speed of **Joy**, the slow heaviness of **Sadness**, or the sharp intensity of **Anger**, this engine ensures the voice matches the message.

---

## ✨ Key Features

### 🧠 Advanced Emotion Intelligence
*   **7-Emotion Granularity**: Goes beyond simple positive/negative analysis to detect **Joy, Anger, Fear, Sadness, Surprise, Disgust,** and **Neutral**.
*   **Hugging Face Transformers**: Powered by the `j-hartmann/emotion-english-distilroberta-base` model for state-of-the-art accuracy.
*   **Intensity Scaling**: The system calculates an "intensity score" based on prediction confidence, scaling the vocal changes accordingly (e.g., "somewhat happy" vs. "ecstatic").

### 🎨 UI Showcase

<div align="center">
  <img src="frontend/UI_images/image 1.png" alt="Empathy Engine UI - Main Interface" width="800"/>
  <p><em>The Glassmorphic Main Interface</em></p>
  
  <img src="frontend/UI_images/image 2.png" alt="Empathy Engine UI - Waveform" width="45%" /> 
  <img src="frontend/UI_images/image 3.png" alt="Empathy Engine UI - Controls" width="45%" />
  <p><em>Real-time Visualizer & Emotion Controls</em></p>
</div>

### 🗣️ Dynamic Voice Synthesis

#### VITS Emotion-to-Speaker Mapping
We don't just change speed; we utilize specific **VCTK Speaker IDs** to match the character of the voice to the emotion:

| Emotion | VCTK Speaker | Character Traits | Modifiers |
| :--- | :--- | :--- | :--- |
| **😊 Joy** | `p226` | Bright, energetic female | 1.0x Speed (Standard) |
| **😠 Anger** | `p225` | Lower pitch, forceful | 1.05x Speed (Intense) |
| **😢 Sadness** | `p229` | Deep, resonant, slower | 0.75x Speed (Heavy) |
| **😨 Fear** | `p231` | Tense, slightly higher | 1.0x Speed (Anxious) |
| **😲 Surprise** | `p226` | Sharp attack | 1.0x Speed (Startled) |
| **🤢 Disgust** | `p228` | Aversive, restrained | 0.9x Speed (Slow) |
| **😐 Neutral** | `p230` | Balanced, clear | 0.9x Speed (Measured) |


### 🚀 Hybrid Model Architecture
*   **Auto (Emotion)**: The default smart mode using local neural rendering.
*   **XTTS v2 Support**: Integrated support for state-of-the-art Voice Cloning (XTTS v2) for highly realistic, consistent character voices.
*   **Cloud Fallback**: Seamless integration with **ElevenLabs** for production-grade, ultra-premium audio when an API key is provided.

### 🎨 Premium User Experience
*   **Glassmorphic UI**: A stunning, modern interface featuring frosted glass effects, dynamic gradients, and smooth transitions.
*   **Real-Time Visualizer**: A Web Audio API-powered frequency visualizer that reacts instantly to the speech.
*   **Instant Analysis**: "Analyze Only" mode to preview emotion detection without generating audio.

---

## 🏗️ System Architecture

The Empathy Engine is built on a modular, asynchronous architecture designed for performance and extensibility.

```mermaid
graph TD
    User[User / Client] -->|HTTP POST| API[FastAPI Backend]
    
    subgraph "The Empathy Engine"
        API --> Processor[Text Processor]
        
        Processor -->|Clean Text| Classifier[Emotion Classifier]
        Classifier -- DistilRoberta --> Emotion[Detected Emotion & Intensity]
        
        Emotion --> Mapper[Voice Mapper]
        Mapper -->|Params: Speed, Pitch, Speaker| Stitcher[Audio Stitcher]
        
        Processor -->|Split Sentences| Stitcher
        
        subgraph "TTS Core"
            Stitcher -->|Chunk 1| VITS[VITS Model]
            Stitcher -->|Chunk 2| XTTS[XTTS v2 Model]
            Stitcher -->|Cloud Req| Eleven[ElevenLabs API]
        end
        
        VITS -->|WAV| Mixer[Audio Mixer]
        XTTS -->|WAV| Mixer
        
        Mixer -->|Stitched Audio + Dynamic Pauses| Output[Final Audio File]
    end
    
    Output -->|Stream/File| User
```

---

## 🌊 Information Flow & Logic

How does a sentence become an emotional experience?

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant E as Emotion Model
    participant T as TTS Engine
    
    U->>A: "I can't believe you did this!"
    A->>E: Analyze Text
    E-->>A: {"label": "anger", "confidence": 0.95}
    
    Note over A, T: Mapping Logic Applied
    A->>A: Map "anger" -> Speed: 1.05x, Pause: 600ms
    
    A->>A: Split Text: ["I can't believe", "you did this!"]
    
    loop For Each Chunk
        A->>T: Synthesize(Text, Speaker="p225", Speed=1.05)
        T-->>A: Audio Chunk WAV
    end
    
    A->>A: Stitch Chunks + 600ms Silence
    A-->>U: Returns Final Audio
```

---

## 🛠️ Technology Stack

We leveraged a powerful stack to ensure low latency and high quality.

| Component | Technology | Why we chose it |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** (Python) | Async support (essential for ML), auto-docs, and high performance. |
| **Emotion Model** | **Transformers** (Hugging Face) | DistilRoberta offers the best balance of speed vs. accurate 7-emotion detection. |
| **TTS Engine** | **Coqui TTS (VITS/XTTS)** | Open-source state-of-the-art neural networks. Superior to OS-level TTS (pyttsx3). |
| **Audio Processing** | **Pydub** (FFmpeg) | Precise millisecond-level audio manipulation for our "Stitching" logic. |
| **Frontend** | **Vanilla JS + CSS3** | Lightweight, no-build-step complexity, focusing on pure performant animations. |
| **Matrix Ops** | **PyTorch** | The backbone for running both the Transformer and TTS models. |

---

## 🚀 Getting Started

### Prerequisites
*   **Python 3.10+**
*   **Visual C++ Build Tools** (for some Python audio libraries)
*   *(Optional)* NVIDIA GPU for faster XTTS rendering

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/empathy-engine.git
    cd empathy-engine
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    *Note: We pin specific versions to ensure compatibility between Transformers and XTTS.*
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

### Configuration
Create a `.env` file in the root directory:

```env
# Optional: Enable ElevenLabs for cloud fallbacks
USE_ELEVENLABS=false
ELEVENLABS_API_KEY=your_key_here

# Hardware Acceleration
USE_GPU=true
```

## 🏃‍♂️ Running the Engine

1.  **Start the Server**
    ```bash
    cd backend
    python main.py
    ```
    *The first run will download the necessary AI models (~2GB). Please be patient!*

2.  **Launch the UI**
    Open your browser to: `http://localhost:8000`

---

## 📚 API Reference

### POST `/api/synthesize`
Generates audio from text interactively.

*   **Body**: `{"text": "Hello world", "model": "xtts"}`
*   **Returns**: JSON with `audio_base64`, `emotion_data`, and `voice_metrics`.

### POST `/api/analyze`
Returns emotion data without generating audio (fast).

---

## 🧪 Improvements & Innovation

We didn't just wrap a library; we **engineered a solution**:

1.  **Dependency Harmony**: Successfully monkeypatched `torch.load` to allow modern PyTorch 2.6 to coexist with legacy XTTS checkpoints, checking a major compatibility blocker.
2.  **Audio Stitching Strategy**: Standard TTS ignores punctuation timing. We implemented a custom "Stitcher" that physically inserts silence based on emotion (long pauses for *Anger*, short for *Joy*), creating a drastically more human cadence.
3.  **Dynamic Speaker Mapping**: We don't just change pitch; we change *identities* (speakers) within the VITS dataset to best match the emotional timbre.

---

## ☁️ Deployment

### Hugging Face Spaces (Docker)

This project is ready for one-click deployment to Hugging Face Spaces using the provided `Dockerfile`.

1.  Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2.  Select **Docker** as the SDK.
3.  Upload this entire repository.
4.  (Optional) Add your `ELEVENLABS_API_KEY` in the Space **Settings > Secrets**.

The Space will automatically build and serve the application on port 7860.

---

Built for the **Empathy Engine Challenge**.
