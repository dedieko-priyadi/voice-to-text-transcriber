# Architecture & Technical Design

## Overview

Voice-to-Text Transcriber adalah aplikasi sederhana untuk transkrip file audio menggunakan OpenAI Audio Transcription API. Dirancang dengan prinsip KISS (Keep It Simple, Stupid) untuk mudah dikelola oleh satu orang (one-man-show).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                    │
├─────────────────────────────────────────────────────┤
│  Streamlit Web UI          │  CLI Script             │
│  (streamlit_app.py)        │  (cli_transcribe.py)    │
│  - Upload files            │  - Command line args    │
│  - Select models/formats   │  - Batch processing     │
│  - Preview results         │  - Scripting            │
└─────────────┬──────────────┴────────────┬────────────┘
              │                          │
              └──────────────┬───────────┘
                             │
              ┌──────────────▼────────────┐
              │  Transcriber Module       │
              │  (transcriber.py)         │
              ├──────────────────────────┤
              │ - OpenAI API client       │
              │ - Format handling         │
              │ - Multi-format support    │
              │ - Error handling          │
              └──────────────┬────────────┘
                             │
              ┌──────────────▼────────────┐
              │  Audio Processor          │
              │  (audio_processor.py)     │
              ├──────────────────────────┤
              │ - File size checking      │
              │ - Audio chunking (>25MB)  │
              │ - Format merging          │
              │ - Timestamp adjustment    │
              └──────────────┬────────────┘
                             │
              ┌──────────────▼────────────┐
              │  External Services        │
              ├──────────────────────────┤
              │ - OpenAI Audio API        │
              │ - FFmpeg (conversion)     │
              │ - Librosa (analysis)      │
              └──────────────────────────┘

              ┌──────────────────────────┐
              │  Storage                 │
              ├──────────────────────────┤
              │ - input/                 │
              │ - output/                │
              │ - .env (config)          │
              └──────────────────────────┘
```

## Module Description

### 1. **transcriber.py** - Core Transcription Engine

**Responsibility**: Mengelola komunikasi dengan OpenAI Audio Transcription API

```python
AudioTranscriber
├── __init__()                # Initialize OpenAI client
├── is_supported_format()     # Validasi format file
├── transcribe()              # Call API untuk transcription
└── transcribe_and_save()     # Transcribe dan save ke multiple formats
```

**Features**:
- Support berbagai models: `gpt-4o-transcribe`, `gpt-4o-transcribe-diarize`, `whisper-1`
- Output formats: `text`, `json`, `verbose_json`, `srt`, `vtt`
- Language support: Berbagai bahasa dengan default Indonesia (`id`)
- Optional context prompt untuk meningkatkan akurasi
- Error handling dan logging

**Dependencies**:
- `openai` - OpenAI Python SDK
- `python-dotenv` - Environment variable loading

---

### 2. **audio_processor.py** - Audio Processing & Merging

**Responsibility**: Handle audio file yang melebihi 25MB limit dengan chunking otomatis

```python
AudioProcessor
├── get_file_size()           # Cek ukuran file
├── get_audio_duration()      # Durasi audio
├── needs_chunking()          # Check apakah perlu di-split
├── chunk_audio()             # Split file menjadi chunks
│
├── merge_text_transcripts()  # Gabung text results
├── merge_json_transcripts()  # Gabung JSON dengan metadata
├── merge_srt_transcripts()   # Gabung SRT dengan timing adjustment
├── merge_vtt_transcripts()   # Gabung VTT
│
└── cleanup_chunks()          # Hapus temp chunk files
```

**Key Features**:
- Auto-detection file size >25MB
- Configurable chunk duration (default 5 menit)
- Smart timestamp adjustment saat merge SRT/VTT
- Preserve audio format (MP3, WAV, etc)
- Automatic cleanup temp files

**Dependencies**:
- `pydub` - Audio processing
- `librosa` - Audio analysis
- `numpy` - Numerical computing

---

### 3. **streamlit_app.py** - Web User Interface

**Responsibility**: Menyediakan web UI untuk user-friendly transcription

**Features**:
- File uploader dengan drag-drop support
- Model selection dropdown
- Output format checkboxes (dynamic based on model)
- Language selection
- Optional custom prompt
- Progress bar + status updates
- Multi-format download buttons
- Transcript preview (text/JSON/SRT/VTT)
- History panel (recent 10 files)
- Responsive design dengan custom CSS

**Data Flow**:
```
Upload File
    ↓
Save ke input/
    ↓
Check file size
    ↓
Chunk (jika >25MB) atau Direct transcribe
    ↓
Call OpenAI API per chunk
    ↓
Merge results
    ↓
Save ke output/
    ↓
Display results + Download buttons
```

**Dependencies**:
- `streamlit` - Web framework
- Semua module internal

---

### 4. **cli_transcribe.py** - Command Line Interface

**Responsibility**: Menyediakan CLI untuk scripting dan batch processing

**Usage**:
```bash
python cli_transcribe.py audio.mp3 \
  --model gpt-4o-transcribe \
  --formats text,json,srt \
  --language id \
  --output output/
