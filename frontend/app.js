/**
 * The Empathy Engine - Main Application JavaScript
 * Handles UI interactions, API calls, and audio playback
 */

// ============== DOM Elements ==============
const textInput = document.getElementById('text-input');
const charCount = document.getElementById('char-count');
const generateBtn = document.getElementById('generate-btn');
const resultsSection = document.getElementById('results-section');
const audioElement = document.getElementById('audio-element');

// Emotion Panel
const emotionEmoji = document.getElementById('emotion-emoji');
const emotionName = document.getElementById('emotion-name');
const confidenceFill = document.getElementById('confidence-fill');
const confidenceText = document.getElementById('confidence-text');
const paramRate = document.getElementById('param-rate');
const paramPitch = document.getElementById('param-pitch');
const paramVolume = document.getElementById('param-volume');

// Audio Player
const playBtn = document.getElementById('play-btn');
const progressBar = document.getElementById('progress-bar');
const progressFill = document.getElementById('progress-fill');
const currentTimeEl = document.getElementById('current-time');
const durationEl = document.getElementById('duration');
const downloadBtn = document.getElementById('download-btn');
const shareBtn = document.getElementById('share-btn');

// Audio Effects
const pitchSlider = document.getElementById('pitch-slider');
const pitchValue = document.getElementById('pitch-value');
const reverbSlider = document.getElementById('reverb-slider');
const reverbValue = document.getElementById('reverb-value');

// Voice Toggle
const voiceBtns = document.querySelectorAll('.voice-btn');

// History
const historyToggle = document.getElementById('history-toggle');
const historyList = document.getElementById('history-list');

// ============== State ==============
let isPlaying = false;
let currentAudioUrl = null;
let currentAudioBase64 = null;
let visualizer = null;
let generationHistory = [];
let isGenerating = false;
let selectedModel = 'vits-emotion'; // Auto emotion-matched voice

// ============== API Configuration ==============
const API_BASE = '';

// ============== Initialization ==============
document.addEventListener('DOMContentLoaded', () => {
    // Initialize waveform visualizer
    visualizer = new WaveformVisualizer('waveform-canvas', audioElement);

    // Set up event listeners
    setupEventListeners();

    // Load history from localStorage
    loadHistory();

    console.log('🎙️ The Empathy Engine initialized');
});

// ============== Event Listeners ==============
function setupEventListeners() {
    // Text input character counter
    textInput.addEventListener('input', () => {
        charCount.textContent = textInput.value.length;
    });

    // Generate button
    generateBtn.addEventListener('click', handleGenerate);

    // Allow Ctrl+Enter to generate
    textInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            handleGenerate();
        }
    });

    // Audio player controls
    playBtn.addEventListener('click', togglePlayback);
    progressBar.addEventListener('click', seekAudio);

    // Audio element events
    audioElement.addEventListener('timeupdate', updateProgress);
    audioElement.addEventListener('loadedmetadata', updateDuration);
    audioElement.addEventListener('ended', handleAudioEnded);
    audioElement.addEventListener('play', () => {
        isPlaying = true;
        playBtn.querySelector('.play-icon').textContent = '⏸️';
        visualizer.start();
    });
    audioElement.addEventListener('pause', () => {
        isPlaying = false;
        playBtn.querySelector('.play-icon').textContent = '▶️';
        visualizer.stop();
    });

    // Download button
    downloadBtn.addEventListener('click', handleDownload);

    // Share button
    shareBtn.addEventListener('click', handleShare);

    // History toggle
    historyToggle.addEventListener('click', toggleHistory);

    // Effects sliders
    if (pitchSlider) {
        pitchSlider.addEventListener('input', () => {
            pitchValue.textContent = pitchSlider.value;
        });
    }
    if (reverbSlider) {
        reverbSlider.addEventListener('input', () => {
            reverbValue.textContent = reverbSlider.value;
        });
    }

    // Voice toggle buttons
    voiceBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            voiceBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedModel = btn.dataset.model;
            console.log(`Voice changed to: ${selectedModel}`);
        });
    });
}

// ============== Button Loading State ==============
function setButtonLoading(loading) {
    isGenerating = loading;
    generateBtn.disabled = loading;

    const btnIcon = generateBtn.querySelector('.btn-icon');
    const btnText = generateBtn.querySelector('.btn-text');

    if (loading) {
        btnIcon.textContent = '';
        btnIcon.innerHTML = '<span class="btn-spinner"></span>';
        btnText.textContent = 'Generating...';
        generateBtn.classList.add('loading');
    } else {
        btnIcon.innerHTML = '🎙️';
        btnText.textContent = 'Generate Voice';
        generateBtn.classList.remove('loading');
    }
}

