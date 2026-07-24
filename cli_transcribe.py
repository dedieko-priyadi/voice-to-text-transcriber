"""
CLI Script untuk Voice-to-Text Transcription
Jalankan: python cli_transcribe.py <audio_atau_video_file> [--model] [--formats]
Support: Audio files (MP3, WAV, M4A, dll) dan Video files (MP4, AVI, MOV, dll)
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from transcriber import AudioTranscriber
from audio_processor import AudioProcessor


def main():
    # Load environment
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Transcribe audio atau video file menggunakan OpenAI API. Otomatis ekstrak audio dari video.",
    )
    parser.add_argument("audio_file", help="Path ke audio file (MP3, WAV, M4A, dll) atau video file (MP4, AVI, MOV, dll)")
    parser.add_argument(
        "--model",
        default="gpt-4o-transcribe",
        choices=["gpt-4o-transcribe", "gpt-4o-transcribe-diarize", "whisper-1"],
        help="Model transcription (default: gpt-4o-transcribe)",
    )
    parser.add_argument(
        "--formats",
        default="text,json",
        help="Output formats separated by comma (default: text,json)",
    )
    parser.add_argument(
        "--language",
        default="id",
        help="Language code (default: id untuk Indonesia)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output)",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Optional prompt untuk konteks",
    )
    
    args = parser.parse_args()
    
    # Validate audio file
    audio_path = Path(args.audio_file)
    if not audio_path.exists():
        print(f"❌ Error: File not found: {args.audio_file}")
        sys.exit(1)
    
    # Parse formats
    formats = [fmt.strip() for fmt in args.formats.split(",")]
    
    # Initialize
    transcriber = AudioTranscriber()
    processor = AudioProcessor()
    
    print(f"🎤 Voice-to-Text Transcriber")
    print(f"📁 File: {audio_path.name}")
    print(f"📊 Model: {args.model}")
    print(f"📝 Formats: {', '.join(formats)}")
    print(f"🌍 Language: {args.language}")
    print()
    
    try:
        # IMPORTANT: Extract audio FIRST, then check file size
        file_to_process = str(audio_path)
        original_filename = audio_path.stem  # Simpan nama file asli untuk output
        
        print(f"📋 Analyzing file: {Path(file_to_process).name}")
        
        # Step 1: Ekstrak audio dari video DULU (sebelum cek ukuran)
        # Cek apakah file itu video atau file tanpa extension
        is_video = processor.is_video_file(file_to_process)
        has_no_extension = Path(file_to_process).suffix == ""
        
        if is_video or has_no_extension:
            print("📹 Detected video file or no extension - extracting audio...")
            try:
                extracted_audio = processor.extract_audio_from_video(file_to_process)
                file_to_process = extracted_audio
                print(f"✓ Audio extracted successfully")
            except Exception as e:
                print(f"⚠️  Extraction attempt failed: {str(e)}")
                print("Proceeding with original file...")
        
        # Step 2: Check if audio file needs chunking (SETELAH ekstraksi)
        needs_size_chunking = processor.needs_chunking(file_to_process)
        needs_duration_chunking = processor.needs_duration_chunking(file_to_process, model=args.model)
        
        if needs_size_chunking or needs_duration_chunking:
            if needs_duration_chunking:
                print(f"⚠️  Audio duration exceeds {args.model} limit (1400s), chunking by duration...")
                # Use 1200s chunks to stay safely within the 1400s model limit
                chunks = processor.chunk_audio_by_duration(
                    file_to_process,
                    max_duration_sec=1200,
                )
            else:
                print("⚠️  File >25MB, chunking otomatis...")
                chunks = processor.chunk_audio(
                    file_to_process,
                    chunk_duration_ms=5 * 60 * 1000,
                )
            
            # Transcribe chunks
            all_results = {fmt: [] for fmt in formats}
            
            for i, chunk_path in enumerate(chunks):
                print(f"\n📝 Transcribing chunk {i+1}/{len(chunks)}...")
                
                chunk_results = transcriber.transcribe_and_save(
                    chunk_path,
                    output_dir=args.output,
                    model=args.model,
                    response_formats=formats,
                    language=args.language,
                )
                
                for fmt, transcript_path in chunk_results.items():
                    if transcript_path:
                        with open(transcript_path, "r", encoding="utf-8") as f:
                            all_results[fmt].append(f.read())
            
            print(f"\n🔗 Merging chunks...")
            
            # Merge results
            output_path = Path(args.output)
            output_path.mkdir(exist_ok=True)
            
            import json
            for fmt in formats:
                if fmt == "text":
                    merged = processor.merge_text_transcripts(all_results[fmt])
                    output_file = output_path / f"{original_filename}.txt"
                elif fmt == "json":
                    merged_json = processor.merge_json_transcripts(all_results[fmt])
                    merged = json.dumps(merged_json, ensure_ascii=False, indent=2)
                    output_file = output_path / f"{original_filename}.json"
                elif fmt == "srt":
                    merged = processor.merge_srt_transcripts(all_results[fmt])
                    output_file = output_path / f"{original_filename}.srt"
                elif fmt == "vtt":
                    merged = processor.merge_vtt_transcripts(all_results[fmt])
                    output_file = output_path / f"{original_filename}.vtt"
                else:
                    continue
                
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(merged)
                
                print(f"✓ Saved: {output_file}")
            
            processor.cleanup_chunks()
        
        else:
            # Direct transcription (file < 25MB)
            print("Transcribing...")
            results = transcriber.transcribe_and_save(
                file_to_process,
                output_dir=args.output,
                model=args.model,
                response_formats=formats,
                language=args.language,
            )
            
            print()
            for fmt, output_file in results.items():
                if output_file:
                    print(f"✓ {fmt.upper()}: {output_file}")
                else:
                    print(f"✗ {fmt.upper()}: Failed")
        
        print("\n✅ Done!")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
