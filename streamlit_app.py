"""
Streamlit Web UI untuk Voice-to-Text Transcriber
Interface untuk upload, transcribe, dan download hasil audio transcription.
"""

import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from datetime import datetime

from transcriber import AudioTranscriber
from audio_processor import AudioProcessor


# Load environment variables
load_dotenv()

# Streamlit page config
st.set_page_config(
    page_title="Voice-to-Text Transcriber",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        padding: 10px;
    }
    .success-box {
        padding: 15px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 15px;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🎤 Voice-to-Text Transcriber")
st.write("Transkrip file audio menggunakan OpenAI Audio Transcription API")

# Sidebar config
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    
    model = st.selectbox(
        "Pilih Model",
        options=[
            "gpt-4o-transcribe",
            "gpt-4o-transcribe-diarize",
            "whisper-1",
        ],
        help="gpt-4o-transcribe: Kualitas terbaik\ngpt-4o-transcribe-diarize: Multi-speaker\nwhisper-1: Format lebih banyak",
    )
    
    # Output format berdasar model
    if model == "gpt-4o-transcribe":
        format_options = ["text", "json"]
    elif model == "gpt-4o-transcribe-diarize":
        format_options = ["text", "json"]
    else:  # whisper-1
        format_options = ["text", "json", "verbose_json", "srt", "vtt"]
    
    selected_formats = st.multiselect(
        "Output Format",
        options=format_options,
        default=["text", "json"],
        help="Format file output hasil transkrip",
    )
    
    language = st.selectbox(
        "Bahasa",
        options=["id", "en", "es", "fr", "de", "ja", "zh"],
        index=0,
        help="Bahasa audio untuk optimasi transkrip",
    )
    
    use_prompt = st.checkbox("Gunakan Custom Prompt", value=False)
    custom_prompt = None
    if use_prompt:
        custom_prompt = st.text_area(
            "Prompt (opsional)",
            placeholder="Contoh: Ini adalah rapat office...",
            help="Konteks untuk meningkatkan akurasi",
        )
    
    st.divider()
    st.subheader("ℹ️ Informasi")
    st.info("""
    **File Size Limit**: 25MB per transkrip
    
    **Supported Formats**: MP3, MP4, MPEG, MPGA, M4A, WAV, WebM
    
    **Fitur**: Auto-chunking untuk file besar, multiple output formats
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📁 Upload Audio File")
    
    uploaded_file = st.file_uploader(
        "Pilih file audio",
        type=["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"],
        help="Max file size: 25MB (akan di-chunk otomatis jika lebih besar)",
    )
    
    if uploaded_file is not None:
        st.write(f"✓ File: **{uploaded_file.name}**")
        st.write(f"✓ Size: **{uploaded_file.size / 1024 / 1024:.2f} MB**")

with col2:
    st.subheader("📊 Status")
    placeholder_status = st.empty()

# Transcription section
st.divider()
st.subheader("🚀 Transkrip")

if st.button("Mulai Transcription", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.error("❌ Silakan upload file audio terlebih dahulu")
    else:
        try:
            # Initialize
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                st.error("❌ OPENAI_API_KEY tidak ditemukan. Buat file .env dengan API key Anda.")
            else:
                # Save uploaded file
                input_dir = Path("input")
                input_dir.mkdir(exist_ok=True)
                
                temp_file_path = input_dir / uploaded_file.name
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.info(f"📁 File disimpan: {temp_file_path}")
                
                # Initialize transcriber
                transcriber = AudioTranscriber(api_key=api_key)
                processor = AudioProcessor()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                output_placeholder = st.empty()
                
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                
                # Check if chunking needed
                if processor.needs_chunking(str(temp_file_path)):
                    status_text.info(f"⚠️ File >25MB, chunking otomatis...")
                    progress_bar.progress(10)
                    
                    chunks = processor.chunk_audio(
                        str(temp_file_path),
                        chunk_duration_ms=5 * 60 * 1000,  # 5 menit
                    )
                    progress_bar.progress(30)
                    
                    # Transcribe each chunk
                    all_results = {}
                    for fmt in selected_formats:
                        all_results[fmt] = []
                    
                    for i, chunk_path in enumerate(chunks):
                        progress = 30 + (i / len(chunks)) * 60
                        progress_bar.progress(progress)
                        
                        status_text.info(f"📝 Transcribing chunk {i+1}/{len(chunks)}...")
                        
                        chunk_transcripts = transcriber.transcribe_and_save(
                            chunk_path,
                            output_dir=str(output_dir),
                            model=model,
                            response_formats=selected_formats,
                            language=language,
                        )
                        
                        for fmt, transcript in chunk_transcripts.items():
                            if transcript:
                                with open(transcript, "r", encoding="utf-8") as f:
                                    all_results[fmt].append(f.read())
                    
                    progress_bar.progress(95)
                    
                    # Merge results
                    status_text.info("🔗 Menggabungkan hasil chunks...")
                    audio_stem = temp_file_path.stem
                    
                    for fmt in selected_formats:
                        if fmt == "text":
                            merged = processor.merge_text_transcripts(all_results[fmt])
                            output_file = output_dir / f"{audio_stem}.txt"
                        elif fmt == "json":
                            merged_json = processor.merge_json_transcripts(all_results[fmt])
                            merged = json.dumps(merged_json, ensure_ascii=False, indent=2)
                            output_file = output_dir / f"{audio_stem}.json"
                        elif fmt == "srt":
                            merged = processor.merge_srt_transcripts(all_results[fmt])
                            output_file = output_dir / f"{audio_stem}.srt"
                        elif fmt == "vtt":
                            merged = processor.merge_vtt_transcripts(all_results[fmt])
                            output_file = output_dir / f"{audio_stem}.vtt"
                        else:
                            continue
                        
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(merged)
                    
                    processor.cleanup_chunks()
                
                else:
                    # File < 25MB, langsung transcribe
                    status_text.info(f"📝 Transcribing {uploaded_file.name}...")
                    progress_bar.progress(50)
                    
                    results = transcriber.transcribe_and_save(
                        str(temp_file_path),
                        output_dir=str(output_dir),
                        model=model,
                        response_formats=selected_formats,
                        language=language,
                    )
                    
                    progress_bar.progress(90)
                
                progress_bar.progress(100)
                status_text.empty()
                
                # Show results
                st.success("✅ Transcription selesai!")
                
                results_data = []
                for fmt in selected_formats:
                    output_file = output_dir / f"{temp_file_path.stem}.{fmt if fmt != 'verbose_json' else 'json'}"
                    if output_file.exists():
                        file_size = output_file.stat().st_size
                        results_data.append({
                            "Format": fmt.upper(),
                            "File": output_file.name,
                            "Size": f"{file_size / 1024:.2f} KB",
                        })
                
                st.dataframe(results_data, use_container_width=True, hide_index=True)
                
                # Download buttons
                st.subheader("📥 Download Hasil")
                download_cols = st.columns(len(selected_formats))
                
                for idx, fmt in enumerate(selected_formats):
                    output_file = output_dir / f"{temp_file_path.stem}.{fmt if fmt != 'verbose_json' else 'json'}"
                    
                    if output_file.exists():
                        with open(output_file, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        
                        with download_cols[idx]:
                            st.download_button(
                                label=f"📄 {fmt.upper()}",
                                data=file_content,
                                file_name=output_file.name,
                                mime="text/plain" if fmt == "text" else "application/json",
                                use_container_width=True,
                            )
                
                # Preview
                st.divider()
                st.subheader("👁️ Preview Transcript")
                
                preview_format = st.radio(
                    "Format preview:",
                    options=selected_formats,
                    horizontal=True,
                )
                
                preview_file = output_dir / f"{temp_file_path.stem}.{preview_format if preview_format != 'verbose_json' else 'json'}"
                if preview_file.exists():
                    with open(preview_file, "r", encoding="utf-8") as f:
                        preview_content = f.read()
                    
                    if preview_format == "json" or preview_format == "verbose_json":
                        st.json(json.loads(preview_content))
                    else:
                        st.text_area(
                            f"Transcript ({preview_format.upper()})",
                            value=preview_content,
                            height=300,
                            disabled=True,
                        )
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)

# History section
st.divider()
st.subheader("📜 Transcript History")

output_dir = Path("output")
if output_dir.exists():
    files = sorted(output_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if files:
        history_data = []
        for file in files[:10]:  # Show latest 10
            file_size = file.stat().st_size
            mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            history_data.append({
                "File": file.name,
                "Size": f"{file_size / 1024:.2f} KB",
                "Modified": mod_time,
            })
        
        st.dataframe(history_data, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada transcript. Upload dan transcribe file audio untuk mulai.")
else:
    st.info("Belum ada transcript. Upload dan transcribe file audio untuk mulai.")
