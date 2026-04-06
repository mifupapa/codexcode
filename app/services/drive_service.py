"""Google Drive 連携サービス。
OAuth2 認証 → 書籍フォルダ作成 → MP3 アップロード。
credentials/client_secret.json が存在しない場合はモック動作。
"""
from __future__ import annotations
import os
import shutil
from pathlib import Path

CREDENTIALS_DIR = Path("credentials")
CLIENT_SECRET = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
MOCK_DRIVE_DIR = Path(os.getenv("DATA_DIR", "data")) / "mock_drive"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def is_configured() -> bool:
    return CLIENT_SECRET.exists()


def get_credentials():
    """OAuth2 トークンを取得（初回はブラウザ認証）。"""
    from google.oauth2.credentials import Credentials  # type: ignore
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    from google.auth.transport.requests import Request  # type: ignore

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        CREDENTIALS_DIR.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def get_or_create_folder(service, parent_id: str | None, folder_name: str) -> str:
    """指定フォルダ内に同名フォルダを検索し、なければ作成してIDを返す。"""
    query = (
        f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        " and trashed=false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    meta = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        meta["parents"] = [parent_id]

    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def upload_mp3(
    mp3_path: str | Path,
    book_title: str,
    file_name: str,
) -> str:
    """MP3 を Drive の BookVoice/{book_title}/ フォルダにアップロードしてファイルIDを返す。"""
    if not is_configured():
        return _mock_upload(mp3_path, book_title, file_name)

    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.http import MediaFileUpload  # type: ignore

    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    root_id = get_or_create_folder(service, None, "BookVoice")
    book_id = get_or_create_folder(service, root_id, book_title)

    media = MediaFileUpload(str(mp3_path), mimetype="audio/mpeg", resumable=True)
    file_meta = {"name": file_name, "parents": [book_id]}

    # 同名ファイルが存在する場合は上書き
    query = f"name='{file_name}' and '{book_id}' in parents and trashed=false"
    existing = service.files().list(q=query, fields="files(id)").execute().get("files", [])
    if existing:
        result = service.files().update(
            fileId=existing[0]["id"], media_body=media
        ).execute()
    else:
        result = service.files().create(
            body=file_meta, media_body=media, fields="id"
        ).execute()

    return result["id"]


def _mock_upload(mp3_path: str | Path, book_title: str, file_name: str) -> str:
    """Drive 未設定時のローカルモック保存。"""
    dest_dir = MOCK_DRIVE_DIR / "BookVoice" / book_title
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file_name
    shutil.copy2(str(mp3_path), str(dest))
    return f"mock:{dest}"
