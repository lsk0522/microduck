@echo off
chcp 65001 >nul
setlocal
title Microduck - reference repositories
cd /d "%~dp0.."
echo ================================================
echo  Download reference projects into external\
echo   - pollen-robotics/microduck_rl   (RL training)
echo   - pollen-robotics/microduck      (robot runtime)
echo   - apirrone/Open_Duck_Mini        (hobby-track leg design)
echo ================================================
where git >nul 2>nul
if errorlevel 1 (
  echo [x] git not found. Install Git for Windows: https://git-scm.com/download/win
  pause
  exit /b 1
)
if not exist external mkdir external
call :get microduck_rl https://github.com/pollen-robotics/microduck_rl develop
call :get microduck_runtime https://github.com/pollen-robotics/microduck main
call :get Open_Duck_Mini https://github.com/apirrone/Open_Duck_Mini v2
echo.
echo Done. Folder: %CD%\external
start "" "external"
pause
exit /b 0

:get
if exist "external\%1\.git" (
  echo [update] %1
  git -C "external\%1" pull --ff-only
) else (
  echo [clone ] %1
  git clone --depth 1 -b %3 %2 "external\%1"
  if errorlevel 1 git clone --depth 1 %2 "external\%1"
)
exit /b 0
