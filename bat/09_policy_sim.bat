@echo off
chcp 65001 >nul
setlocal
title Microduck - drive a policy in simulation
cd /d "%~dp0.."
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo ================================================
echo  Drive a trained walking policy (.onnx) with the keyboard
echo  Uses external\microduck_rl  (run 08 first)
echo  EXPERIMENTAL on Windows: microduck_rl targets Linux + CUDA.
echo  If "uv sync" fails here, use Ubuntu or WSL2 instead.
echo ================================================
if not exist "external\microduck_rl\pyproject.toml" (
  echo [x] external\microduck_rl not found. Run 08_get_reference_repos.bat first.
  pause
  exit /b 1
)
set /p ONNX=Path to walking policy .onnx: 
if "%ONNX%"=="" (pause & exit /b 1)
for %%I in ("%ONNX%") do set "ONNX=%%~fI"
cd /d external\microduck_rl
uv sync
if errorlevel 1 (
  echo [x] Environment install failed on this machine. Use Ubuntu/WSL2.
  pause
  exit /b 1
)
uv run scripts/infer_policy.py --walking "%ONNX%"
pause
