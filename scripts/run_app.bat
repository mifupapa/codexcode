@echo off
title BookVoice OCR Studio

echo ================================================
echo   BookVoice OCR Studio - Starting...
echo ================================================
echo.

pushd "%~dp0.."
set "ROOT=%CD%"

:: Try to find Python (python, py launcher, or common install paths)
set "PYTHON="
python --version >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (
    py --version >nul 2>&1 && set "PYTHON=py"
)
if not defined PYTHON (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    )
)
if not defined PYTHON (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    )
)
if not defined PYTHON (
    if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    )
)
if not defined PYTHON (
    if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
        set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    )
)
if not defined PYTHON (
    if exist "C:\Python311\python.exe" set "PYTHON=C:\Python311\python.exe"
)
if not defined PYTHON (
    echo [ERROR] Python not found.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Check "Add Python to PATH" when installing.
    popd
    pause
    exit /b 1
)
echo [OK] Python found: %PYTHON%

:: Create venv if not exists
if not exist "%ROOT%\.venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    "%PYTHON%" -m venv "%ROOT%\.venv"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        popd
        pause
        exit /b 1
    )
)

:: Install packages
echo [2/3] Checking packages...
"%ROOT%\.venv\Scripts\pip.exe" install -r "%ROOT%\requirements.txt" -q --disable-pip-version-check
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install packages.
    popd
    pause
    exit /b 1
)

:: Create data dirs and .env
if not exist "%ROOT%\data\projects" mkdir "%ROOT%\data\projects"
if not exist "%ROOT%\data\mock_drive" mkdir "%ROOT%\data\mock_drive"
if not exist "%ROOT%\credentials" mkdir "%ROOT%\credentials"
if not exist "%ROOT%\.env" (
    if exist "%ROOT%\.env.example" copy "%ROOT%\.env.example" "%ROOT%\.env" >nul
)

echo [3/3] Starting server...
echo.
echo Open your browser at: http://127.0.0.1:8000
echo Close this window to stop the app.
echo ================================================

start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:8000"

cd /d "%ROOT%"
"%ROOT%\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

popd
pause
