# 📚 Panduan Lengkap Voice-to-Text Transcriber

## 📋 Daftar Isi
1. [Gambaran Umum](#gambaran-umum)
2. [Struktur Proyek](#struktur-proyek)
3. [Instalasi & Setup](#instalasi--setup)
4. [Penjelasan Kode](#penjelasan-kode)
5. [Cara Penggunaan](#cara-penggunaan)
6. [API & Models](#api--models)
7. [Troubleshooting](#troubleshooting)

---

## 📖 Gambaran Umum

**Voice-to-Text Transcriber** adalah aplikasi Python yang mengubah file audio/video menjadi teks menggunakan OpenAI Audio Transcription API.

### 🎯 Fitur Utama
- ✅ **Web UI** - Upload file via Streamlit interface
- ✅ **CLI** - Command-line tool untuk batch processing
- ✅ **Multi-format Output** - TXT, JSON, SRT, VTT
- ✅ **Auto-chunking** - Split file otomatis jika >25MB
- ✅ **Multi-model** - Support gpt-4o, whisper, diarize
- ✅ **Multi-language** - Support berbagai bahasa
- ✅ **Video Support** - Ekstrak audio dari video file

---

## 🏗️ Struktur Proyek

```
voice_to_text/
├── 📄 Main Scripts
│   ├── streamlit_app.py          # Web UI
│   ├── cli_transcribe.py         # CLI interface
│   ├── transcriber.py            # Core transcription engine
│   └── audio_processor.py        # Audio processing & merging
│
├── 🗂️ Folders
│   ├── input/                    # Upload audio files di sini
│   └── output/                   # Hasil transkrip otomatis tersimpan
│
├── ⚙️ Config & Setup
│   ├── requirements.txt          # Python dependencies
│   ├── requirements-dev.txt      # Dev dependencies
│   ├── .env                      # Konfigurasi API key
│   ├── setup.bat                 # Windows setup
│   ├── setup.sh                  # MacOS/Linux setup
│   └── docker-compose.yml        # Docker setup (opsional)
│
├── 📖 Documentation
│   ├── README.md                 # Overview
│   ├── ARCHITECTURE.md           # Technical design
│   ├── QUICKSTART.md             # Quick start guide
│   └── PANDUAN_LENGKAP.md        # Panduan ini
│
├── 🧪 Test Scripts
│   ├── test_mock.py              # Test dengan mock data
│   └── test_video.py             # Test video extraction
│
└── 🐳 Docker
    └── Dockerfile                # Container setup

```

---

## 🚀 Instalasi & Setup

### Step 1: Prerequisites
- **Python 3.11+** (download dari python.org)
- **FFmpeg** (untuk audio processing)
- **OpenAI API Key** (dari platform.openai.com)

### Step 2: Install FFmpeg

#### Windows
```bash
# Menggunakan Chocolatey
choco install ffmpeg

# Atau download manual
# https://ffmpeg.org/download.html
```

#### MacOS
```bash
brew install ffmpeg
```

#### Linux
```bash
sudo apt-get install ffmpeg
```

### Step 3: Install Python Dependencies

**Opsi A: Automatic (Recommended)**

Windows:
```bash
setup.bat
```

MacOS/Linux:
```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
```

**Opsi B: Manual**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# MacOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Setup OpenAI API Key

1. Buat file `.env` di root directory
2. Dapatkan API key dari: https://platform.openai.com/api-keys
3. Edit `.env`:
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

Verifikasi setup:
```bash
python -c "from openai import OpenAI; print('✓ OpenAI module installed')"
```

---

## 💻 Penjelasan Kode

### 1. **transcriber.py** - Core Engine

Modul utama yang menangani komunikasi dengan OpenAI API.

#### Komponen Utama:

```python
class AudioTranscriber:
    def __init__(self, api_key: Optional[str] = None)
```
**Fungsi**: Initialize OpenAI client dari environment variable atau parameter

**Parameters**:
- `api_key` (str, optional): OpenAI API key

**Attributes**:
- `self.client`: OpenAI client instance
- `self.processor`: AudioProcessor instance
- `self.supported_formats`: List format audio yang didukung

---

```python
def is_supported_format(self, file_path: str) -> bool
```
**Fungsi**: Validasi apakah format file didukung

**Supported Formats**: MP3, MP4, MPEG, MPGA, M4A, WAV, WebM + Video formats

---

```python
def transcribe(
    self, 
    file_path: str, 
    model: str = "gpt-4o-transcribe",
    language: str = "id",
    prompt: Optional[str] = None
) -> dict
```
**Fungsi**: Call OpenAI API untuk transcription

**Parameters**:
- `file_path` (str): Path ke audio file
- `model` (str): Model transcription
  - `gpt-4o-transcribe` (Default, Best quality)
  - `gpt-4o-transcribe-diarize` (Multi-speaker support)
  - `whisper-1` (Legacy, More formats)
- `language` (str): Language code (default: "id")
- `prompt` (str, optional): Context untuk improve accuracy

**Returns**: Dict dengan transcript dan metadata

---

```python
def transcribe_and_save(
    self,
    file_path: str,
    output_dir: str = "output",
    formats: list = ["text", "json"],
    model: str = "gpt-4o-transcribe",
    language: str = "id",
    prompt: Optional[str] = None
)
```
**Fungsi**: Transcribe dan save ke multiple format output

**Output Formats**:
- `text` - Plain text (.txt)
- `json` - JSON dengan metadata (.json)
- `verbose_json` - JSON dengan detailed timing (Whisper only)
- `srt` - Subtitle format (.srt)
- `vtt` - WebVTT format (.vtt)

---

### 2. **audio_processor.py** - Audio Processing

Modul untuk handle audio chunking, format conversion, dan merging hasil.

#### Komponen Utama:

```python
class AudioProcessor:
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB limit
```

OpenAI API memiliki limit 25MB per request. Module ini otomatis split file yang lebih besar.

---

```python
def get_file_size(self, file_path: str) -> int
```
**Fungsi**: Cek ukuran file dalam bytes

---

```python
def get_audio_duration(self, file_path: str) -> float
```
**Fungsi**: Dapatkan durasi audio (dalam seconds) menggunakan librosa

**Return**: Duration dalam detik (float)

---

```python
def needs_chunking(self, file_path: str) -> bool
```
**Fungsi**: Check apakah file perlu di-chunk (size > 25MB)

---

```python
def chunk_audio(
    self, 
    file_path: str, 
    chunk_duration: int = 600
) -> list
```
**Fungsi**: Split audio menjadi chunks (default: 10 menit per chunk)

**Returns**: List of chunk file paths

**Proses**:
1. Load audio file
2. Calculate jumlah chunks berdasarkan duration
3. Simpan setiap chunk ke temp folder
4. Return list file paths

---

```python
def merge_text_transcripts(self, text_files: list) -> str
```
**Fungsi**: Gabung multiple text files menjadi satu

**Proses**: Konkatenasi semua text dengan separator baru

---

```python
def merge_json_transcripts(self, json_files: list) -> dict
```
**Fungsi**: Gabung JSON dengan metadata

**Proses**:
1. Load semua JSON files
2. Merge `text` field
3. Preserve metadata (model, language, dll)

---

```python
def merge_srt_transcripts(self, srt_files: list) -> str
```
**Fungsi**: Gabung SRT dengan timestamp adjustment

**Penting**: Adjust timestamps setiap chunk berdasarkan posisinya

**Proses**:
1. Parse setiap SRT file
2. Adjust timing untuk setiap chunk
3. Combine dengan renumber sequence

---

```python
def extract_audio_from_video(self, video_path: str) -> str
```
**Fungsi**: Ekstrak audio dari video file

**Supported Video Formats**: MP4, AVI, MOV, MKV, FLV, WMV, WebM, M4V

**Returns**: Path ke extracted audio file (.mp3)

---

### 3. **streamlit_app.py** - Web UI

Interface web untuk upload dan transcribe audio.

#### Main Sections:

**1. Configuration Sidebar**
```python
model = st.selectbox(...)        # Pilih model
selected_formats = st.multiselect(...)  # Output formats
language = st.selectbox(...)     # Bahasa
custom_prompt = st.text_area(...) # Optional context
```

**2. File Upload**
```python
uploaded_file = st.file_uploader(...)  # Upload audio file
```

**3. Transcription Process**
- Save file ke `input/` folder
- Check ukuran file
- Auto-chunk jika > 25MB
- Call transcription API
- Save hasil ke `output/` folder
- Show preview hasil
- Provide download button

#### Fitur UI:
- ✅ Real-time status updates
- ✅ Progress bar untuk chunked files
- ✅ Preview hasil transcription
- ✅ Download buttons untuk setiap format
- ✅ Error handling dengan user-friendly messages

---

### 4. **cli_transcribe.py** - Command Line Interface

CLI tool untuk scripting dan batch processing.

#### Usage:

```bash
# Basic
python cli_transcribe.py input/audio.mp3

# With options
python cli_transcribe.py input/audio.mp3 \
    --model whisper-1 \
    --formats text,json,srt \
    --language en \
    --output results/

# With prompt
python cli_transcribe.py input/video.mp4 \
    --prompt "Ini adalah meeting dengan topik X"
```

#### Parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `audio_file` | - | Path ke file (required) |
| `--model` | gpt-4o-transcribe | Model choice |
| `--formats` | text,json | Output formats |
| `--language` | id | Language code |
| `--output` | output/ | Output directory |
| `--prompt` | None | Optional context |

#### Process Flow:
1. Validate file exists
2. Detect file type (audio/video)
3. Extract audio jika video
4. Check file size, chunk jika perlu
5. Transcribe setiap chunk
6. Merge results
7. Save ke output folder

---

## 📱 Cara Penggunaan

### Opsi 1: Web UI (Streamlit)

**Start aplikasi:**
```bash
streamlit run streamlit_app.py
```

**Akses:**
- Browser: `http://localhost:8501`

**Workflow:**
1. Upload file audio di main area
2. Configure settings di sidebar (model, format, language)
3. (Optional) Add custom prompt untuk improve accuracy
4. Click "Mulai Transcription"
5. Tunggu proses selesai
6. Preview hasil dan download

**Output locations:**
- Semua hasil tersimpan di `output/` folder
- Format: `[filename]_chunk_000.[format]`

---

### Opsi 2: CLI (Command Line)

**Basic transcription:**
```bash
python cli_transcribe.py input/audio.mp3
```

**Output:**
- `output/audio_chunk_000.txt`
- `output/audio_chunk_000.json`

**Dengan multiple formats:**
```bash
python cli_transcribe.py input/audio.mp3 \
    --formats text,json,srt,vtt
```

**Dengan context prompt:**
```bash
python cli_transcribe.py input/meeting.mp3 \
    --prompt "Ini adalah rapat tim engineering"
```

**Dengan video file:**
```bash
python cli_transcribe.py input/presentation.mp4 \
    --model whisper-1 \
    --formats text,json
```

---

### Opsi 3: Programmatic (Python Script)

```python
from transcriber import AudioTranscriber
from audio_processor import AudioProcessor

# Initialize
transcriber = AudioTranscriber()
processor = AudioProcessor()

# Simple transcription
result = transcriber.transcribe(
    "input/audio.mp3",
    model="gpt-4o-transcribe",
    language="id",
    prompt="Ini adalah diskusi tentang teknologi"
)

print(result['text'])

# Or transcribe and save multiple formats
transcriber.transcribe_and_save(
    file_path="input/audio.mp3",
    output_dir="output",
    formats=["text", "json", "srt"],
    model="whisper-1",
    language="id"
)
```

---

## 🤖 API & Models

### OpenAI Audio Models

#### 1. **gpt-4o-transcribe** (Recommended)
- **Quality**: ⭐⭐⭐⭐⭐ (Best)
- **Speed**: Medium
- **Cost**: Higher
- **Output Formats**: text, json
- **Use Case**: High-quality transcription

#### 2. **gpt-4o-transcribe-diarize**
- **Quality**: ⭐⭐⭐⭐⭐ (Best)
- **Speed**: Medium
- **Cost**: Higher
- **Output Formats**: text, json
- **Special**: Multi-speaker identification
- **Use Case**: Meetings, conversations dengan multiple speakers

#### 3. **whisper-1** (Legacy)
- **Quality**: ⭐⭐⭐⭐ (Very Good)
- **Speed**: Faster
- **Cost**: Lower
- **Output Formats**: text, json, verbose_json, srt, vtt
- **Use Case**: Subtitle generation, timestamps needed

---

### Output Formats Explanation

#### **text**
Plain text format, hanya transcript tanpa metadata.

File: `audio.txt`
```
Halo, ini adalah transkrip dari audio file.
Sistem ini menggunakan OpenAI API untuk transcription.
```

---

#### **json**
Structured JSON dengan metadata.

File: `audio.json`
```json
{
  "text": "Halo, ini adalah transkrip...",
  "task": "transcribe",
  "language": "id",
  "model": "gpt-4o-transcribe",
  "duration": 120.5
}
```

---

#### **verbose_json** (Whisper only)
Detailed JSON dengan word-level timing.

File: `audio.json`
```json
{
  "task": "transcribe",
  "language": "id",
  "duration": 120.5,
  "text": "Halo, ini adalah transkrip...",
  "words": [
    {"word": "Halo", "start": 0.1, "end": 0.5},
    {"word": "ini", "start": 0.6, "end": 0.9},
    ...
  ]
}
```

---

#### **srt** (Subtitle Format)
SubRip subtitle format dengan timestamps.

File: `audio.srt`
```
1
00:00:00,100 --> 00:00:02,000
Halo, ini adalah transkrip

2
00:00:02,100 --> 00:00:05,000
dari audio file.

3
00:00:05,100 --> 00:00:08,000
Sistem ini menggunakan OpenAI API
```

---

#### **vtt** (WebVTT Format)
Web Video Text Tracks format (compatible dengan HTML5 video).

File: `audio.vtt`
```
WEBVTT

00:00:00.100 --> 00:00:02.000
Halo, ini adalah transkrip

00:00:02.100 --> 00:00:05.000
dari audio file.
```

---

## 🔧 Troubleshooting

### ❌ Error: "OPENAI_API_KEY not found"

**Solusi**:
1. Cek `.env` file ada di root directory
2. Verify format: `OPENAI_API_KEY=sk-proj-xxxxx`
3. Tidak ada spaces sebelum/sesudah `=`
4. Restart terminal/application setelah update `.env`

```bash
# Test
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

---

### ❌ Error: "FFmpeg not found"

**Solusi**:
1. Install FFmpeg sesuai OS Anda
2. Verify instalasi:
```bash
ffmpeg -version
```
3. Add ke PATH jika perlu

---

### ❌ Error: "File too large (>25MB)"

**Solusi**:
Aplikasi otomatis chunk file, tapi jika error tetap terjadi:
1. Gunakan FFmpeg manual untuk compress audio
2. Reduce bitrate:
```bash
ffmpeg -i input.mp3 -ab 128k output.mp3
```

---

### ❌ Error: "Audio quality too poor"

**Solusi**:
1. Try gunakan `--prompt` parameter dengan context
2. Switch ke model berbeda (try whisper-1)
3. Check audio file format support

---

### ❌ Error: "Unsupported file format"

**Solusi**:
1. Check list format yang didukung
2. Convert file ke format yang didukung:
```bash
# Convert ke MP3
ffmpeg -i input.wav -acodec libmp3lame -ab 192k output.mp3

# Convert video ke MP4
ffmpeg -i input.avi output.mp4
```

---

### ⚠️ Warning: "Extraction attempt failed"

**Solusi**:
1. File mungkin bukan video atau corrupted
2. Try manual ekstraksi:
```bash
ffmpeg -i video.mp4 -q:a 0 -map a output.mp3
```
3. Verify file format: `file video.mp4`

---

### 🐌 Slow Transcription

**Optimization Tips**:
1. Compress audio sebelumnya
2. Reduce durasi per chunk (adjust `chunk_duration`)
3. Use whisper-1 untuk speed (sacrifice quality)
4. Process multiple files dengan CLI (batch mode)

---

## 📊 Performance Metrics

### Typical Processing Times

| File Size | Model | Time |
|-----------|-------|------|
| 5 MB | gpt-4o | ~30 sec |
| 10 MB | gpt-4o | ~60 sec |
| 25 MB | gpt-4o | ~150 sec |
| 50 MB | gpt-4o | ~300 sec (2 chunks) |

### Cost Estimation (OpenAI Pricing)

| Model | Cost | Notes |
|-------|------|-------|
| gpt-4o-transcribe | $0.02 per minute | Recommended |
| whisper-1 | $0.02 per minute | Legacy |
| gpt-4o-transcribe-diarize | $0.02 per minute | Multi-speaker |

---

## 🎓 Advanced Usage

### Custom Processing Pipeline

```python
from transcriber import AudioTranscriber
from audio_processor import AudioProcessor

transcriber = AudioTranscriber()
processor = AudioProcessor()

# 1. Check file
file_path = "input/large_video.mp4"
print(f"File size: {processor.get_file_size(file_path) / 1024 / 1024:.2f} MB")
print(f"Duration: {processor.get_audio_duration(file_path)} seconds")

# 2. Extract audio dari video
audio_path = processor.extract_audio_from_video(file_path)

# 3. Check if needs chunking
if processor.needs_chunking(audio_path):
    print("Chunking required...")
    chunks = processor.chunk_audio(audio_path, chunk_duration=600)
    
    # 4. Transcribe setiap chunk
    transcripts = []
    for chunk in chunks:
        result = transcriber.transcribe(chunk)
        transcripts.append(result)
    
    # 5. Merge results
    merged_text = processor.merge_text_transcripts([t['text'] for t in transcripts])
    print(merged_text)
else:
    # Direct transcription
    result = transcriber.transcribe(audio_path)
    print(result['text'])
```

---

### Batch Processing

```python
from pathlib import Path
from transcriber import AudioTranscriber

transcriber = AudioTranscriber()
input_dir = Path("input")

# Process semua MP3 files
for audio_file in input_dir.glob("*.mp3"):
    print(f"Processing: {audio_file.name}")
    transcriber.transcribe_and_save(
        str(audio_file),
        formats=["text", "json"]
    )
    print(f"✓ Saved to output/")
```

---

## 📝 File Naming Convention

Output files mengikuti pattern:
```
[original_filename]_chunk_[sequence].[format]
```

**Contoh**:
- Input: `meeting_20240115.mp3`
- Output (single file):
  - `meeting_20240115_chunk_000.txt`
  - `meeting_20240115_chunk_000.json`
- Output (chunked):
  - `meeting_20240115_chunk_000.txt`
  - `meeting_20240115_chunk_001.txt`
  - `meeting_20240115_chunk_002.txt`
  - (merged to): `meeting_20240115.txt`

---

## 🔐 Security Notes

1. **API Key Safety**:
   - Jangan commit `.env` file ke git
   - Add `.env` ke `.gitignore`
   - Use environment variables di production

2. **File Storage**:
   - Sensitive audio files harus encrypted
   - Regular cleanup temp files (.temp_audio folder)

3. **Docker Deployment**:
   - Use environment variables, bukan hardcoded keys
   - Mount volumes untuk input/output
   - Use read-only volumes jika possible

---

## 🤝 Contributing & Customization

### Adding New Output Format

Edit `audio_processor.py`:
```python
def merge_custom_format(self, files: list) -> str:
    """Implement your custom merge logic"""
    # Your code here
    pass
```

Edit `transcriber.py`:
```python
def transcribe_and_save(self, ..., formats: list = ["text", "json"]):
    # Add your format handling
    if "custom" in formats:
        result = self.merge_custom_format(...)
```

---

## 📞 Support & Resources

- **OpenAI Docs**: https://platform.openai.com/docs/api-reference/audio
- **Streamlit Docs**: https://docs.streamlit.io/
- **FFmpeg Wiki**: https://trac.ffmpeg.org/wiki
- **GitHub**: [Project repository if available]

---

## 📝 Changelog

### v1.0.0 (Current)
- ✅ Web UI with Streamlit
- ✅ CLI with multi-format support
- ✅ Auto-chunking untuk large files
- ✅ Multi-model support
- ✅ Video audio extraction
- ✅ Multiple output formats

---

## ✅ Checklist untuk Memulai

- [ ] Python 3.11+ installed
- [ ] FFmpeg installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] OpenAI API key obtained
- [ ] `.env` file configured dengan API key
- [ ] Test setup dengan test scripts
- [ ] Choose UI (Web atau CLI)
- [ ] Upload test file
- [ ] Verify output dalam `output/` folder

---

**Last Updated**: Desember 2024  
**Version**: 1.0.0  
**License**: MIT (atau sesuai project Anda)

---

Selamat menggunakan Voice-to-Text Transcriber! 🎉
