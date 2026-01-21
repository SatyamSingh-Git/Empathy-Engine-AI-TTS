FROM python:3.10-slim

# 1. Create a non-root user (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user

# 2. Install system dependencies as root
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Switch to the non-root user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# 4. Install Python dependencies
COPY --chown=user backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r backend/requirements.txt

# 5. Copy application code
COPY --chown=user backend backend
COPY --chown=user frontend frontend

# 6. Create output directory (owned by user)
RUN mkdir -p output

# 7. Configuration
ENV HOST=0.0.0.0
ENV PORT=7860
ENV OUTPUT_DIR=/app/output
ENV PYTHONPATH=/app/backend

# 8. Start the app
CMD ["python", "backend/main.py"]