```

**Command Arguments**:
- `audio_file` (required) - Path audio file
- `--model` - Model selection
- `--formats` - Output formats (comma-separated)
- `--language` - Language code
- `--output` - Output directory
- `--prompt` - Optional context prompt

**Dependencies**:
- `argparse` - CLI argument parsing
- Semua module internal

---

## Data Flow

### Scenario 1: File < 25MB
```
1. User upload file via UI / CLI
2. Save temporary ke input/
3. Check file size → OK (< 25MB)
4. Call OpenAI API langsung
5. Receive transcript (text/json/srt/vtt)
6. Save ke output/
7. User download hasil
```

### Scenario 2: File > 25MB
```
1. User upload file
2. Check file size → LARGE (> 25MB)
3. Chunk audio menjadi ~5 menit chunks
4. For each chunk:
   a. Call OpenAI API
   b. Store result temporarily
5. Merge results (text/json/srt/vtt dengan smart handling)
6. Save merged ke output/
7. Cleanup temp chunks
8. User download hasil
```

### Multi-Format Export
```
User select: [text] [json] [srt] [vtt]
    ↓
For each format:
  - Call OpenAI dengan response_format=<format>
  - Save <filename>.<ext>
    ↓
Download buttons for all formats
```

---

## File Size & Chunk Strategy

**OpenAI Limits**:
- Max file size per request: **25 MB**
- Supported formats: MP3, MP4, MPEG, MPGA, M4A, WAV, WebM

**Our Chunking Strategy**:
```
File Size              Action
─────────────────────────────
< 25 MB              Direct transcribe
25-250 MB            Split to 5-min chunks
250 MB - 2 GB        Split to 3-min chunks
> 2 GB               Warning + Split to 2-min chunks
```

**Chunk Merging Logic**:
- **Text**: Simple concatenation dengan space separator
- **JSON**: Merge dengan chunk index + metadata tracking
- **SRT**: Parse + adjust timestamps + renumber subtitles
- **VTT**: Parse + adjust timestamps

---

## Error Handling

### Level 1: Validation
```python
if not Path(file).exists():
    raise FileNotFoundError()

if not is_supported_format(file):
    raise ValueError("Unsupported format")
```

### Level 2: API Errors
```python
try:
    transcript = client.audio.transcriptions.create(...)
except OpenAI.APIError as e:
    log error + retry with exponential backoff
    or fallback to alternative model
```

### Level 3: Processing Errors
```python
try:
    chunk = merge_chunks(...)
except Exception as e:
    log detailed error
    return partial results (completed chunks)
    notify user about failure
```

---

## Configuration

### Environment Variables (.env)
```
OPENAI_API_KEY=sk-proj-xxxxx...    # Required
OPENAI_MODEL=gpt-4o-transcribe     # Optional, default used
DEFAULT_LANGUAGE=id                # Optional, default used
```

### Runtime Configs
- Model selection
- Output format selection
- Language selection
- Custom prompt (optional)

---

## Performance Considerations

### Speed Optimization
1. **Parallel Chunk Processing** (Future)
   - Implement async OpenAI API calls
   - Process multiple chunks simultaneously

2. **Caching** (Future)
   - Cache transcripts untuk file identical
   - Hash-based deduplication

3. **Audio Preprocessing** (Optional)
   - Auto-convert ke MP3 untuk consistency
   - Reduce bitrate untuk faster processing

### Memory Management
- Stream file uploads (no full load to memory)
- Delete temp chunks immediately after transcription
- Limit chunk duration untuk manage memory usage

---

## Deployment Options

### Option 1: Local Python
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env dengan API key
streamlit run streamlit_app.py
```

### Option 2: Docker
```bash
cp .env.example .env
docker-compose up --build
```

### Option 3: CLI Only (No UI)
```bash
python cli_transcribe.py input/audio.mp3
```

---

## Security Considerations

1. **API Key Management**
   - Store in `.env` file (never commit)
   - Use `.gitignore` untuk protect secrets
   - Consider using environment variable injection di production

2. **File Handling**
   - Validate file type & size sebelum processing
   - Use secure temp directory untuk chunks
   - Auto-cleanup temp files

3. **User Input**
   - Sanitize file names sebelum save
   - Validate all CLI arguments
   - Error messages yang generic (tidak leak info sensitif)

---

## Future Enhancements

1. **Features**
   - [ ] Batch processing multiple files
   - [ ] Email results when done (async job)
   - [ ] Custom vocabulary training
   - [ ] Translation (text hasil ke language lain)
   - [ ] Speaker identification visualization

2. **Performance**
   - [ ] Async/parallel chunk processing
   - [ ] Result caching dengan content-hash
   - [ ] Distributed processing (multiple workers)

3. **Reliability**
   - [ ] Retry logic dengan exponential backoff
   - [ ] Fallback ke whisper-1 jika gpt-4o gagal
   - [ ] Resume interrupted transcriptions

4. **UI/UX**
   - [ ] Dark mode
   - [ ] Advanced filters untuk history
   - [ ] Real-time chunk processing visualization
   - [ ] Export ke multiple formats otomatis

5. **Integration**
   - [ ] API endpoint untuk integration ke apps lain
   - [ ] Webhook notifications
   - [ ] Database storage untuk transcript history
