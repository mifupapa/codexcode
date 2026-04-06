"""TTS（テキスト音声合成）サービス。
優先: gTTS（無料、インターネット必要）
オプション: Google Cloud TTS（高品質、要APIキー）
"""
from __future__ import annotations
import os
from pathlib import Path


def run_tts(text: str, output_path: str | Path, language: str = "ja") -> str:
    """テキストを音声合成して MP3 ファイルを保存。保存パスを返す。"""
    engine = os.getenv("TTS_ENGINE", "gtts").lower()
    if not text.strip():
        raise ValueError("テキストが空のため音声を生成できません。")

    if engine == "cloud_tts":
        try:
            return _cloud_tts(text, output_path, language)
        except Exception as e:
            print(f"[TTS] Google Cloud TTS 失敗、gTTS にフォールバック: {e}")

    return _gtts(text, output_path, language)


# ────────────────────────────────────────────
# gTTS（無料）
# ────────────────────────────────────────────

def _gtts(text: str, output_path: str | Path, language: str) -> str:
    try:
        from gtts import gTTS  # type: ignore
    except ImportError:
        raise RuntimeError("gTTS がインストールされていません。pip install gtts を実行してください。")

    tts = gTTS(text=text, lang=language, slow=False)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tts.save(str(out))
    return str(out)


# ────────────────────────────────────────────
# Google Cloud TTS（高品質）
# ────────────────────────────────────────────

def _cloud_tts(text: str, output_path: str | Path, language: str) -> str:
    from google.cloud import texttospeech  # type: ignore

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=f"{language}-JP" if language == "ja" else language,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(response.audio_content)
    return str(out)
