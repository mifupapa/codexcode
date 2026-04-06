#!/usr/bin/env bash
# BookVoice OCR Studio — Linux/Mac 起動スクリプト
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "================================================"
echo "  BookVoice OCR Studio を起動しています..."
echo "================================================"

# 仮想環境の作成（初回のみ）
if [ ! -d ".venv" ]; then
    echo "[1/3] 仮想環境を作成しています..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "[2/3] 必要なパッケージを確認しています..."
pip install -r requirements.txt -q

# .env ファイルの初期化
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[情報] .env ファイルを作成しました。"
fi

mkdir -p data/projects data/mock_drive credentials

echo "[3/3] アプリを起動しています..."
echo ""
echo "ブラウザで http://127.0.0.1:8000 を開いてください"
echo "終了するには Ctrl+C を押してください"
echo "================================================"

# ブラウザを開く
(sleep 2 && python3 -c "import webbrowser; webbrowser.open('http://127.0.0.1:8000')") &

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
