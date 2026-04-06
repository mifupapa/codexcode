$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath  = Join-Path $ProjectRoot "scripts\run_app.bat"
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "BookVoice OCR Studio.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

$Shortcut.TargetPath       = "cmd.exe"
$Shortcut.Arguments        = "/c `"$ScriptPath`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description      = "BookVoice OCR Studio"
$Shortcut.WindowStyle      = 1
$IconPath = $env:SystemRoot + "\System32\shell32.dll,23"
$Shortcut.IconLocation     = $IconPath

$Shortcut.Save()

Write-Host "Shortcut created: $ShortcutPath" -ForegroundColor Green
