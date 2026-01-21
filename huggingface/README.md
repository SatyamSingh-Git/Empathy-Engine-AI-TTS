---
title: The Empathy Engine
emoji: 🎭
colorFrom: purple
colorTo: pink
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🎭 The Empathy Engine

An AI-powered Text-to-Speech system that detects emotions and generates expressive voice with appropriate tone, pace, and emphasis.

## Features
- 🧠 **Emotion Detection** - Analyzes text for 7 emotions (joy, anger, sadness, fear, surprise, disgust, neutral)
- 🗣️ **Expressive TTS** - Uses Coqui XTTS v2 for natural, emotion-aware speech
- ✏️ **Smart Punctuation** - Enhances text with emotion-appropriate punctuation

## How to Use
1. Enter your text in the input box
2. Click "Generate Speech"
3. Listen to the emotion-aware voice output!

## Technology
- **Emotion Detection**: DistilRoBERTa fine-tuned for emotions
- **Text-to-Speech**: Coqui XTTS v2
- **Framework**: Gradio + Python
