@echo off
chcp 65001 >nul
setlocal
title Microduck - update
cd /d "%~dp0.."
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo ================================================
echo  Update from GitHub (git pull) + refresh packages
echo ================================================
where git >nul 2>nul
if errorlevel 1 (
  echo [x] git not found. Install Git for Windows: https://git-scm.com/download/win
  pause
  exit /b 1
)
if not exist ".git" (
  echo [x] This folder is not a git clone. Re-run install_microduck_to_desktop.bat.
  pause
  exit /b 1
)
git status --short
echo.
echo Local changes shown above (if any) are kept. Pulling ...
git pull --ff-only
if errorlevel 1 (
  echo [x] Pull failed - you probably changed a file that was also changed on GitHub.
  echo     Commit or stash your changes, then try again.
  pause
  exit /b 1
)
where uv >nul 2>nul && uv sync
pause
