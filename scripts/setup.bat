@echo off
chcp 65001 > nul
title BookVoice OCR Studio — 初回セットアップ

echo ================================================
echo   BookVoice OCR Studio セットアップ
echo ================================================
echo.

cd /d "%~dp0.."

:: デスクトップショートカット作成
echo [1/2] デスクトップにショートカットを作成しています...
powershell -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1"
if %ERRORLEVEL% neq 0 (
    echo [警告] ショートカットの作成に失敗しました。手動で run_app.bat を実行してください。
) else (
    echo [完了] ショートカットを作成しました。
)

echo.
echo [2/2] 仮想環境とパッケージをセットアップしています...
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q --disable-pip-version-check

echo.
echo ================================================
echo   セットアップ完了！
echo ================================================
echo.
echo デスクトップの「BookVoice OCR Studio」を
echo ダブルクリックするとアプリが起動します。
echo.
pause
