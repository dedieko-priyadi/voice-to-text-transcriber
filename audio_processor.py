"""
Audio Processing Module
Handles audio chunking untuk file >25MB, format conversion, video extraction, dan hasil gabungan.
"""

import os
from pathlib import Path
from typing import Optional, Callable
import json
import re
import subprocess
import shutil
from pydub import AudioSegment
from pydub.utils import which
import librosa
import numpy as np
import soundfile as sf
from scipy.io import wavfile


class AudioProcessor:
    """Handle audio chunking, conversion, video extraction, dan merge hasil transkrip"""
    
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB dalam bytes
    
    AUDIO_FORMATS = {"mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"}
    VIDEO_FORMATS = {"mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "m4v", "json"}  # json untuk file video salah ekstensi
    
    def __init__(self, temp_dir: str = ".temp_audio"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        self.ffmpeg_path: Optional[str] = None
        self.ffprobe_path: Optional[str] = None
        
        # Set FFmpeg path untuk AudioSegment
        self._setup_ffmpeg_path()
    
    def _setup_ffmpeg_path(self):
        """Try to find and setup FFmpeg path for pydub and librosa"""
        # Check common locations (including portable FFmpeg in project)
        possible_paths = [
            str(Path(__file__).parent / "ffmpeg" / "bin" / "ffmpeg.exe"),
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "C:\\tools\\ffmpeg\\bin\\ffmpeg.exe",
            str(Path.home() / "AppData" / "Local" / "ffmpeg" / "bin" / "ffmpeg.exe"),
            str(Path.home() / "scoop" / "shims" / "ffmpeg.exe"),
            which("ffmpeg"),
        ]

        for path in [candidate for candidate in possible_paths if candidate]:
            try:
                result = subprocess.run([path, "-version"], capture_output=True, timeout=2)
                if result.returncode == 0:
                    ffmpeg_path = str(Path(path).resolve())
                    ffprobe_candidate = Path(ffmpeg_path).with_name("ffprobe.exe")
                    ffprobe_path = str(ffprobe_candidate) if ffprobe_candidate.exists() else which("ffprobe")

                    # Found FFmpeg, set it for pydub
                    self.ffmpeg_path = ffmpeg_path
                    self.ffprobe_path = ffprobe_path
                    AudioSegment.converter = path
                    AudioSegment.ffmpeg = path
                    if ffprobe_path:
                        AudioSegment.ffprobe = ffprobe_path
                        os.environ["FFPROBE_BINARY"] = ffprobe_path
                    # Also set in environment for subprocess/audioread
                    os.environ["FFMPEG_BINARY"] = ffmpeg_path
                    os.environ['FFMPEG_PATH'] = ffmpeg_path
                    print(f"✓ FFmpeg found: {ffmpeg_path}")
                    if ffprobe_path:
                        print(f"✓ FFprobe found: {ffprobe_path}")
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        print("⚠️  FFmpeg not found")
        return False
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        return os.path.getsize(file_path)
    
    def get_audio_duration(self, file_path: str) -> float:
        """Get audio duration in seconds using librosa"""
        try:
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            return duration
        except Exception as e:
            print(f"Warning: Could not get duration: {e}")
            return None
    
    def is_video_file(self, file_path: str) -> bool:
        """Check if file is video format"""
        ext = Path(file_path).suffix.lstrip(".").lower()
        return ext in self.VIDEO_FORMATS
    
    def is_audio_file(self, file_path: str) -> bool:
        """Check if file is audio format"""
        ext = Path(file_path).suffix.lstrip(".").lower()
        return ext in self.AUDIO_FORMATS
    
    def extract_audio_from_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio dari video file menggunakan ffmpeg
        
        Args:
            video_path: Path ke video file
            output_path: Path untuk save audio (default: .temp_audio/extracted_audio.mp3)
        
        Returns:
            Path ke file audio yang sudah diekstrak
        """
        if output_path is None:
            output_path = self.temp_dir / "extracted_audio.mp3"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Extracting audio from video: {Path(video_path).name}")
        
        try:
            ffmpeg_bin = self.ffmpeg_path or "ffmpeg"
            # Gunakan ffmpeg untuk ekstraksi
            # Format: ffmpeg -i input.mp4 -q:a 0 -map a output.mp3
            cmd = [
                ffmpeg_bin,
                "-i", str(video_path),
                "-q:a", "0",
                "-map", "a",
                str(output_path),
                "-y"  # Overwrite output file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
            
            if not output_path.exists():
                raise Exception(f"Audio extraction failed: output file not created")
            
            file_size = output_path.stat().st_size / 1024 / 1024
            print(f"✓ Audio extracted: {output_path.name} ({file_size:.2f} MB)")
            return str(output_path)
        
        except FileNotFoundError:
            raise Exception(
                "FFmpeg not found. Install FFmpeg:\n"
                "- Windows: choco install ffmpeg\n"
                "- macOS: brew install ffmpeg\n"
                "- Linux: sudo apt-get install ffmpeg"
            )
        except Exception as e:
            raise Exception(f"Error extracting audio: {str(e)}")
    
    def process_media_file(self, file_path: str) -> str:
        """
        Process media file (video atau audio)
        Jika video, extract audio dulu.
        Jika audio, return path-nya.
        
        Args:
            file_path: Path ke media file
        
        Returns:
            Path ke audio file yang siap diproses
        """
        file_path = str(file_path)
        
        if self.is_video_file(file_path):
            print(f"📹 Detected video file: {Path(file_path).name}")
            return self.extract_audio_from_video(file_path)
        elif self.is_audio_file(file_path):
            print(f"🎵 Detected audio file: {Path(file_path).name}")
            return file_path
        else:
            raise ValueError(f"Unsupported file format: {Path(file_path).suffix}")
    
    def needs_chunking(self, file_path: str) -> bool:
        """Check if file needs chunking (>25MB)"""
        return self.get_file_size(file_path) > self.MAX_FILE_SIZE

    def needs_duration_chunking(self, file_path: str, model: str = "gpt-4o-transcribe") -> bool:
        """
        Check if audio duration exceeds model limits.
        
        Model limits (with 200s safety margin):
        - gpt-4o-transcribe: 1200s effective (1400s hard limit)
        - gpt-4o-transcribe-diarize: 1200s effective (1400s hard limit)
        - whisper-1: 25MB file size limit (no duration limit, but practical limits apply)
        
        Returns:
            True if duration exceeds model limit
        """
        # Model duration limits in seconds (with safety margin)
        MODEL_LIMITS = {
            "gpt-4o-transcribe": 1200,
            "gpt-4o-transcribe-diarize": 1200,
        }
        
        if model not in MODEL_LIMITS:
            return False
        
        max_duration = MODEL_LIMITS[model]
        duration = self.get_audio_duration(file_path)
        
        if duration is None:
            return False
        
        return duration > max_duration

    def _get_media_duration_seconds(self, file_path: str) -> float:
        """Get media duration using ffprobe."""
        if not self.ffprobe_path:
            raise RuntimeError("FFprobe not found")

        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    
    def chunk_audio_by_duration(
        self,
        file_path: str,
        max_duration_sec: float = 1400.0,
        output_dir: Optional[str] = None,
    ) -> list[str]:
        """
        Split audio file into chunks based on maximum duration.
        This is used when audio exceeds model time limits (e.g., gpt-4o-transcribe's 1400s limit).
        
        Args:
            file_path: Path to audio file
            max_duration_sec: Maximum duration per chunk in seconds (default: 1400s)
            output_dir: Directory to save chunks (default: self.temp_dir)
        
        Returns:
            List of chunk file paths
        """
        if output_dir is None:
            output_dir = self.temp_dir
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        file_path = str(Path(file_path).resolve())
        ffmpeg_bin = self.ffmpeg_path or "ffmpeg"
        
        print(f"Loading audio: {file_path}")

        try:
            total_duration_sec = self._get_media_duration_seconds(file_path)
        except Exception as e:
            print(f"❌ Error reading duration with ffprobe: {e}")
            raise

        num_chunks = int(np.ceil(total_duration_sec / max_duration_sec))
        
        print(f"Total duration: {total_duration_sec:.1f}s ({total_duration_sec/60:.1f} min)")
        print(f"Max duration per chunk: {max_duration_sec:.1f}s ({max_duration_sec/60:.1f} min)")
        print(f"Creating {num_chunks} chunks...")
        
        chunks = []
        audio_stem = Path(file_path).stem
        
        for i in range(num_chunks):
            start_sec = i * max_duration_sec
            current_chunk_duration = min(max_duration_sec, total_duration_sec - start_sec)
            chunk_path = output_path / f"{audio_stem}_chunk_{i:03d}.mp3"

            cmd = [
                ffmpeg_bin,
                "-ss", str(start_sec),
                "-t", str(current_chunk_duration),
                "-i", file_path,
                "-vn",
                "-acodec", "mp3",
                "-y",
                str(chunk_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg chunking failed: {result.stderr}")

            chunks.append(str(chunk_path))
            
            chunk_start_min = start_sec / 60
            chunk_duration_min = current_chunk_duration / 60
            print(f"  Chunk {i+1}/{num_chunks}: {chunk_start_min:.1f}m - {chunk_start_min + chunk_duration_min:.1f}m ({current_chunk_duration:.1f}s)")
        
        return chunks
    
    def chunk_audio(
        self,
        file_path: str,
        chunk_duration_ms: int = 5 * 60 * 1000,  # 5 menit default
        output_dir: Optional[str] = None,
    ) -> list[str]:
        """
        Split audio file into chunks
        
        Args:
            file_path: Path to audio file
            chunk_duration_ms: Duration per chunk in milliseconds
            output_dir: Directory to save chunks (default: self.temp_dir)
        
        Returns:
            List of chunk file paths
        """
        if output_dir is None:
            output_dir = self.temp_dir
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Convert to absolute path to handle spaces and special characters properly
        file_path = str(Path(file_path).resolve())
        ffmpeg_bin = self.ffmpeg_path or "ffmpeg"
        
        print(f"Loading audio: {file_path}")

        try:
            total_duration_sec = self._get_media_duration_seconds(file_path)
        except Exception as e:
            print(f"❌ Error reading duration with ffprobe: {e}")
            raise

        chunk_duration_sec = chunk_duration_ms / 1000.0
        total_duration = int(total_duration_sec * 1000)
        num_chunks = int(np.ceil(total_duration_sec / chunk_duration_sec))
        
        print(f"Total duration: {total_duration_sec:.1f}s")
        print(f"Chunk size: {chunk_duration_sec:.1f}s")
        print(f"Creating {num_chunks} chunks...")
        
        chunks = []
        audio_stem = Path(file_path).stem
        
        for i in range(num_chunks):
            start_sec = i * chunk_duration_sec
            current_chunk_duration = min(chunk_duration_sec, total_duration_sec - start_sec)
            chunk_path = output_path / f"{audio_stem}_chunk_{i:03d}.mp3"

            cmd = [
                ffmpeg_bin,
                "-ss", str(start_sec),
                "-t", str(current_chunk_duration),
                "-i", file_path,
                "-vn",
                "-acodec", "mp3",
                "-y",
                str(chunk_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg chunking failed: {result.stderr}")

            chunks.append(str(chunk_path))
            
            print(f"  Chunk {i+1}/{num_chunks}: {current_chunk_duration:.1f}s → {chunk_path.name}")
        
        return chunks
    
    def merge_text_transcripts(self, transcripts: list[str]) -> str:
        """Merge text transcripts dari multiple chunks"""
        return " ".join(transcripts)
    
    def merge_json_transcripts(
        self,
        json_transcripts: list[str],
        preserve_timestamps: bool = False,
    ) -> dict:
        """
        Merge JSON transcripts dengan metadata
        
        Args:
            json_transcripts: List of JSON transcript strings
            preserve_timestamps: Keep timing info jika ada
        
        Returns:
            Merged JSON object
        """
        merged = {
            "text": "",
            "chunks": [],
            "metadata": {
                "total_chunks": len(json_transcripts),
                "merged": True,
            }
        }
        
        texts = []
        
        for i, json_str in enumerate(json_transcripts):
            try:
                data = json.loads(json_str)
                
                if isinstance(data, dict) and "text" in data:
                    text = data["text"]
                else:
                    text = json_str
                
                texts.append(text)
                
                merged["chunks"].append({
                    "index": i,
                    "text": text,
                    "length": len(text),
                })
            except json.JSONDecodeError:
                texts.append(json_str)
                merged["chunks"].append({
                    "index": i,
                    "text": json_str,
                    "length": len(json_str),
                })
        
        merged["text"] = " ".join(texts)
        return merged
    
    def merge_srt_transcripts(self, srt_transcripts: list[str]) -> str:
        """
        Merge SRT files dengan adjusted timestamps
        
        Args:
            srt_transcripts: List of SRT content strings
        
        Returns:
            Merged SRT string
        """
        merged_lines = []
        current_index = 1
        time_offset = 0
        
        for srt_content in srt_transcripts:
            lines = srt_content.strip().split("\n")
            
            for line in lines:
                # Check if line is timestamp
                if " --> " in line:
                    # Parse and adjust timestamps
                    parts = line.split(" --> ")
                    try:
                        start = self._add_time_offset(parts[0].strip(), time_offset)
                        end = self._add_time_offset(parts[1].strip(), time_offset)
                        merged_lines.append(f"{start} --> {end}")
                    except:
                        merged_lines.append(line)
                elif line.strip() == "":
                    merged_lines.append("")
                elif line.strip().isdigit():
                    merged_lines.append(str(current_index))
                    current_index += 1
                else:
                    merged_lines.append(line)
            
            # Add blank line between chunks
            if merged_lines and merged_lines[-1] != "":
                merged_lines.append("")
        
        return "\n".join(merged_lines)
    
    def merge_vtt_transcripts(self, vtt_transcripts: list[str]) -> str:
        """Merge VTT files dengan adjusted timestamps"""
        merged_lines = ["WEBVTT\n"]
        time_offset = 0
        
        for vtt_content in vtt_transcripts:
            lines = vtt_content.strip().split("\n")
            
            # Skip WEBVTT header di chunk berikutnya
            start_idx = 1 if lines[0].startswith("WEBVTT") else 0
            
            for line in lines[start_idx:]:
                if " --> " in line:
                    parts = line.split(" --> ")
                    try:
                        start = self._add_time_offset(parts[0].strip(), time_offset)
                        end = self._add_time_offset(parts[1].strip(), time_offset)
                        merged_lines.append(f"{start} --> {end}")
                    except:
                        merged_lines.append(line)
                elif line.strip():
                    merged_lines.append(line)
        
        return "\n".join(merged_lines)
    
    def _add_time_offset(self, time_str: str, offset_ms: int) -> str:
        """Add milliseconds offset to timestamp"""
        # Parse HH:MM:SS.mmm
        match = re.match(r"(\d+):(\d+):(\d+)[.,](\d+)", time_str)
        if not match:
            return time_str
        
        hours, minutes, seconds, millis = map(int, match.groups())
        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + millis
        total_ms += offset_ms
        
        new_hours = total_ms // (3600 * 1000)
        remaining = total_ms % (3600 * 1000)
        new_minutes = remaining // (60 * 1000)
        remaining = remaining % (60 * 1000)
        new_seconds = remaining // 1000
        new_millis = remaining % 1000
        
        return f"{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}.{new_millis:03d}"
    
    def cleanup_chunks(self, chunk_dir: Optional[str] = None):
        """Delete temporary chunk files"""
        if chunk_dir is None:
            chunk_dir = self.temp_dir
        
        chunk_path = Path(chunk_dir)
        for file in chunk_path.glob("*_chunk_*.mp3"):
            file.unlink()
            print(f"Deleted: {file}")
    
    def extract_audio_from_video(self, video_path: str, output_format: str = "mp3") -> str:
        """
        Extract audio dari file video (MP4, MKV, AVI, MOV, dll)
        
        Args:
            video_path: Path ke file video
            output_format: Format output audio (default: mp3)
        
        Returns:
            Path ke file audio yang diekstrak
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Output path dengan ekstensi audio
        audio_path = self.temp_dir / f"{video_path.stem}_extracted.{output_format}"
        
        print(f"Extracting audio from video: {video_path.name}")
        print(f"Output format: {output_format}")
        
        try:
            # Load video file sebagai audio (pydub bisa baca audio dari video)
            video = AudioSegment.from_file(str(video_path))
            
            # Export sebagai audio
            video.export(str(audio_path), format=output_format)
            
            print(f"✓ Audio extracted: {audio_path}")
            print(f"  Duration: {len(video) / 1000:.1f}s")
            print(f"  File size: {audio_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            return str(audio_path)
        
        except Exception as e:
            print(f"✗ Error extracting audio: {e}")
            # Coba alternatif: gunakan librosa untuk baca video
            try:
                print("Trying alternative method with librosa...")
                y, sr = librosa.load(str(video_path), sr=None)
                
                # Simpan sebagai WAV
                import soundfile as sf
                audio_path_wav = self.temp_dir / f"{video_path.stem}_extracted.wav"
                sf.write(str(audio_path_wav), y, sr)
                print(f"✓ Audio extracted (librosa): {audio_path_wav}")
                return str(audio_path_wav)
            except Exception as e2:
                raise Exception(f"Failed to extract audio: {e}, then {e2}")
