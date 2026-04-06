"""BookVoice OCR Studio — FastAPI メインアプリ"""
from __future__ import annotations
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.models import (
    DriveResult,
    OcrResult,
    Page,
    PageResponse,
    Project,
    ProjectCreate,
    ProjectResponse,
    TextUpdate,
    TtsResult,
)
from app.services import drive_service, ocr_service, project_service, tts_service

BASE_DIR = Path(__file__).parent
app = FastAPI(title="BookVoice OCR Studio", version="1.0.0")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


# ─────────────────────────────────────────────
# ページ
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# ─────────────────────────────────────────────
# プロジェクト CRUD
# ─────────────────────────────────────────────

@app.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate):
    project = Project(title=body.title, author=body.author, language=body.language)
    project_service.save(project)
    return _to_response(project)


@app.get("/projects", response_model=list[ProjectResponse])
async def list_projects():
    return [_to_response(p) for p in project_service.list_all()]


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    project = _get_or_404(project_id)
    return _to_response(project)


@app.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: str):
    if not project_service.delete(project_id):
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")


# ─────────────────────────────────────────────
# ページ管理
# ─────────────────────────────────────────────

@app.post("/projects/{project_id}/pages", response_model=PageResponse, status_code=201)
async def upload_page(project_id: str, file: UploadFile = File(...)):
    project = _get_or_404(project_id)

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"対応していないファイル形式です（対応: {', '.join(ALLOWED_IMAGE_EXTS)}）",
        )

    order = len(project.pages) + 1
    filename = f"{order:04d}{ext}"
    images_dir = project_service.images_dir(project_id)
    image_path = images_dir / filename

    content = await file.read()
    image_path.write_bytes(content)

    page = Page(order=order, image_path=str(image_path))
    project.pages.append(page)
    project_service.save(project)
    return _page_to_response(page)


@app.get("/projects/{project_id}/pages", response_model=list[PageResponse])
async def list_pages(project_id: str):
    project = _get_or_404(project_id)
    return [_page_to_response(p) for p in sorted(project.pages, key=lambda x: x.order)]


@app.get("/projects/{project_id}/pages/{page_id}", response_model=PageResponse)
async def get_page(project_id: str, page_id: str):
    project = _get_or_404(project_id)
    page = _page_or_404(project, page_id)
    return _page_to_response(page)


@app.patch("/projects/{project_id}/pages/{page_id}/text", response_model=PageResponse)
async def update_text(project_id: str, page_id: str, body: TextUpdate):
    """OCR テキストを手動編集する。"""
    project = _get_or_404(project_id)
    page = _page_or_404(project, page_id)
    page.ocr_text = body.ocr_text
    page.ocr_status = "done"
    project_service.update_page(project, page)
    return _page_to_response(page)


@app.delete("/projects/{project_id}/pages/{page_id}", status_code=204)
async def delete_page(project_id: str, page_id: str):
    project = _get_or_404(project_id)
    before = len(project.pages)
    project.pages = [p for p in project.pages if p.page_id != page_id]
    if len(project.pages) == before:
        raise HTTPException(status_code=404, detail="ページが見つかりません")
    # order を振り直す
    for i, p in enumerate(sorted(project.pages, key=lambda x: x.order), start=1):
        p.order = i
    project_service.save(project)


# ─────────────────────────────────────────────
# OCR
# ─────────────────────────────────────────────

@app.post("/projects/{project_id}/pages/{page_id}/ocr", response_model=OcrResult)
async def run_ocr(project_id: str, page_id: str):
    """1 ページ OCR を実行。失敗時も status=error で保存し再実行可能。"""
    project = _get_or_404(project_id)
    page = _page_or_404(project, page_id)

    page.ocr_status = "processing"
    project_service.update_page(project, page)

    try:
        text = ocr_service.run_ocr(page.image_path, project.language)
        page.ocr_text = text
        page.ocr_status = "done"
        page.error_message = None
    except Exception as e:
        page.ocr_status = "error"
        page.error_message = str(e)

    project_service.update_page(project, page)
    return OcrResult(
        page_id=page.page_id,
        ocr_text=page.ocr_text,
        ocr_status=page.ocr_status,
        error_message=page.error_message,
    )


