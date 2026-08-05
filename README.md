# Voice-to-Text Transcriber

Simple application for transcribing audio files using the OpenAI Audio Transcription API.

## Features

- Upload audio files via the Streamlit UI
- Choose transcription model (`gpt-4o-transcribe`, `gpt-4o-transcribe-diarize`, `whisper-1`)
- Choose output format (TXT, JSON, SRT, VTT)
- Auto-chunking for files larger than 25 MB
- Download transcripts directly
- Meeting minutes generator (LLM-based, `notulen.py`)

## Requirements

- Python 3.11+
- OpenAI API Key
- FFmpeg (for pydub)

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up the OpenAI API Key

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-...
```

### 3. Install FFmpeg (Windows)

Download from https://ffmpeg.org/download.html or use:

```bash
# Via chocolatey
choco install ffmpeg
```

## Usage

### Streamlit UI

```bash
streamlit run streamlit_app.py
```

Open your browser at `http://localhost:8501`

### CLI Script

```bash
python cli_transcribe.py input/audio.mp3
```

## Docker

A `docker-compose.yml` is included:

```bash
docker compose up -d --build
```

- `transcriber` service: Streamlit app on port 8501 (subpath-aware via `BASE_URL_PATH`)
- `nginx` service (profile `nginx`): reverse proxy for subpath deployment, e.g. `http://localhost:8510/voice-to-text/`
- `transcriber-cli` service (profile `cli`): runs the CLI transcriber once for batch processing

Environment variables (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for transcription |
| `LLM_BASE_URL` | Base URL of an OpenAI-compatible LLM endpoint for the meeting-minutes generator |
| `LLM_API_KEY` | API key for that LLM endpoint |
| `LLM_MODEL` | Model name for the meeting-minutes generator |

## Supported Audio Formats

- MP3, MP4, MPEG, MPGA, M4A, WAV, WebM
- Max file size: 25 MB per chunk

## Models

### gpt-4o-transcribe (Default — Recommended)

- Best transcription quality
- Output: text, json

### gpt-4o-transcribe-diarize

- For audio with multiple speakers
- Output: text, json (with speaker metadata)

### whisper-1

- Broader format support
- Output: text, json, srt, vtt, verbose_json

## Project Structure

```
├── input/                    # Upload audio files
├── output/                   # Transcripts
├── streamlit_app.py          # Web UI
├── cli_transcribe.py         # CLI interface
├── transcriber.py            # OpenAI API logic
├── audio_processor.py        # Audio handling
├── notulen.py                # Meeting minutes generator
├── requirements.txt
├── .env
└── .env.example
```
