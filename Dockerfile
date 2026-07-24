FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
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
COPY .env .

# Create directories
RUN mkdir -p input output

# Streamlit config
RUN mkdir -p ~/.streamlit && \
    echo "[server]\nenableCORS=false\nenableXsrfProtection=false\n" > ~/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Default command - Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