@app.post("/projects/{project_id}/ocr/batch", response_model=list[OcrResult])
async def batch_ocr(project_id: str, retry_errors_only: bool = False):
    """全ページ（または error ページのみ）OCR を一括実行。"""
    project = _get_or_404(project_id)
    results = []
    for page in sorted(project.pages, key=lambda x: x.order):
        if retry_errors_only and page.ocr_status not in ("pending", "error"):
            continue
        page.ocr_status = "processing"
        project_service.update_page(project, page)
        try:
            text = ocr_service.run_ocr(page.image_path, project.language)
            page.ocr_text = text
            page.ocr_status = "done"
            page.error_message = None
        except Exception as e:
            page.ocr_status = "error"
            page.error_message = str(e)
        project_service.update_page(project, page)
        results.append(
            OcrResult(
                page_id=page.page_id,
                ocr_text=page.ocr_text,
                ocr_status=page.ocr_status,
                error_message=page.error_message,
            )
        )
    return results


# ─────────────────────────────────────────────
# TTS
# ─────────────────────────────────────────────

@app.post("/projects/{project_id}/pages/{page_id}/tts", response_model=TtsResult)
async def run_tts(project_id: str, page_id: str):
    """1 ページ TTS を実行。"""
    project = _get_or_404(project_id)
    page = _page_or_404(project, page_id)

    if not page.ocr_text.strip():
        raise HTTPException(status_code=400, detail="OCR テキストが空です。先に OCR を実行してください。")

    page.tts_status = "processing"
    project_service.update_page(project, page)

    audio_dir = project_service.audio_dir(project_id)
    mp3_path = audio_dir / f"{page.order:04d}.mp3"

    try:
        tts_service.run_tts(page.ocr_text, mp3_path, project.language)
        page.tts_path = str(mp3_path)
        page.tts_status = "done"
        page.error_message = None
    except Exception as e:
        page.tts_status = "error"
        page.error_message = str(e)

    project_service.update_page(project, page)
    return TtsResult(
        page_id=page.page_id,
        tts_path=page.tts_path,
        tts_status=page.tts_status,
        error_message=page.error_message,
    )


@app.post("/projects/{project_id}/tts/batch", response_model=list[TtsResult])
async def batch_tts(project_id: str, retry_errors_only: bool = False):
    """全ページ（または error ページのみ）TTS を一括実行。"""
    project = _get_or_404(project_id)
    audio_dir = project_service.audio_dir(project_id)
    results = []
    for page in sorted(project.pages, key=lambda x: x.order):
        if retry_errors_only and page.tts_status not in ("pending", "error"):
            continue
        if not page.ocr_text.strip():
            results.append(
                TtsResult(
                    page_id=page.page_id,
                    tts_path="",
                    tts_status="error",
                    error_message="OCR テキストが空のためスキップ",
                )
            )
            continue
        mp3_path = audio_dir / f"{page.order:04d}.mp3"
        page.tts_status = "processing"
        project_service.update_page(project, page)
        try:
            tts_service.run_tts(page.ocr_text, mp3_path, project.language)
            page.tts_path = str(mp3_path)
            page.tts_status = "done"
            page.error_message = None
        except Exception as e:
            page.tts_status = "error"
            page.error_message = str(e)
        project_service.update_page(project, page)
        results.append(
            TtsResult(
                page_id=page.page_id,
                tts_path=page.tts_path,
                tts_status=page.tts_status,
                error_message=page.error_message,
            )
        )
    return results


# ─────────────────────────────────────────────
# 画像ファイル配信（UI のサムネイル表示用）
# ─────────────────────────────────────────────

@app.get("/projects/{project_id}/pages/{page_id}/image")
async def get_page_image(project_id: str, page_id: str):
    project = _get_or_404(project_id)
    page = _page_or_404(project, page_id)
    img_path = Path(page.image_path)
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="画像ファイルが見つかりません")
    ext = img_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".bmp": "image/bmp", ".tif": "image/tiff", ".tiff": "image/tiff",
    }
    return FileResponse(path=str(img_path), media_type=media_type_map.get(ext, "image/jpeg"))


# ─────────────────────────────────────────────
# 音声ファイルダウンロード
# ─────────────────────────────────────────────

