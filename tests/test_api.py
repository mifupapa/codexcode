"""API 統合テスト（TestClient 使用）"""
import io
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

_tmp = tempfile.mkdtemp()
os.environ["DATA_DIR"] = _tmp
os.environ["OCR_ENGINE"] = "tesseract"
os.environ["TTS_ENGINE"] = "gtts"

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_project():
    res = client.post("/projects", json={"title": "APIテスト書籍", "author": "著者"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "APIテスト書籍"
    assert "project_id" in data


def test_list_projects():
    client.post("/projects", json={"title": "一覧テスト"})
    res = client.get("/projects")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_get_project_not_found():
    res = client.get("/projects/nonexistent-id")
    assert res.status_code == 404


def test_upload_page_invalid_file():
    proj = client.post("/projects", json={"title": "ページテスト"}).json()
    pid = proj["project_id"]

    # テキストファイルはエラー
    res = client.post(
        f"/projects/{pid}/pages",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400


def test_upload_page_valid_image(tmp_path):
    """PNG ダミーファイルでアップロードテスト"""
    from PIL import Image
    proj = client.post("/projects", json={"title": "画像テスト"}).json()
    pid = proj["project_id"]

    # 1x1 PNG を作成
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    res = client.post(
        f"/projects/{pid}/pages",
        files={"file": ("page001.png", buf, "image/png")},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["order"] == 1
    assert data["ocr_status"] == "pending"


def test_update_text():
    proj = client.post("/projects", json={"title": "テキスト更新テスト"}).json()
    pid = proj["project_id"]

    # ページを追加
    from PIL import Image
    img = Image.new("RGB", (10, 10))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    page = client.post(
        f"/projects/{pid}/pages",
        files={"file": ("p.png", buf, "image/png")},
    ).json()
    page_id = page["page_id"]

    # テキスト更新
    res = client.patch(
        f"/projects/{pid}/pages/{page_id}/text",
        json={"ocr_text": "手動編集したテキスト"},
    )
    assert res.status_code == 200
    assert res.json()["ocr_text"] == "手動編集したテキスト"
    assert res.json()["ocr_status"] == "done"


def test_drive_status():
    res = client.get("/drive/status")
    assert res.status_code == 200
    assert "configured" in res.json()


def test_delete_project():
    proj = client.post("/projects", json={"title": "削除テスト"}).json()
    pid = proj["project_id"]
    res = client.delete(f"/projects/{pid}")
    assert res.status_code == 204
    res2 = client.get(f"/projects/{pid}")
    assert res2.status_code == 404
