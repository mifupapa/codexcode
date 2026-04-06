"""TTS service.
Primary  : AivisSpeech (local, high quality, VOICEVOX-compatible API)
Fallback : gTTS (online, free)
"""
from __future__ import annotations
import io
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

AIVIS_HOST = os.getenv("AIVIS_HOST", "http://127.0.0.1:10101")
AIVIS_SPEAKER = int(os.getenv("AIVIS_SPEAKER", "0"))  # style_id


def run_tts(text: str, output_path: str | Path, language: str = "ja") -> str:
    """Synthesize text to audio file. Returns the saved file path."""
    engine = os.getenv("TTS_ENGINE", "aivis").lower()
    if not text.strip():
        raise ValueError("Text is empty.")

    if engine == "aivis":
        try:
            return _aivis_tts(text, output_path)
        except Exception as e:
            print(f"[TTS] AivisSpeech failed, falling back to gTTS: {e}")

    return _gtts(text, output_path, language)


# ──────────────────────────────────────────────
# AivisSpeech (VOICEVOX-compatible API)
# ──────────────────────────────────────────────

def _aivis_tts(text: str, output_path: str | Path) -> str:
    speaker = AIVIS_SPEAKER

    # Step 1: audio_query
    url_query = f"{AIVIS_HOST}/audio_query?speaker={speaker}"
    req1 = urllib.request.Request(
        url_query,
        data=json.dumps(text).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp1 = urllib.request.urlopen(req1, timeout=30)
    except urllib.error.URLError:
        raise RuntimeError(
            "AivisSpeech Engine is not running. "
            "Start AivisSpeech first, then retry."
        )
    audio_query = json.loads(resp1.read())

    # Step 2: synthesis
    url_synth = f"{AIVIS_HOST}/synthesis?speaker={speaker}"
    req2 = urllib.request.Request(
        url_synth,
        data=json.dumps(audio_query).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp2 = urllib.request.urlopen(req2, timeout=120)
    wav_data = resp2.read()

    # Save as WAV (AivisSpeech returns WAV)
    out = Path(output_path)
    # Change extension to .wav
    out = out.with_suffix(".wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(wav_data)
    return str(out)


def get_speakers() -> list[dict]:
    """Get available speakers from AivisSpeech."""
    url = f"{AIVIS_HOST}/speakers"
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        return json.loads(resp.read())
    except Exception:
        return []


def is_aivis_running() -> bool:
    """Check if AivisSpeech Engine is running."""
    try:
        urllib.request.urlopen(f"{AIVIS_HOST}/version", timeout=3)
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────
# gTTS (online fallback)
# ──────────────────────────────────────────────

def _gtts(text: str, output_path: str | Path, language: str) -> str:
    try:
        from gtts import gTTS  # type: ignore
    except ImportError:
        raise RuntimeError("gTTS not installed. Run: pip install gtts")

    tts = gTTS(text=text, lang=language, slow=False)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tts.save(str(out))
    return str(out)
