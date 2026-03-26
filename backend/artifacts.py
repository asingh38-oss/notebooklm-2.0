"""
backend/artifacts.py
--------------------
Generate notebook artifacts: report, quiz, and podcast (transcript + optional audio).
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import openai

from backend import storage

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_PODCAST_VOICE = os.getenv("OPENAI_PODCAST_VOICE", "alloy")


def _get_extracted_text(username: str, nb_id: str) -> str:
    folder = Path(storage.notebook_dir(username, nb_id)) / "files_extracted"
    if not folder.exists():
        return ""

    segments = []
    for path in sorted(folder.glob("*.txt")):
        try:
            segments.append(path.read_text(encoding="utf-8", errors="ignore").strip())
        except Exception:
            continue

    return "\n\n".join([s for s in segments if s])


def _ensure_openai_key() -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set. Set it in your environment variables.")
    openai.api_key = OPENAI_API_KEY


def _openai_chat(messages, model: str = OPENAI_MODEL, max_tokens: int = 1100):
    _ensure_openai_key()
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.22,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def _generate_from_content(username: str, nb_id: str, prompt: str) -> str:
    content = _get_extracted_text(username, nb_id)
    if not content:
        return "_No source content indexed yet. Upload a file or URL in Sources to generate artifacts._"

    # Limit the content to avoid model context overflow while retaining variety.
    if len(content) > 32000:
        content = content[:32000] + "\n\n[truncated]"

    messages = [
        {
            "role": "system",
            "content": "You are an assistant that produces clean Markdown artifacts from a set of user notes and documents.",
        },
        {
            "role": "user",
            "content": f"The user notebook contains the following text:\n\n{content}\n\n{prompt}",
        },
    ]

    return _openai_chat(messages)


def generate_report(nb_id: str, username: str) -> str:
    """Generate a study report for the selected notebook."""
    prompt = (
        "Create a Markdown study report with sections: Overview, Key Concepts, "
        "Important Details, and Suggested Next Steps. Keep it concise and clearly formatted."
    )

    report_md = _generate_from_content(username, nb_id, prompt)

    try:
        storage.save_artifact(username, nb_id, "reports", report_md, extension="md")
    except Exception:
        pass

    return report_md


def generate_quiz(nb_id: str, username: str) -> str:
    """Generate a quiz for the selected notebook."""
    prompt = (
        "Create an 8-question multiple-choice quiz (with answers) based on the notebook text. "
        "Format as Markdown with question numbers, four options each (A-D), and an answer key at the end."
    )

    quiz_md = _generate_from_content(username, nb_id, prompt)

    try:
        storage.save_artifact(username, nb_id, "quizzes", quiz_md, extension="md")
    except Exception:
        pass

    return quiz_md


def _generate_podcast_transcript(nb_id: str, username: str) -> str:
    prompt = (
        "Produce a friendly podcast transcript (~600-900 words) to teach this content. "
        "Include an intro, 3 main points, short examples, and a closing takeaway. "
        "Use a conversational tone as if two hosts are discussing."
    )

    transcript_md = _generate_from_content(username, nb_id, prompt)
    return transcript_md


def _create_tts_audio(text: str, output_path: Path) -> Optional[str]:
    try:
        _ensure_openai_key()

        if hasattr(openai, "Audio"):
            # New OpenAI library has audio endpoint as openai.Audio.speech.create
            audio_resp = openai.Audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=OPENAI_PODCAST_VOICE,
                input=text,
            )
            if hasattr(audio_resp, "content"):
                output_path.write_bytes(audio_resp.content)
                return str(output_path)
            if isinstance(audio_resp, dict) and audio_resp.get("b64_json"):
                import base64

                data = base64.b64decode(audio_resp["b64_json"])
                output_path.write_bytes(data)
                return str(output_path)

        # fallback to no audio if API not capable
        return None
    except Exception:
        return None


def generate_podcast(nb_id: str, username: str) -> Tuple[str, Optional[str]]:
    """Generate a podcast transcript (and optional audio file)."""
    transcript = _generate_podcast_transcript(nb_id, username)

    try:
        storage.save_artifact(username, nb_id, "podcasts", transcript, extension="md")
    except Exception:
        pass

    # Attempt TTS output if OpenAI supports it.
    out_dir = Path(storage.notebook_dir(username, nb_id)) / "artifacts" / "podcasts"
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_path = out_dir / "podcast_1.mp3"

    tts_result = _create_tts_audio(transcript, audio_path)

    return transcript, tts_result
