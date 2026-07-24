FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg and audio libraries for librosa
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY streamlit_app.py .
COPY cli_transcribe.py .
COPY transcriber.py .
COPY audio_processor.py .

# Create directories
RUN mkdir -p input output

# Streamlit config — subpath-aware via BASE_URL_PATH env var
RUN mkdir -p ~/.streamlit && \
    printf "[server]\nenableCORS=false\nenableXsrfProtection=false\n" > ~/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Default command — supports BASE_URL_PATH for subpath deployment (e.g. /voice-to-text)
# ponytail: shell-form CMD needed for env var expansion; switch to entrypoint script if logic grows
CMD streamlit run streamlit_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.baseUrlPath="${BASE_URL_PATH:-}"
