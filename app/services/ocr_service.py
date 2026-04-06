"""OCR サービス。
優先: Google Cloud Vision API（縦書き日本語に最適）
フォールバック: pytesseract（オフライン、Tesseract インストール必須）
"""
from __future__ import annotations
import os
import re
from pathlib import Path


def run_ocr(image_path: str | Path, language: str = "ja") -> str:
    """画像からテキストを抽出して返す。"""
    engine = os.getenv("OCR_ENGINE", "vision").lower()
    if engine == "vision":
        try:
            return _vision_ocr(image_path, language)
        except Exception as e:
            print(f"[OCR] Google Vision 失敗、tesseract にフォールバック: {e}")
    return _tesseract_ocr(image_path, language)


# ────────────────────────────────────────────
# Google Cloud Vision API
# ────────────────────────────────────────────

def _vision_ocr(image_path: str | Path, language: str) -> str:
    from google.cloud import vision  # type: ignore

    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)

    # image_context で縦書き日本語を明示
    image_context = vision.ImageContext(
        language_hints=[language],
    )

    response = client.document_text_detection(
        image=image,
        image_context=image_context,
    )

    if response.error.message:
        raise RuntimeError(f"Vision API エラー: {response.error.message}")

    text = response.full_text_annotation.text
    return _clean_text(text)


# ────────────────────────────────────────────
# pytesseract（フォールバック）
# ────────────────────────────────────────────

def _tesseract_ocr(image_path: str | Path, language: str) -> str:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        raise RuntimeError(
            "pytesseract または Pillow がインストールされていません。"
            "pip install pytesseract pillow を実行してください。"
        )

    # Tesseract が PATH にない場合（Windows）
    tesseract_cmd = os.getenv("TESSERACT_CMD", "")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    # 言語マッピング
    lang_map = {"ja": "jpn_vert+jpn", "en": "eng"}
    tess_lang = lang_map.get(language, "jpn_vert+jpn")

    # 縦書き用設定
    custom_config = "--psm 5"  # psm 5 = Assume a single uniform block of vertically aligned text

    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang=tess_lang, config=custom_config)
    return _clean_text(text)


# ────────────────────────────────────────────
# テキスト後処理
# ────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """OCR 結果の不要な空行・文字を整理する。"""
    if not text:
        return ""
    # 連続する空行を1行に
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 行末の余分なスペース
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()