// ============== Main Generate Function ==============
async function handleGenerate() {
    const text = textInput.value.trim();

    if (!text) {
        showToast('Please enter some text to synthesize', 'error');
        return;
    }

    if (isGenerating) {
        return;
    }

    // Show loading in button (not overlay)
    setButtonLoading(true);

    try {
        // Get effects values
        const pitch = pitchSlider ? parseFloat(pitchSlider.value) : 0;
        const reverb = reverbSlider ? parseFloat(reverbSlider.value) : 0;
        const applyEffects = pitch !== 0 || reverb > 0;

        const response = await fetch(`${API_BASE}/api/synthesize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text,
                model: selectedModel,
                apply_effects: applyEffects,
                pitch_shift: pitch,
                reverb_amount: reverb
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate audio');
        }

        const result = await response.json();

        // Update UI with results
        displayResults(result);

        // Add to history
        addToHistory(result);

        showToast('Voice generated successfully!', 'success');

    } catch (error) {
        console.error('Generation failed:', error);
        showToast(error.message || 'Generation failed', 'error');
    } finally {
        setButtonLoading(false);
    }
}

// ============== Toast Notifications ==============
function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
        <span class="toast-message">${message}</span>
    `;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto remove
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============== Display Results ==============
function displayResults(result) {
    // Show results section
    resultsSection.classList.remove('hidden');

    // Update emotion panel
    const emotion = result.emotion;
    emotionEmoji.textContent = emotion.emoji;
    emotionEmoji.style.setProperty('--emotion-color', emotion.color);
    emotionName.textContent = emotion.name;
    emotionName.style.color = emotion.color;

    // Animate confidence bar
    const confidence = Math.round(emotion.confidence * 100);
    confidenceFill.style.width = `${confidence}%`;
    confidenceFill.style.setProperty('--emotion-color', emotion.color);
    confidenceText.textContent = `${confidence}%`;

    // Update voice parameters
    const params = result.voice_parameters;
    updateParamDisplay('param-rate', params.rate_modifier);
    updateParamDisplay('param-pitch', params.pitch_modifier);
    updateParamDisplay('param-volume', params.volume_modifier);

    // Set visualizer color
    visualizer.setEmotionColor(emotion.color);

    // Set up audio - use the server URL directly for better compatibility
    currentAudioUrl = result.audio_url;
    currentAudioBase64 = result.audio_base64;

    // Reset and set new audio source
    audioElement.pause();
    audioElement.currentTime = 0;

    // Try using server URL first (more reliable), fallback to base64
    audioElement.src = result.audio_url;

    // Add error handler to fallback to base64 if URL fails
    audioElement.onerror = function () {
        console.log('Server URL failed, using base64 fallback');
        const audioBlob = base64ToBlob(result.audio_base64, 'audio/wav');
        const audioBlobUrl = URL.createObjectURL(audioBlob);
        audioElement.src = audioBlobUrl;
        audioElement.load();
    };

    audioElement.load();

    // Auto-play when ready (with user gesture workaround)
    audioElement.oncanplaythrough = function () {
        console.log('Audio ready to play');
    };

    // Reset player UI
    progressFill.style.width = '0%';
    currentTimeEl.textContent = '0:00';
    playBtn.querySelector('.play-icon').textContent = '▶️';

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ============== Parameter Display ==============
function updateParamDisplay(elementId, modifier) {
    const element = document.getElementById(elementId);
    const change = Math.round((modifier - 1) * 100);

    if (change > 0) {
        element.textContent = `+${change}%`;
        element.className = 'param-value positive';
    } else if (change < 0) {
        element.textContent = `${change}%`;
        element.className = 'param-value negative';
    } else {
        element.textContent = '0%';
        element.className = 'param-value';
    }
}

// ============== Audio Playback ==============
function togglePlayback() {
    if (!audioElement.src) return;

    if (isPlaying) {
        audioElement.pause();
    } else {
        audioElement.play().catch(err => {
            console.error('Playback failed:', err);
            showToast('Failed to play audio', 'error');
        });
    }
}

function seekAudio(e) {
    if (!audioElement.duration) return;

    const rect = progressBar.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    audioElement.currentTime = percent * audioElement.duration;
}

function updateProgress() {
    if (!audioElement.duration) return;

    const percent = (audioElement.currentTime / audioElement.duration) * 100;
    progressFill.style.width = `${percent}%`;
    currentTimeEl.textContent = formatTime(audioElement.currentTime);
}

function updateDuration() {
    durationEl.textContent = formatTime(audioElement.duration);
}

function handleAudioEnded() {
    isPlaying = false;
    playBtn.querySelector('.play-icon').textContent = '▶️';
    progressFill.style.width = '0%';
    currentTimeEl.textContent = '0:00';
    visualizer.stop();
}

// ============== Download & Share ==============
function handleDownload() {
    if (!currentAudioBase64) return;

    const blob = base64ToBlob(currentAudioBase64, 'audio/mpeg');
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `empathy_engine_${Date.now()}.mp3`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Audio downloaded!', 'success');
}

async function handleShare() {
    if (!currentAudioBase64) return;

    if (navigator.share) {
        try {
            const blob = base64ToBlob(currentAudioBase64, 'audio/mpeg');
            const file = new File([blob], 'empathy_engine_audio.mp3', { type: 'audio/mpeg' });

            await navigator.share({
                title: 'The Empathy Engine',
                text: 'Check out this emotion-aware synthesized speech!',
                files: [file]
            });
        } catch (err) {
            if (err.name !== 'AbortError') {
                copyToClipboard(window.location.href);
                showToast('Link copied to clipboard!', 'success');
            }
        }
    } else {
        copyToClipboard(window.location.href);
        showToast('Link copied to clipboard!', 'success');
    }
}

// ============== History ==============
function toggleHistory() {
    historyToggle.classList.toggle('expanded');
    historyList.classList.toggle('collapsed');
}

function addToHistory(result) {
    const item = {
        id: Date.now(),
        text: result.text,
        emotion: result.emotion,
        audioBase64: result.audio_base64,
        timestamp: new Date().toISOString()
    };

    generationHistory.unshift(item);

    // Keep only last 10 items
    if (generationHistory.length > 10) {
        generationHistory.pop();
    }

    // Save to localStorage
    saveHistory();

    // Update UI
    renderHistory();
}

function renderHistory() {
    if (generationHistory.length === 0) {
        historyList.innerHTML = '<p class="empty-history">No generations yet. Try creating one above!</p>';
        return;
    }

    historyList.innerHTML = generationHistory.map(item => `
        <div class="history-item" data-id="${item.id}" onclick="playHistoryItem(${item.id})">
            <span class="history-emoji">${item.emotion.emoji}</span>
            <span class="history-text">${escapeHtml(item.text)}</span>
            <span class="history-play">▶️</span>
        </div>
    `).join('');
}

function playHistoryItem(id) {
    const item = generationHistory.find(h => h.id === id);
    if (!item || !item.audioBase64) {
        showToast('Audio not available for this item', 'error');
        return;
    }

    // Set up audio
    const audioBlob = base64ToBlob(item.audioBase64, 'audio/mpeg');
    const audioBlobUrl = URL.createObjectURL(audioBlob);
    audioElement.src = audioBlobUrl;

    // Update emotion display
    emotionEmoji.textContent = item.emotion.emoji;
    emotionEmoji.style.setProperty('--emotion-color', item.emotion.color);
    emotionName.textContent = item.emotion.name;
    visualizer.setEmotionColor(item.emotion.color);

    // Show results and play
    resultsSection.classList.remove('hidden');
    audioElement.play();
}

function saveHistory() {
    try {
        // Save with audio data for replay
        localStorage.setItem('empathyEngineHistory', JSON.stringify(generationHistory));
    } catch (err) {
        console.warn('Failed to save history:', err);
        // If storage is full, save without audio
        try {
            const lightHistory = generationHistory.map(h => ({
                id: h.id,
                text: h.text,
                emotion: h.emotion,
                timestamp: h.timestamp
            }));
            localStorage.setItem('empathyEngineHistory', JSON.stringify(lightHistory));
        } catch (e) {
            console.warn('Failed to save light history:', e);
        }
    }
}

function loadHistory() {
    try {
        const saved = localStorage.getItem('empathyEngineHistory');
        if (saved) {
            generationHistory = JSON.parse(saved);
            renderHistory();
        }
    } catch (err) {
        console.warn('Failed to load history:', err);
    }
}

// ============== Utility Functions ==============
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).catch(err => {
        console.error('Failed to copy:', err);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make playHistoryItem available globally
window.playHistoryItem = playHistoryItem;
