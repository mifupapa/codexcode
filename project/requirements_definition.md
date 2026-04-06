# BookVoice OCR Studio — 要件定義書

## 概要
書籍をスキャンした画像から OCR でテキストを抽出し、音声合成（TTS）で MP3 を生成、
Google Drive に自動保存するデスクトップ向け Web アプリ。

## ターゲットユーザー
- 非エンジニア（中高年含む）
- 書籍の音声化・電子化をしたい個人ユーザー

---

## MVP 必須機能

| # | 機能 | 優先度 | 完了条件 |
|---|------|--------|----------|
| 1 | プロジェクト作成（書名・著者・言語） | 最高 | POST /projects → project_id 返却 |
| 2 | 画像アップロード（複数枚対応） | 最高 | POST /projects/{id}/pages → page_id 返却 |
| 3 | OCR 実行（縦書き日本語対応） | 最高 | POST /projects/{id}/pages/{pid}/ocr → text 返却 |
| 4 | テキスト編集 UI | 高 | ブラウザ上でテキスト修正可能 |
| 5 | TTS 生成（MP3） | 高 | POST /projects/{id}/pages/{pid}/tts → mp3_path 返却 |
| 6 | 途中保存・再開 | 高 | サーバー再起動後も状態復元可 |
| 7 | エラーページのみ再実行 | 高 | status=error のページのみ再 OCR/TTS 可 |
| 8 | Google Drive 保存 | 中 | OAuth2 認証 → 書籍フォルダに MP3 アップロード |
| 9 | Windows ワンクリック起動 | 最高 | .bat ダブルクリックで起動 |

---

## 技術スタック

- **Backend**: Python 3.11+, FastAPI, uvicorn
- **OCR**: Google Cloud Vision API（主）/ pytesseract（フォールバック）
- **TTS**: gTTS（主）/ Google Cloud TTS（オプション）
- **Drive**: Google Drive API v3（OAuth2）
- **Storage**: JSON ファイル（プロジェクト状態）
- **Frontend**: Vanilla JS + HTML（依存ライブラリなし）

---

## データモデル

```json
{
  "project_id": "uuid",
  "title": "書名",
  "author": "著者",
  "language": "ja",
  "created_at": "2024-01-01T00:00:00",
  "pages": [
    {
      "page_id": "uuid",
      "order": 1,
      "image_path": "data/projects/{id}/images/001.jpg",
      "ocr_text": "...",
      "ocr_status": "done|error|pending",
      "tts_path": "data/projects/{id}/audio/001.mp3",
      "tts_status": "done|error|pending",
      "drive_file_id": null,
      "error_message": null
    }
  ]
}
```

---

## 非機能要件
- Windows 11 で動作すること
- Python 仮想環境（venv）を使用すること
- 起動は `.bat` ファイルのダブルクリックのみで完結すること
- エラーメッセージは日本語で表示すること
- オフライン時は pytesseract / gTTS でフォールバックすること
