"""サービス単体テスト"""
import json
import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートを PATH に追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# テスト用に DATA_DIR を一時ディレクトリに向ける
_tmp = tempfile.mkdtemp()
os.environ["DATA_DIR"] = _tmp
os.environ["OCR_ENGINE"] = "tesseract"
os.environ["TTS_ENGINE"] = "gtts"

import pytest
from app.models import Page, Project
from app.services import project_service


# ─────────────────────────────────────────────
# project_service テスト
# ─────────────────────────────────────────────

def test_create_and_load_project():
    p = Project(title="テスト書籍", author="著者A", language="ja")
    project_service.save(p)
    loaded = project_service.load(p.project_id)
    assert loaded is not None
    assert loaded.title == "テスト書籍"
    assert loaded.author == "著者A"


def test_list_projects():
    p1 = Project(title="書籍1")
    p2 = Project(title="書籍2")
    project_service.save(p1)
    project_service.save(p2)
    all_projects = project_service.list_all()
    ids = [p.project_id for p in all_projects]
    assert p1.project_id in ids
    assert p2.project_id in ids


def test_update_page():
    p = Project(title="ページテスト")
    page = Page(order=1, image_path="/tmp/img.jpg")
    p.pages.append(page)
    project_service.save(p)

    page.ocr_text = "こんにちは"
    page.ocr_status = "done"
    project_service.update_page(p, page)

    loaded = project_service.load(p.project_id)
    assert loaded.pages[0].ocr_text == "こんにちは"
    assert loaded.pages[0].ocr_status == "done"


def test_delete_project():
    p = Project(title="削除テスト")
    project_service.save(p)
    assert project_service.load(p.project_id) is not None
    project_service.delete(p.project_id)
    assert project_service.load(p.project_id) is None


def test_load_nonexistent_returns_none():
    assert project_service.load("nonexistent-id-12345") is None


# ─────────────────────────────────────────────
# OCR テキスト後処理テスト
# ─────────────────────────────────────────────

def test_ocr_clean_text():
    from app.services.ocr_service import _clean_text

    raw = "こんにちは   \n\n\n\n世界\n"
    cleaned = _clean_text(raw)
    assert "こんにちは" in cleaned
    assert "世界" in cleaned
    assert "\n\n\n" not in cleaned


def test_ocr_clean_empty():
    from app.services.ocr_service import _clean_text
    assert _clean_text("") == ""
    assert _clean_text("   ") == ""


# ─────────────────────────────────────────────
# Drive サービス テスト（モック）
# ─────────────────────────────────────────────

def test_drive_mock_upload(tmp_path):
    from app.services import drive_service

    # client_secret.json がないので mock になる
    assert not drive_service.is_configured()

    mp3 = tmp_path / "test.mp3"
    mp3.write_bytes(b"fake mp3 content")

    file_id = drive_service.upload_mp3(str(mp3), "テスト書籍", "001.mp3")
    assert file_id.startswith("mock:")
