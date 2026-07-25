"""
Meeting Minutes Generator — LLM-based notulen creation dari transcript.
Menggunakan OpenAI (atau 9router jika tersedia).
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# ── Config (lazy load dari env) ──────────────────────────────
from dotenv import load_dotenv
load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://pc-amd7900x.tail758353.ts.net/ugmrouter/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# ── Data Models ────────────────────────────────────────────────────

@dataclass
class DiscussionPoint:
    """Satu topik diskusi dalam rapat."""
    topic: str
    summary: str
    decisions: list[str]
    action_items: list[str]


@dataclass
class ActionItem:
    """Item action dengan PIC dan deadline."""
    description: str
    pic: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "pending"


@dataclass
class MeetingMinutes:
    """Struktur notulen lengkap."""
    title: str
    date: str
    participants: list[str]
    executive_summary: str
    discussion_points: list[DiscussionPoint]
    action_items: list[ActionItem]
    next_meeting: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert ke dict untuk JSON serialization."""
        return {
            "title": self.title,
            "date": self.date,
            "participants": self.participants,
            "executive_summary": self.executive_summary,
            "discussion_points": [
                {
                    "topic": dp.topic,
                    "summary": dp.summary,
                    "decisions": dp.decisions,
                    "action_items": dp.action_items,
                }
                for dp in self.discussion_points
            ],
            "action_items": [
                {
                    "description": ai.description,
                    "pic": ai.pic,
                    "deadline": ai.deadline,
                    "status": ai.status,
                }
                for ai in self.action_items
            ],
            "next_meeting": self.next_meeting,
            "notes": self.notes,
        }


# ── LLM Prompts ────────────────────────────────────────────────────

SYSTEM_PROMPT = """Kamu adalah asisten pembuat notulen rapat profesional.
Tugasmu: menganalisis transcript diskusi dan menghasilkan notulen struktural.

Output HARUS berupa JSON valid dengan struktur:
{
  "executive_summary": "Ringkasan singkat (2-3 paragraf) isi rapat",
  "discussion_points": [
    {
      "topic": "Topik diskusi",
      "summary": "Inti pembahasan",
      "decisions": ["Keputusan 1", "Keputusan 2"],
      "action_items": ["Aksi 1: siapa", "Aksi 2: siapa"]
    }
  ],
  "action_items": [
    {
      "description": "Tugas spesifik",
      "pic": "Nama PIC (jika ada)",
      "deadline": "Deadline (jika disebutkan)"
    }
  ],
  "next_meeting": "Waktu rapat berikutnya (jika disebutkan)"
}

Aturan:
- Ekstrak hanya informasi FAKTUAL dari transcript
- Jangan invention atau hallucination
- Gunakan bahasa formal tapi natural (Bahasa Indonesia)
- Deadline format: YYYY-MM-DD atau deskripsi (e.g. "2 minggu", "akhir bulan")
- Jika info tidak ada, gunakan null
- HANYA output JSON, tanpa teks lain"""


def _call_llm(user_prompt: str) -> str | None:
    """Panggil LLM via 9router, return response atau None."""
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("openai package not installed")
        return None

    if not LLM_API_KEY:
        logger.error("LLM_API_KEY not set")
        return None

    try:
        client = OpenAI(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
            timeout=60.0,
        )
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        content = resp.choices[0].message.content
        # DeepSeek reasoning models put content in reasoning_content
        if not content:
            reasoning = getattr(resp.choices[0].message, 'reasoning_content', None)
            if reasoning:
                content = reasoning
        if content:
            content = content.strip()
            logger.info("LLM notulen generated: %d chars", len(content))
            return content
        logger.error("LLM returned empty content")
        return None
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return None


# ── Main API ───────────────────────────────────────────────────────

