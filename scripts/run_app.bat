@echo off
chcp 65001 > nul
title BookVoice OCR Studio

echo ================================================
echo   BookVoice OCR Studio を起動しています...
echo ================================================
echo.

:: スクリプトのあるディレクトリの親（プロジェクトルート）へ移動
cd /d "%~dp0.."

:: Python の確認
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [エラー] Python が見つかりません。
    echo Python 3.11 以上をインストールしてください。
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 仮想環境の作成（初回のみ）
if not exist ".venv" (
    echo [1/3] 仮想環境を作成しています...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [エラー] 仮想環境の作成に失敗しました。
        pause
        exit /b 1
    )
)

:: 仮想環境を有効化
call .venv\Scripts\activate.bat

:: 依存パッケージのインストール（初回 or 更新時）
echo [2/3] 必要なパッケージを確認しています...
pip install -r requirements.txt -q --disable-pip-version-check
if %ERRORLEVEL% neq 0 (
    echo [エラー] パッケージのインストールに失敗しました。
    echo インターネット接続を確認してください。
    pause
    exit /b 1
)

:: .env ファイルのコピー（初回のみ）
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" > nul
        echo [情報] .env ファイルを作成しました。必要に応じて編集してください。
    )
)

:: データディレクトリの作成
if not exist "data\projects" mkdir "data\projects"
if not exist "data\mock_drive" mkdir "data\mock_drive"
if not exist "credentials" mkdir "credentials"

:: ブラウザで開く（サーバー起動後に自動オープン）
echo [3/3] アプリを起動しています...
echo.
echo ブラウザが自動で開きます。開かない場合は以下を開いてください:
echo   http://127.0.0.1:8000
echo.
echo 終了するには このウィンドウを閉じるか Ctrl+C を押してください。
echo ================================================

:: 少し待ってからブラウザを開く
start "" cmd /c "timeout /t 2 > nul && start http://127.0.0.1:8000"

:: FastAPI サーバーを起動
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