@app.get("/projects/{project_id}/pages/{page_id}/audio")
async def download_audio(project_id: str, page_id: str):
    project = _get_or_404(project_id)
    page = _page_or_404(project, page_id)
    if not page.tts_path or not Path(page.tts_path).exists():
        raise HTTPException(status_code=404, detail="音声ファイルが見つかりません。先に TTS を実行してください。")
    return FileResponse(
        path=page.tts_path,
        media_type="audio/mpeg",
        filename=f"{project.title}_{page.order:04d}.mp3",
    )


# ─────────────────────────────────────────────
# Google Drive 保存
# ─────────────────────────────────────────────

@app.post("/projects/{project_id}/pages/{page_id}/drive", response_model=DriveResult)
async def upload_to_drive(project_id: str, page_id: str):
    project = _get_or_404(project_id)
    page = _page_or_404(project, page_id)

    if not page.tts_path or not Path(page.tts_path).exists():
        raise HTTPException(status_code=400, detail="音声ファイルがありません。先に TTS を実行してください。")

    file_name = f"{project.title}_{page.order:04d}.mp3"
    try:
        file_id = drive_service.upload_mp3(page.tts_path, project.title, file_name)
        page.drive_file_id = file_id
        page.error_message = None
    except Exception as e:
        page.drive_file_id = None
        page.error_message = str(e)
        project_service.update_page(project, page)
        return DriveResult(
            page_id=page.page_id,
            drive_file_id=None,
            status="error",
            message=str(e),
        )

    project_service.update_page(project, page)
    is_mock = str(file_id).startswith("mock:")
    return DriveResult(
        page_id=page.page_id,
        drive_file_id=file_id,
        status="done",
        message="モック保存完了（Drive未設定）" if is_mock else "Drive にアップロード完了",
    )


@app.post("/projects/{project_id}/drive/batch", response_model=list[DriveResult])
async def batch_drive(project_id: str):
    """全完了ページの音声を Drive に一括アップロード。"""
    project = _get_or_404(project_id)
    results = []
    for page in sorted(project.pages, key=lambda x: x.order):
        if page.tts_status != "done" or not page.tts_path:
            continue
        file_name = f"{project.title}_{page.order:04d}.mp3"
        try:
            file_id = drive_service.upload_mp3(page.tts_path, project.title, file_name)
            page.drive_file_id = file_id
            project_service.update_page(project, page)
            is_mock = str(file_id).startswith("mock:")
            results.append(DriveResult(
                page_id=page.page_id,
                drive_file_id=file_id,
                status="done",
                message="モック保存" if is_mock else "Drive 保存完了",
            ))
        except Exception as e:
            results.append(DriveResult(
                page_id=page.page_id,
                drive_file_id=None,
                status="error",
                message=str(e),
            ))
    return results


# ─────────────────────────────────────────────
# Drive 設定状態確認
# ─────────────────────────────────────────────

@app.get("/drive/status")
async def drive_status():
    return {
        "configured": drive_service.is_configured(),
        "message": "Google Drive が設定済みです" if drive_service.is_configured()
                   else "Drive 未設定（モック保存モード）。credentials/client_secret.json を配置してください。",
    }


# ─────────────────────────────────────────────
# ヘルパー
# ─────────────────────────────────────────────

def _get_or_404(project_id: str) -> Project:
    p = project_service.load(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")
    return p


def _page_or_404(project: Project, page_id: str) -> Page:
    page = project_service.get_page(project, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="ページが見つかりません")
    return page


def _to_response(project: Project) -> ProjectResponse:
    done = sum(1 for p in project.pages if p.tts_status == "done")
    errors = sum(1 for p in project.pages if p.ocr_status == "error" or p.tts_status == "error")
    return ProjectResponse(
        project_id=project.project_id,
        title=project.title,
        author=project.author,
        language=project.language,
        created_at=project.created_at,
        page_count=len(project.pages),
        done_count=done,
        error_count=errors,
    )


def _page_to_response(page: Page) -> PageResponse:
    return PageResponse(
        page_id=page.page_id,
        order=page.order,
        ocr_text=page.ocr_text,
        ocr_status=page.ocr_status,
        tts_path=page.tts_path,
        tts_status=page.tts_status,
        drive_file_id=page.drive_file_id,
        error_message=page.error_message,
    )
