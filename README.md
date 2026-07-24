# Voice-to-Text Transcriber

Aplikasi sederhana untuk transkrip file audio menggunakan OpenAI Audio Transcription API.

## Features
- Upload file audio via UI Streamlit
- Pilih model transcription (gpt-4o-transcribe, gpt-4o-transcribe-diarize, whisper-1)
- Pilih output format (TXT, JSON, SRT, VTT)
- Auto-chunking untuk file >25MB
- Download hasil transkrip langsung

## Requirements
- Python 3.11+
- OpenAI API Key
- FFmpeg (untuk pydub)

## Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup OpenAI API Key
Copy `.env.example` ke `.env` dan isi API key Anda:
```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-proj-xxxxx...
```

### 3. Install FFmpeg (Windows)
Download dari https://ffmpeg.org/download.html atau pakai:
```bash
# Pakai chocolatey
choco install ffmpeg
```

## Usage

### Streamlit UI
```bash
streamlit run streamlit_app.py
```
Buka browser ke `http://localhost:8501`

### CLI Script
```bash
python cli_transcribe.py input/audio.mp3
```

## Supported Audio Formats
- MP3, MP4, MPEG, MPGA, M4A, WAV, WebM
- Max file size: 25MB per chunk

## Models

### gpt-4o-transcribe (Default - Recommended)
- Kualitas transkrip terbaik
- Output: text, json

### gpt-4o-transcribe-diarize
- Untuk audio dengan multiple speakers
- Output: text, json (dengan speaker metadata)

### whisper-1
- Dukungan format lebih lengkap
- Output: text, json, srt, vtt, verbose_json

## Project Structure
```
├── input/                    # Upload audio files
├── output/                   # Hasil transkrip
├── streamlit_app.py          # Web UI
├── cli_transcribe.py         # CLI interface
├── transcriber.py            # OpenAI API logic
├── audio_processor.py        # Audio handling
├── requirements.txt
├── .env
└── .env.example
```
