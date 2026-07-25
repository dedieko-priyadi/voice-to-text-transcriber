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
from notulen import generate_notulen, format_notulen_markdown


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

# Session state init — persist hasil transcribe antar rerun
if "last_stem" not in st.session_state:
    st.session_state.last_stem = None
if "last_formats" not in st.session_state:
    st.session_state.last_formats = []

# Transcription section
st.divider()
st.subheader("🚀 Transkrip")

if st.button("Mulai Transcription", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.error("❌ Silakan upload file audio terlebih dahulu")
    else:
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                st.error("❌ OPENAI_API_KEY tidak ditemukan. Buat file .env dengan API key Anda.")
            else:
                input_dir = Path("input")
                input_dir.mkdir(exist_ok=True)

                temp_file_path = input_dir / uploaded_file.name
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                st.info(f"📁 File disimpan: {temp_file_path}")

                transcriber = AudioTranscriber(api_key=api_key)
                processor = AudioProcessor()

                progress_bar = st.progress(0)
                status_text = st.empty()

                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)

                if processor.needs_chunking(str(temp_file_path)):
                    status_text.info("⚠️ File >25MB, chunking otomatis...")
                    progress_bar.progress(10)

                    chunks = processor.chunk_audio(
                        str(temp_file_path),
                        chunk_duration_ms=5 * 60 * 1000,
                    )
                    progress_bar.progress(30)

                    all_results = {fmt: [] for fmt in selected_formats}

                    for i, chunk_path in enumerate(chunks):
                        progress = 30 + (i / len(chunks)) * 60
                        progress_bar.progress(int(progress))
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
                st.success("✅ Transcription selesai!")

                # Pin hasil ke session_state agar persist antar rerun
                st.session_state.last_stem = str(temp_file_path.stem)
                st.session_state.last_formats = list(selected_formats)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)

# ── Render hasil dari session_state (persist antar widget interaction) ──
output_dir = Path("output")
if st.session_state.last_stem and st.session_state.last_formats:
    stem = st.session_state.last_stem
    formats = st.session_state.last_formats

    # Results table
    results_data = []
    for fmt in formats:
        output_file = output_dir / f"{stem}.{fmt if fmt != 'verbose_json' else 'json'}"
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
    download_cols = st.columns(len(formats))

    for idx, fmt in enumerate(formats):
        output_file = output_dir / f"{stem}.{fmt if fmt != 'verbose_json' else 'json'}"
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
        options=formats,
        horizontal=True,
        key="preview_format",
    )

    preview_file = output_dir / f"{stem}.{preview_format if preview_format != 'verbose_json' else 'json'}"
    if preview_file.exists():
        with open(preview_file, "r", encoding="utf-8") as f:
            preview_content = f.read()
        if preview_format in ("json", "verbose_json"):
            try:
                st.json(json.loads(preview_content))
            except json.JSONDecodeError:
                st.warning("⚠️ File JSON tidak valid (mungkin hasil transcribe lama). Silakan transcribe ulang.")
                st.text(preview_content[:500])
        else:
            st.text_area(
                f"Transcript ({preview_format.upper()})",
                value=preview_content if preview_content else "(empty)",
                height=300,
                disabled=True,
            )

# ── History section ──

# Notulen section — generate meeting minutes dari transcript
st.divider()
st.subheader("📋 Generate Notulen (Meeting Minutes)")

if st.session_state.last_stem and st.session_state.last_formats:
    stem = st.session_state.last_stem
    
    # Get transcript content
    txt_file = output_dir / f"{stem}.txt"
    if txt_file.exists():
        with open(txt_file, "r", encoding="utf-8") as f:
            transcript_content = f.read()
        
        col_gen, col_opt = st.columns([2, 1])
        
        with col_gen:
            if st.button("🤖 Generate Notulen", use_container_width=True):
                with st.spinner("Generating meeting minutes..."):
                    # Optional inputs
                    meeting_title = st.session_state.get("meeting_title", "Meeting")
                    participants = st.session_state.get("participants", [])
                    
                    minutes = generate_notulen(
                        transcript=transcript_content,
                        title=meeting_title,
                        participants=participants,
                    )
                    
                    if minutes:
                        st.session_state.generated_minutes = minutes
                        st.success("✅ Notulen berhasil dibuat!")
                    else:
                        st.error("❌ Gagal generate notulen. Cek API key & transcript.")
        
        with col_opt:
            st.subheader("⚙️ Opsi")
            st.session_state.meeting_title = st.text_input(
                "Meeting title:",
                value=st.session_state.get("meeting_title", "Untitled Meeting"),
                key="mt_input",
            )
            participants_input = st.text_area(
                "Participants (comma-separated):",
                value=",".join(st.session_state.get("participants", [])),
                key="part_input",
                height=80,
            )
            st.session_state.participants = [p.strip() for p in participants_input.split(",") if p.strip()]
        
        # Display generated notulen
        if "generated_minutes" in st.session_state:
            minutes = st.session_state.generated_minutes
            st.divider()
            
            # Tabs untuk berbagai format
            tab_json, tab_md, tab_download = st.tabs(["📊 JSON", "📝 Markdown", "💾 Download"])
            
            with tab_json:
                st.json(minutes.to_dict())
            
            with tab_md:
                md_content = format_notulen_markdown(minutes)
                st.markdown(md_content)
            
            with tab_download:
                import json as json_lib
                
                # JSON export
                json_data = json_lib.dumps(minutes.to_dict(), indent=2, ensure_ascii=False)
                st.download_button(
                    "📥 Download Notulen (JSON)",
                    data=json_data,
                    file_name=f"{stem}_notulen.json",
                    mime="application/json",
                    use_container_width=True,
                )
                
                # Markdown export
                md_data = format_notulen_markdown(minutes)
                st.download_button(
                    "📥 Download Notulen (Markdown)",
                    data=md_data,
                    file_name=f"{stem}_notulen.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
    else:
        st.info("💡 Transcript belum tersedia. Transcribe audio file terlebih dahulu.")

st.divider()
st.subheader("📜 History")
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
