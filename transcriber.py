"""
OpenAI Audio Transcription Module
Handles calling OpenAI API untuk transcription dengan support berbagai models dan output formats.
Juga support video files dengan automatic audio extraction.
"""

import os
from pathlib import Path
from typing import Optional, Literal
from openai import OpenAI
import json

from audio_processor import AudioProcessor


class AudioTranscriber:
    """Class untuk handle transcription via OpenAI Audio Transcription API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client"""
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Set it in .env file or environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.supported_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        self.processor = AudioProcessor()  # Untuk video extraction
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported (audio atau video)"""
        ext = Path(file_path).suffix.lstrip(".").lower()
        # Support audio files dan video files
        return ext in self.supported_formats or self.processor.is_video_file(file_path)
    
    def is_video_file(self, file_path: str) -> bool:
        """Check if file is a video format"""
        video_extensions = {
            ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", 
            ".webm", ".m4v", ".mpg", ".mpeg", ".3gp"
        }
        ext = Path(file_path).suffix.lower()
        return ext in video_extensions
    
    def ensure_audio_format(self, file_path: str, processor: Optional[object] = None) -> str:
        """
        Ensure file is in supported audio format.
        If it's a video file, extract audio first.
        
        Args:
            file_path: Path to input file (audio or video)
            processor: Optional AudioProcessor instance
        
        Returns:
            Path to audio file (may be extracted from video)
        """
        file_path = str(file_path)
        
        # If already supported audio format, return as-is
        if self.is_supported_format(file_path):
            return file_path
        
        # If it's a video file, extract audio
        if self.is_video_file(file_path):
            if processor is None:
                from audio_processor import AudioProcessor
                processor = AudioProcessor()
            
            print(f"⚠️  Detected video file: {Path(file_path).name}")
            print("Extracting audio...")
            audio_path = processor.extract_audio_from_video(file_path)
            return audio_path
        
        # Unsupported format
        raise ValueError(
            f"Unsupported file format: {Path(file_path).suffix}\n"
            f"Supported audio: {self.supported_formats}\n"
            f"Supported video: .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm, .m4v"
        )
    
    def transcribe(
        self,
        audio_path: str,
        model: str = "gpt-4o-transcribe",
        response_format: Literal["text", "json", "verbose_json", "srt", "vtt"] = "text",
        language: Optional[str] = "id",  # Indonesia
        prompt: Optional[str] = None,
    ) -> str:
        """
        Transcribe audio file using OpenAI API
        Support video files dengan automatic audio extraction.
        
        Args:
            audio_path: Path to audio file atau video file
            model: Model to use (gpt-4o-transcribe, gpt-4o-transcribe-diarize, whisper-1)
            response_format: Output format
            language: Language code (default: id untuk Indonesia)
            prompt: Optional prompt for context
        
        Returns:
            Transcription result as string
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"File not found: {audio_path}")
        
        if not self.is_supported_format(audio_path):
            raise ValueError(f"Unsupported format. Supported audio: {self.supported_formats}, video: mp4, avi, mov, mkv, dll")
        
        # Handle video files - extract audio dulu
        if self.processor.is_video_file(audio_path):
            print(f"📹 Video file detected, extracting audio...")
            audio_path = self.processor.extract_audio_from_video(audio_path)
        
        # Check if audio duration exceeds model limits (for non-whisper models)
        if model in ["gpt-4o-transcribe", "gpt-4o-transcribe-diarize"]:
            duration = self.processor.get_audio_duration(audio_path)
            if duration and duration > 1400:
                raise ValueError(
                    f"Audio duration ({duration:.1f}s) exceeds {model} limit (1400s). "
                    f"Please use duration-based chunking or switch to whisper-1 model."
                )
        
        print(f"Transcribing: {audio_path}")
        print(f"Model: {model}, Format: {response_format}")
        
        with open(audio_path, "rb") as audio_file:
            # Prepare kwargs based on model dan format
            kwargs = {
                "model": model,
                "file": audio_file,
                "response_format": response_format,
            }
            
            # Add language for models yang support
            if model in ["gpt-4o-transcribe", "whisper-1"]:
                kwargs["language"] = language
            
            # Add prompt if provided
            if prompt and model in ["gpt-4o-transcribe", "whisper-1"]:
                kwargs["prompt"] = prompt
            
            transcript = self.client.audio.transcriptions.create(**kwargs)
        
        # Return hasil sesuai format
        if isinstance(transcript, str):
            return transcript
        elif hasattr(transcript, "text"):
            return transcript.text
        else:
            return str(transcript)
    
    def transcribe_and_save(
        self,
        audio_path: str,
        output_dir: str = "output",
        model: str = "gpt-4o-transcribe",
        response_formats: list[str] = None,
        language: Optional[str] = "id",
    ) -> dict[str, str]:
        """
        Transcribe dan save hasil ke multiple formats
        Support video files dengan automatic audio extraction.
        
        Args:
            audio_path: Path ke audio file atau video file
            output_dir: Directory untuk save hasil
            model: Model yang dipakai
            response_formats: List of formats to save (default: ["text", "json"])
            language: Language code
        
        Returns:
            Dict berisi path hasil files
        """
        if response_formats is None:
            response_formats = ["text", "json"]
        
        # Handle video files - extract audio dulu
        if self.processor.is_video_file(audio_path):
            print(f"📹 Video file detected, extracting audio...")
            audio_path = self.processor.extract_audio_from_video(audio_path)
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        audio_stem = Path(audio_path).stem
        results = {}
        
        for fmt in response_formats:
            try:
                print(f"  Generating {fmt.upper()}...", end=" ")
                
                transcript = self.transcribe(
                    audio_path,
                    model=model,
                    response_format=fmt,
                    language=language,
                )
                
                # Determine output file extension
                ext_map = {
                    "text": "txt",
                    "json": "json",
                    "verbose_json": "json",
                    "srt": "srt",
                    "vtt": "vtt",
                }
                ext = ext_map.get(fmt, fmt)
                
                output_file = output_path / f"{audio_stem}.{ext}"
                
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(transcript)
                
                results[fmt] = str(output_file)
                print(f"✓ Saved: {output_file}")
            
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                results[fmt] = None
        
        return results
