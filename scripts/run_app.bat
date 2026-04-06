@echo off
title BookVoice OCR Studio

echo ================================================
echo   BookVoice OCR Studio - Starting...
echo ================================================
echo.

pushd "%~dp0.."
set "ROOT=%CD%"

:: Find Python
set "PYTHON="
python --version >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (py --version >nul 2>&1 && set "PYTHON=py")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python314\python.exe")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe")
if not defined PYTHON (
    echo [ERROR] Python not found.
    popd & pause & exit /b 1
)
echo [OK] Python found: %PYTHON%

:: Ensure venv exists
if not exist "%ROOT%\.venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    "%PYTHON%" -m venv "%ROOT%\.venv"
)

:: Install/update packages
echo [2/3] Checking packages...
"%ROOT%\.venv\Scripts\pip.exe" install -r "%ROOT%\requirements.txt" -q --disable-pip-version-check

:: Init dirs
if not exist "%ROOT%\data\projects" mkdir "%ROOT%\data\projects"
if not exist "%ROOT%\data\mock_drive" mkdir "%ROOT%\data\mock_drive"
if not exist "%ROOT%\credentials" mkdir "%ROOT%\credentials"
if not exist "%ROOT%\.env" (if exist "%ROOT%\.env.example" copy "%ROOT%\.env.example" "%ROOT%\.env" >nul)

:: Start via Python launcher (auto port detection)
echo [3/3] Starting server...
cd /d "%ROOT%"
"%ROOT%\.venv\Scripts\python.exe" "%ROOT%\scripts\start_server.py"

popd
pause
