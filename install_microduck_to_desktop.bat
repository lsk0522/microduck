@echo off
chcp 65001 >nul
title Microduck - install to Desktop
setlocal
echo ==========================================================
echo  Install Microduck to  Desktop\Microduck
echo  Source: https://github.com/lsk0522/microduck
echo ==========================================================
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%D"
if not defined DESKTOP set "DESKTOP=%USERPROFILE%\Desktop"
set "TARGET=%DESKTOP%\Microduck"
echo Target: %TARGET%
echo.

if exist "%TARGET%\.git" (
  echo Already installed - updating instead.
  goto update
)
if exist "%TARGET%\" (
  dir /b "%TARGET%" | findstr "^" >nul && (
    echo [x] %TARGET% already exists and is not empty.
    echo     Rename or move it, then run this file again. Nothing was changed.
    pause
    exit /b 1
  )
)

set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
where git >nul 2>nul
if not errorlevel 1 goto clone

echo Git is not installed. Trying winget ...
where winget >nul 2>nul
if not errorlevel 1 (
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
)
where git >nul 2>nul
if not errorlevel 1 goto clone

echo Git still not available - downloading a ZIP instead (no "Update" support).
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $z=Join-Path $env:TEMP 'microduck-main.zip'; Invoke-WebRequest 'https://github.com/lsk0522/microduck/archive/refs/heads/main.zip' -OutFile $z; $t=Join-Path $env:TEMP 'microduck-unzip'; if(Test-Path $t){Remove-Item $t -Recurse -Force}; Expand-Archive $z $t; Move-Item (Join-Path $t 'microduck-main') $env:TARGET"
if errorlevel 1 (
  echo [x] Download failed. If the repository is private, install Git and run again.
  pause
  exit /b 1
)
goto setup

:clone
echo Cloning ...
git clone https://github.com/lsk0522/microduck "%TARGET%"
if errorlevel 1 (
  echo [x] git clone failed. If the repository is private, sign in when Git asks.
  pause
  exit /b 1
)
goto setup

:update
git -C "%TARGET%" pull --ff-only

:setup
echo.
echo Creating Desktop shortcut "Microduck" ...
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $env:DESKTOP 'Microduck - START.lnk')); $s.TargetPath=(Join-Path $env:TARGET 'START_HERE.bat'); $s.WorkingDirectory=$env:TARGET; $s.Save()"
call "%TARGET%\bat\00_setup.bat"
start "" "%TARGET%"
endlocal
