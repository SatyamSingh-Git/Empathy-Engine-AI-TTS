/**
 * The Empathy Engine - Real-time Audio Waveform Visualizer
 * Uses Web Audio API for frequency analysis and Canvas for smooth rendering
 */

class WaveformVisualizer {
    constructor(canvasId, audioElement) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.audio = audioElement;
        this.audioContext = null;
        this.analyser = null;
        this.source = null;
        this.isInitialized = false;
        this.isPlaying = false;
        this.animationId = null;
        this.sourceConnected = false;

        // Visualization settings
        this.barCount = 64;
        this.barGap = 2;
        this.emotionColor = '#667eea';

        // Initialize canvas size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // Draw initial idle state
        this.drawIdle();

        // Set up audio context on first user interaction
        document.addEventListener('click', () => this.initAudio(), { once: true });
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        if (container) {
            this.canvas.width = container.clientWidth || 400;
            this.canvas.height = container.clientHeight || 80;
        }
        if (!this.isPlaying) {
            this.drawIdle();
        }
    }

    initAudio() {
        if (this.sourceConnected) return;

        try {
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

            // Create analyser
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 128;
            this.analyser.smoothingTimeConstant = 0.8;

            // Connect audio element to analyser (this can only be done ONCE)
            this.source = this.audioContext.createMediaElementSource(this.audio);
            this.source.connect(this.analyser);
            this.analyser.connect(this.audioContext.destination);

            this.sourceConnected = true;
            this.isInitialized = true;
            console.log('✅ Audio visualizer initialized');
        } catch (error) {
            if (error.name === 'InvalidStateError') {
                // Source already connected - that's fine
                this.sourceConnected = true;
                this.isInitialized = true;
                console.log('Audio source already connected');
            } else {
                console.error('Waveform init error:', error);
            }
        }
    }

    setEmotionColor(color) {
        this.emotionColor = color;
    }

    start() {
        // Try to initialize if not done
        if (!this.isInitialized) {
            this.initAudio();
        }

        // Resume audio context if suspended
        if (this.audioContext && this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }

        this.isPlaying = true;
        this.animate();
    }

    stop() {
        this.isPlaying = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        // Small delay to let last frame finish
        setTimeout(() => this.drawIdle(), 100);
    }

    animate() {
        if (!this.isPlaying) return;

        this.animationId = requestAnimationFrame(() => this.animate());

        // Only draw if analyser is ready
        if (this.analyser && this.sourceConnected) {
            this.drawBars();
        } else {
            // Fallback: draw simulated animation
            this.drawSimulatedBars();
        }
    }

    drawBars() {
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.analyser.getByteFrequencyData(dataArray);

        const { width, height } = this.canvas;
        this.ctx.clearRect(0, 0, width, height);

        const barWidth = (width - (this.barCount - 1) * this.barGap) / this.barCount;
        const step = Math.max(1, Math.floor(bufferLength / this.barCount));

        // Create gradient
        const gradient = this.ctx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, this.emotionColor);
        gradient.addColorStop(0.5, this.adjustBrightness(this.emotionColor, 30));
        gradient.addColorStop(1, this.adjustBrightness(this.emotionColor, 60));

        for (let i = 0; i < this.barCount; i++) {
            // Get average value for this bar
            let sum = 0;
            for (let j = 0; j < step; j++) {
                const idx = i * step + j;
                if (idx < bufferLength) {
                    sum += dataArray[idx];
                }
            }
            const average = sum / step;

            // Calculate bar height
            const barHeight = Math.max(4, (average / 255) * height * 0.9);
            const x = i * (barWidth + this.barGap);
            const y = height - barHeight;

            // Draw bar
            this.ctx.fillStyle = gradient;
            this.ctx.shadowColor = this.emotionColor;
            this.ctx.shadowBlur = 8;
            this.roundRect(x, y, barWidth, barHeight, 2);
            this.ctx.fill();
        }

        this.ctx.shadowBlur = 0;
    }

    drawSimulatedBars() {
        // Fallback animation when Web Audio API fails
        const { width, height } = this.canvas;
        this.ctx.clearRect(0, 0, width, height);

        const barWidth = (width - (this.barCount - 1) * this.barGap) / this.barCount;
        const time = Date.now() / 100;

        const gradient = this.ctx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, this.emotionColor);
        gradient.addColorStop(1, this.adjustBrightness(this.emotionColor, 50));

        for (let i = 0; i < this.barCount; i++) {
            // Create wave-like animation
            const wave = Math.sin(time + i * 0.2) * 0.5 + 0.5;
            const wave2 = Math.sin(time * 1.5 + i * 0.3) * 0.3 + 0.3;
            const barHeight = Math.max(4, (wave * wave2) * height * 0.7);
            const x = i * (barWidth + this.barGap);
            const y = height - barHeight;

            this.ctx.fillStyle = gradient;
            this.ctx.shadowColor = this.emotionColor;
            this.ctx.shadowBlur = 6;
            this.roundRect(x, y, barWidth, barHeight, 2);
            this.ctx.fill();
        }

        this.ctx.shadowBlur = 0;
    }

    drawIdle() {
        const { width, height } = this.canvas;
        this.ctx.clearRect(0, 0, width, height);

        const barWidth = (width - (this.barCount - 1) * this.barGap) / this.barCount;

        for (let i = 0; i < this.barCount; i++) {
            const idleHeight = 4 + Math.sin(i * 0.3) * 2;
            const x = i * (barWidth + this.barGap);
            const y = height - idleHeight;

            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
            this.roundRect(x, y, barWidth, idleHeight, 2);
            this.ctx.fill();
        }
    }

    roundRect(x, y, w, h, radius) {
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius, y);
        this.ctx.lineTo(x + w - radius, y);
        this.ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
        this.ctx.lineTo(x + w, y + h - radius);
        this.ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
        this.ctx.lineTo(x + radius, y + h);
        this.ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
        this.ctx.lineTo(x, y + radius);
        this.ctx.quadraticCurveTo(x, y, x + radius, y);
        this.ctx.closePath();
    }

    adjustBrightness(color, percent) {
        let hex = color.replace('#', '');
        if (hex.length === 3) {
            hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
        }

        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);

        const adjust = (val) => Math.min(255, Math.max(0, val + Math.round(val * (percent / 100))));

        const newR = adjust(r).toString(16).padStart(2, '0');
        const newG = adjust(g).toString(16).padStart(2, '0');
        const newB = adjust(b).toString(16).padStart(2, '0');

        return `#${newR}${newG}${newB}`;
    }
}

// Export for use in app.js
window.WaveformVisualizer = WaveformVisualizer;
