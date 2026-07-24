# Quick Start Guide

## 1. Setup (Pilih salah satu)

### Windows
```bash
setup.bat
```

### MacOS/Linux
```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
```

## 2. Konfigurasi API Key

Edit file `.env`:
```
OPENAI_API_KEY=sk-proj-xxxxx...
```

Dapatkan API key dari: https://platform.openai.com/api-keys

## 3. Cek Setup (Optional)

Pastikan semua dependencies terinstall:
```bash
pip list
```

Pastikan FFmpeg sudah terinstall:
```bash
ffmpeg -version
```

## 4. Gunakan Aplikasi

### Opsi A: Web UI (Recommended)
```bash
streamlit run streamlit_app.py
```
Buka browser ke `http://localhost:8501`

### Opsi B: Command Line
```bash
python cli_transcribe.py input/audio.mp3

# Dengan opsi custom
python cli_transcribe.py input/audio.mp3 \
  --model gpt-4o-transcribe \
  --formats text,json,srt \
  --language id
```

### Opsi C: Python Script
```python
from transcriber import AudioTranscriber

transcriber = AudioTranscriber()
result = transcriber.transcribe(
    "input/audio.mp3",
    model="gpt-4o-transcribe",
    response_format="text",
    language="id",
)
print(result)
```

## Contoh Penggunaan

### 1. Transcribe Satu File ke Text
```bash
python cli_transcribe.py input/meeting.mp3 --formats text
```

### 2. Transcribe dengan Multiple Formats
```bash
python cli_transcribe.py input/meeting.mp3 \
  --formats text,json,srt,vtt
```

### 3. Transcribe File Besar (Auto-chunk)
```bash
# File >25MB akan di-split otomatis menjadi chunks
python cli_transcribe.py input/large-file.mp3 \
  --formats text,json
```

### 4. Transcribe dengan Custom Prompt
```bash
python cli_transcribe.py input/meeting.mp3 \
  --prompt "Ini adalah rapat office untuk diskusi project baru"
```

### 5. Transcribe Multi-speaker (Diarization)
```bash
python cli_transcribe.py input/meeting.mp3 \
  --model gpt-4o-transcribe-diarize \
  --formats json
```

## Output Files

Hasil disimpan di folder `output/`:
- `audio.txt` — Text plain
- `audio.json` — JSON format (termasuk metadata)
- `audio.srt` — Subtitle format dengan timestamps
- `audio.vtt` — WebVTT format

## Troubleshooting

### Error: OPENAI_API_KEY not found
**Solusi**: Buat file `.env` dan isi dengan API key Anda
```bash
cp .env.example .env
# Edit .env dan isi OPENAI_API_KEY
```

### Error: Module not found (openai, streamlit, dll)
**Solusi**: Install dependencies
```bash
pip install -r requirements.txt
```

### Error: FFmpeg not found
**Solusi**: Install FFmpeg
- **Windows**: Download dari https://ffmpeg.org/ atau `choco install ffmpeg`
- **MacOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`

### Error: File size limit exceeded
**Solusi**: File akan di-chunk otomatis. Tidak perlu action apapun.

### Error: Unsupported file format
**Solusi**: Konversi ke format yang didukung:
```bash
# MP4 → MP3
ffmpeg -i input.mp4 -q:a 0 -map a output.mp3

# WAV → MP3
ffmpeg -i input.wav -q:a 0 output.mp3
```

## Tips

1. **Kualitas Terbaik**: Gunakan `gpt-4o-transcribe`
2. **File Besar**: App auto-chunk files >25MB, tidak perlu split manual
3. **Multiple Speakers**: Gunakan `gpt-4o-transcribe-diarize`
4. **SRT/VTT**: Gunakan `whisper-1` (format lebih lengkap)
5. **Custom Prompt**: Tambahkan context untuk akurasi lebih baik

## API Costs

Harga tergantung model dan durasi audio. Cek: https://openai.com/pricing/

## Support

- Docs: https://platform.openai.com/docs/guides/speech-to-text
- Issues: Buat issue di repository
