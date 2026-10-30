@echo off
chcp 65001 >nul
setlocal
title Microduck - assembly guide PDF
call "%~dp0_env.bat" || (pause & exit /b 1)
echo ================================================
echo  Rebuild the assembly guide PDF (docs\assembly)
echo ================================================
set /p RE=Re-scan holes and screws from the CAD meshes? Takes minutes [y/N]: 
if /i "%RE%"=="y" (
  uv run python docs\assembly\tools\find_holes.py cad\reference\microduck\assets docs\assembly\data\holes.json
  if errorlevel 1 (pause & exit /b 1)
  uv run python docs\assembly\tools\find_screws.py docs\assembly\data\holes.json docs\assembly\data\screws.json
  if errorlevel 1 (pause & exit /b 1)
)
echo [1/3] Rendering step images ...
uv run python docs\assembly\tools\render_steps.py docs\assembly\data\screws.json docs\assembly\img
if errorlevel 1 (pause & exit /b 1)
echo [2/3] Preparing PDF engine (first run downloads Chromium) ...
uv run --with playwright python -m playwright install chromium
echo [3/3] Building PDF ...
cd /d "%MD_ROOT%\docs\assembly"
uv run --project "%MD_ROOT%" --with playwright python tools\build_guide.py data\screws.json img Microduck_Assembly_Guide.pdf
if exist Microduck_Assembly_Guide.pdf (start "" Microduck_Assembly_Guide.pdf) else (start "" Microduck_Assembly_Guide.html)
pause