def generate_notulen(
    transcript: str,
    title: str = "Untitled Meeting",
    participants: list[str] | None = None,
) -> Optional[MeetingMinutes]:
    """
    Generate notulen dari transcript.

    Args:
        transcript: Full meeting transcript
        title: Judul rapat
        participants: List nama peserta (optional)

    Returns:
        MeetingMinutes object atau None jika LLM gagal
    """
    if not transcript or len(transcript.strip()) < 100:
        logger.warning("Transcript terlalu pendek")
        return None

    user_prompt = f"""Analisis transcript rapat berikut dan generate notulen:

JUDUL RAPAT: {title}
PESERTA: {', '.join(participants) if participants else 'Tidak disebutkan'}

TRANSCRIPT:
{transcript}

Generate notulen dalam JSON format sesuai struktur yang diminta."""

    response = _call_llm(user_prompt)
    if not response:
        return None

    # Parse JSON
    try:
        # Bersihkan markdown wrapper jika ada
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
            if response.endswith("```"):
                response = response[:-3]

        data = json.loads(response)

        # Build MeetingMinutes object
        discussion_points = [
            DiscussionPoint(
                topic=dp.get("topic", ""),
                summary=dp.get("summary", ""),
                decisions=dp.get("decisions", []),
                action_items=dp.get("action_items", []),
            )
            for dp in data.get("discussion_points", [])
        ]

        action_items = [
            ActionItem(
                description=ai.get("description", ""),
                pic=ai.get("pic"),
                deadline=ai.get("deadline"),
            )
            for ai in data.get("action_items", [])
        ]

        minutes = MeetingMinutes(
            title=title,
            date=datetime.now().isoformat(),
            participants=participants or [],
            executive_summary=data.get("executive_summary", ""),
            discussion_points=discussion_points,
            action_items=action_items,
            next_meeting=data.get("next_meeting"),
        )

        logger.info("Notulen generated: %d points, %d actions", 
                    len(discussion_points), len(action_items))
        return minutes

    except json.JSONDecodeError as e:
        logger.error("LLM response not valid JSON: %s\nResponse: %s", e, response[:200])
        return None
    except Exception as e:
        logger.error("Failed to parse notulen: %s", e)
        return None


def format_notulen_markdown(minutes: MeetingMinutes) -> str:
    """Format notulen sebagai Markdown."""
    md = f"""# {minutes.title}

**Tanggal:** {minutes.date}
**Peserta:** {', '.join(minutes.participants) if minutes.participants else 'N/A'}

---

## Ringkasan Eksekutif

{minutes.executive_summary}

---

## Poin Diskusi

"""
    for i, dp in enumerate(minutes.discussion_points, 1):
        md += f"""
### {i}. {dp.topic}

**Ringkasan:** {dp.summary}

**Keputusan:**
"""
        for dec in dp.decisions:
            md += f"- {dec}\n"
        if dp.action_items:
            md += "\n**Action Items:**\n"
            for ai in dp.action_items:
                md += f"- {ai}\n"

    md += "\n---\n\n## Action Items\n"
    for ai in minutes.action_items:
        pic_str = f" ({ai.pic})" if ai.pic else ""
        deadline_str = f" — Deadline: {ai.deadline}" if ai.deadline else ""
        md += f"- [ ] {ai.description}{pic_str}{deadline_str}\n"

    if minutes.next_meeting:
        md += f"\n---\n\n**Rapat Berikutnya:** {minutes.next_meeting}\n"

    return md


# ── Test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_transcript = """
    Rapat team engineering, 25 Juli 2026.
    
    Moderator: Hari ini kita bahas progress sprint 12 dan planning sprint 13.
    Adi: Voice-to-text project sudah 80% done, tinggal integration testing.
    Bayu: Backend API untuk chatbot DSH sudah ready, testing minggu depan.
    Adi: Untuk voice-to-text, kita perlu add notulen feature. Bisa pakai OpenAI API?
    Bayu: Bisa, tapi lebih hemat pakai 9router yang sudah ada. Deadline akhir bulan depan?
    Adi: Oke, setuju. Aku handle implementation, Bayu tolong code review.
    Moderator: Baik, meeting next Tuesday, 8 AM.
    """

    minutes = generate_notulen(
        transcript=sample_transcript,
        title="Sprint Planning 12-13",
        participants=["Moderator", "Adi", "Bayu"],
    )

    if minutes:
        print("=== Notulen JSON ===")
        print(json.dumps(minutes.to_dict(), indent=2))
        print("\n=== Notulen Markdown ===")
        print(format_notulen_markdown(minutes))
    else:
        print("Failed to generate notulen")
