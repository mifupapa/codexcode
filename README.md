# 📖 BookVoice OCR Studio

書籍スキャン画像から **テキスト抽出（OCR）→ 音声合成（TTS）→ Google Drive 保存** をワンストップで行うアプリです。

---

## 🚀 かんたん起動（Windows）

### はじめて使うとき
1. このフォルダにある **`scripts\setup.bat`** をダブルクリック
2. 自動でセットアップ＋デスクトップにショートカットが作成されます

### 2回目以降
- デスクトップの **「BookVoice OCR Studio」** をダブルクリック
- ブラウザが自動で開いてアプリが使えます

> 終了するときは、黒いコマンドウィンドウを閉じてください

---

## 📋 必要なもの

| 必須 | バージョン | 入手先 |
|------|-----------|--------|
| Python | 3.11 以上 | https://www.python.org/downloads/ |

> **Python インストール時の注意:** 「Add Python to PATH」にチェックを入れてください

---

## 🎯 使い方（中学生でもわかるように）

### ステップ 1：プロジェクトを作る
1. 左側の「**＋ 新規**」ボタンをクリック
2. 書名（本のタイトル）を入力
3. 「作成」をクリック

### ステップ 2：画像をアップロードする
1. 中央の点線エリアに **スキャンした画像をドラッグ＆ドロップ**
   （JPG, PNG, TIFF などに対応）
2. 複数枚を一気にドロップできます

### ステップ 3：OCR でテキストを読み取る
1. 上の「**全ページ OCR**」ボタンをクリック
2. しばらく待つと、各ページのテキストが自動で読み取られます
3. 間違いがあれば、ページをクリックして右パネルで **手動修正** できます

### ステップ 4：音声を作る
1. 「**全ページ TTS**」ボタンをクリック
2. テキストが自動で音声（MP3）に変換されます

### ステップ 5：保存する
- 各ページの「**音声DL**」ボタンで MP3 をダウンロード
- Google Drive を設定していれば「**全て Drive 保存**」で自動アップロード

---

## ⚙️ 高品質 OCR の設定（任意）

デフォルトでは [gTTS](https://pypi.org/project/gTTS/)（無料）を使います。

### Google Cloud Vision API（縦書き日本語に最適）
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. Vision API を有効化
3. サービスアカウントキー（JSON）をダウンロード
4. `credentials/service_account.json` として配置
5. `.env` ファイルの `OCR_ENGINE=vision` を確認

### Google Drive 連携
1. Google Cloud Console で OAuth2 クライアント ID（デスクトップアプリ）を作成
2. `credentials/client_secret.json` として配置
3. 初回 Drive 保存時にブラウザで認証（1回だけ）
4. 以降は `BookVoice/{書名}/` フォルダに自動保存されます

---

## 🗂 フォルダ構成

```
codexcode/
├── app/
│   ├── main.py              # FastAPI サーバー
│   ├── models.py            # データモデル
│   ├── services/
│   │   ├── ocr_service.py   # OCR（Vision API / tesseract）
│   │   ├── tts_service.py   # TTS（gTTS / Cloud TTS）
│   │   ├── drive_service.py # Google Drive 連携
│   │   └── project_service.py # プロジェクト管理
│   ├── templates/index.html # UI
│   └── static/              # CSS/JS
├── data/
│   ├── projects/            # プロジェクトデータ（自動作成）
│   └── mock_drive/          # Drive 未設定時の保存先
├── credentials/             # API キー置き場（gitignore済み）
├── scripts/
│   ├── setup.bat            # 初回セットアップ（Windows）
│   ├── run_app.bat          # 起動スクリプト（Windows）
│   └── run_app.sh           # 起動スクリプト（Mac/Linux）
├── tests/                   # テスト
├── requirements.txt
└── .env                     # 設定ファイル（.env.exampleをコピー）
```

---

## 🛠 開発者向け

```bash
# テスト実行
cd codexcode
python -m pytest tests/ -v

# 手動起動
source .venv/Scripts/activate  # Windows
python -m uvicorn app.main:app --reload
```

---

## ❓ よくあるトラブル

| 症状 | 対処法 |
|------|--------|
| Python が見つかりません | Python をインストールし「Add to PATH」にチェック |
| ブラウザが開かない | `http://127.0.0.1:8000` を手動で開く |
| OCR が失敗する | `.env` の `OCR_ENGINE=tesseract` に変更、Tesseract をインストール |
| 音声生成が失敗する | インターネット接続を確認（gTTS はオンライン必須） |
| Drive 保存できない | `credentials/client_secret.json` を配置し認証を完了する |

---

## 📝 変更履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0.0 | 2026-04-06 | 初回リリース：OCR/TTS/Drive 全機能実装 |
