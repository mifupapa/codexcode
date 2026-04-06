@echo off
title BookVoice OCR Studio Setup

echo ================================================
echo   BookVoice OCR Studio - Setup
echo ================================================
echo.

pushd "%~dp0.."
set "ROOT=%CD%"
echo Root: %ROOT%
echo.

:: Try to find Python
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
    echo [ERROR] Python not found.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    popd
    pause
    exit /b 1
)
echo [OK] Python: %PYTHON%

:: Create venv
echo [1/3] Creating virtual environment...
if not exist "%ROOT%\.venv" (
    "%PYTHON%" -m venv "%ROOT%\.venv"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        popd
        pause
        exit /b 1
    )
)

:: Install packages
echo [2/3] Installing packages (this may take a few minutes)...
"%ROOT%\.venv\Scripts\pip.exe" install -r "%ROOT%\requirements.txt" --disable-pip-version-check
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install packages.
    popd
    pause
    exit /b 1
)

:: Desktop shortcut
echo [3/3] Creating desktop shortcut...
powershell -ExecutionPolicy Bypass -File "%ROOT%\scripts\create_shortcut.ps1"
if %ERRORLEVEL% neq 0 (
    echo [WARN] Shortcut creation failed. Use scripts\run_app.bat directly.
) else (
    echo [OK] Desktop shortcut created.
)

:: Init files
if not exist "%ROOT%\.env" (
    if exist "%ROOT%\.env.example" copy "%ROOT%\.env.example" "%ROOT%\.env" >nul
)
if not exist "%ROOT%\data\projects" mkdir "%ROOT%\data\projects"
if not exist "%ROOT%\data\mock_drive" mkdir "%ROOT%\data\mock_drive"
if not exist "%ROOT%\credentials" mkdir "%ROOT%\credentials"

echo.
echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo Double-click "BookVoice OCR Studio" on Desktop to start.
echo Or run: scripts\run_app.bat
echo.
popd
pause
