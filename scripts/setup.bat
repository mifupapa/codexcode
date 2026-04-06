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

:: --- Python detection ---
set "PYTHON="
python --version >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON (py --version >nul 2>&1 && set "PYTHON=py")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python314\python.exe")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe")
if not defined PYTHON (if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe")
if not defined PYTHON (
    echo [ERROR] Python not found. Install from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" when installing!
    popd & pause & exit /b 1
)
echo [OK] Python: %PYTHON%

:: --- Tesseract OCR installation ---
echo.
echo Checking Tesseract OCR...
set "TESS="
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" set "TESS=C:\Program Files\Tesseract-OCR\tesseract.exe"
if not defined TESS (if exist "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" set "TESS=C:\Program Files (x86)\Tesseract-OCR\tesseract.exe")

if defined TESS (
    echo [OK] Tesseract found: %TESS%
) else (
    echo [INFO] Installing Tesseract OCR via winget (Japanese support)...
    winget install -e --id UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% neq 0 (
        echo [WARN] winget install failed. Please install manually:
        echo   https://github.com/UB-Mannheim/tesseract/wiki
        echo   Choose "Additional language data" and check Japanese during install.
    ) else (
        echo [OK] Tesseract installed.
    )
)

:: --- Virtual environment ---
echo.
echo [1/3] Setting up virtual environment...
if not exist "%ROOT%\.venv" (
    "%PYTHON%" -m venv "%ROOT%\.venv"
    if %ERRORLEVEL% neq 0 (echo [ERROR] venv failed. & popd & pause & exit /b 1)
)

:: --- Install Python packages ---
echo [2/3] Installing Python packages (first time may take a few minutes)...
"%ROOT%\.venv\Scripts\pip.exe" install -r "%ROOT%\requirements.txt" --disable-pip-version-check
if %ERRORLEVEL% neq 0 (echo [ERROR] pip install failed. & popd & pause & exit /b 1)

:: --- Desktop shortcut ---
echo [3/3] Creating desktop shortcut...
powershell -ExecutionPolicy Bypass -File "%ROOT%\scripts\create_shortcut.ps1"
if %ERRORLEVEL% neq 0 (echo [WARN] Shortcut failed. Run scripts\run_app.bat manually.) else (echo [OK] Shortcut created.)

:: --- Init files ---
if not exist "%ROOT%\.env" (if exist "%ROOT%\.env.example" copy "%ROOT%\.env.example" "%ROOT%\.env" >nul)
if not exist "%ROOT%\data\projects" mkdir "%ROOT%\data\projects"
if not exist "%ROOT%\data\mock_drive" mkdir "%ROOT%\data\mock_drive"
if not exist "%ROOT%\credentials" mkdir "%ROOT%\credentials"

echo.
echo ================================================
echo   Setup Complete!
echo ================================================
echo Double-click "BookVoice OCR Studio" on Desktop to start.
echo.
popd
pause
