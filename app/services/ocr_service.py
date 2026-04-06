"""OCR service.
Primary  : Google Cloud Vision API (best for vertical Japanese)
Fallback : pytesseract  (requires Tesseract installed)
"""
from __future__ import annotations
import os
import re
from pathlib import Path

# ──────────────────────────────────────────────
# Tesseract path auto-detection (Windows)
# ──────────────────────────────────────────────

_TESS_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

def _find_tesseract() -> str | None:
    # 1. env var override
    env = os.getenv("TESSERACT_CMD", "")
    if env:
        return env
    # 2. common Windows install paths
    for p in _TESS_CANDIDATES:
        if Path(p).exists():
            return p
    # 3. PATH
    import shutil
    return shutil.which("tesseract")


def run_ocr(image_path: str | Path, language: str = "ja") -> str:
    engine = os.getenv("OCR_ENGINE", "tesseract").lower()
    if engine == "vision":
        try:
            return _vision_ocr(image_path, language)
        except Exception as e:
            print(f"[OCR] Vision API failed, falling back to tesseract: {e}")
    return _tesseract_ocr(image_path, language)


# ──────────────────────────────────────────────
# Google Cloud Vision API
# ──────────────────────────────────────────────

def _vision_ocr(image_path: str | Path, language: str) -> str:
    from google.cloud import vision  # type: ignore

    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    image_context = vision.ImageContext(language_hints=[language])
    response = client.document_text_detection(image=image, image_context=image_context)

    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")

    return _clean_text(response.full_text_annotation.text)


# ──────────────────────────────────────────────
# Tesseract (offline fallback)
# ──────────────────────────────────────────────

def _tesseract_ocr(image_path: str | Path, language: str) -> str:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        raise RuntimeError(
            "pytesseract / Pillow not installed. Run: pip install pytesseract pillow"
        )

    # Set Tesseract path
    tess_path = _find_tesseract()
    if tess_path:
        pytesseract.pytesseract.tesseract_cmd = tess_path
    else:
        raise RuntimeError(
            "tesseract is not installed or it's not in your PATH. "
            "Run scripts/setup.bat to install it automatically, "
            "or download from https://github.com/UB-Mannheim/tesseract/wiki"
        )

    # Language mapping — prefer vertical Japanese
    lang_map = {
        "ja": "jpn_vert+jpn",
        "en": "eng",
        "zh": "chi_sim",
        "ko": "kor",
    }
    tess_lang = lang_map.get(language, "jpn_vert+jpn")

    # Check if jpn_vert data exists; fall back to jpn only
    tessdata_dir = Path(tess_path).parent / "tessdata"
    if not (tessdata_dir / "jpn_vert.traineddata").exists():
        tess_lang = "jpn"

    # PSM 5 = vertical block, PSM 6 = uniform block (try both)
    img = Image.open(image_path)

    # Try vertical layout first
    try:
        text = pytesseract.image_to_string(
            img, lang=tess_lang, config="--psm 5 --oem 1"
        )
        if text.strip():
            return _clean_text(text)
    except Exception:
        pass

    # Fallback: auto layout detection
    text = pytesseract.image_to_string(
        img, lang=tess_lang.split("+")[0], config="--psm 3 --oem 1"
    )
    return _clean_text(text)


# ──────────────────────────────────────────────
# Post-processing
# ──────────────────────────────────────────────

def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()
