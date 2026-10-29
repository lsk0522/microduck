@echo off
chcp 65001 >nul
setlocal
title Microduck - train walking policy
cd /d "%~dp0.."
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
echo ================================================
echo  Train the walking policy (microduck_rl, PPO, MuJoCo Warp)
echo   1  Local GPU  (needs NVIDIA CUDA; Linux/WSL2 strongly recommended)
echo   2  Hugging Face Jobs (cloud GPU, paid; run "hf auth login" first)
echo ================================================
if not exist "external\microduck_rl\pyproject.toml" (
  echo [x] external\microduck_rl not found. Run 08_get_reference_repos.bat first.
  pause
  exit /b 1
)
set "TASK=Mjlab-Velocity-Flat-MicroDuck"
set /p T=Task [Enter = %TASK%]: 
if not "%T%"=="" set "TASK=%T%"
set "ENVS=4096"
set /p E=Parallel envs [Enter = 4096, use 2048 if GPU memory is low]: 
if not "%E%"=="" set "ENVS=%E%"
set "EXTRA="
set /p M=Mode [1 local / 2 HF Jobs, default 1]: 
if "%M%"=="2" set "EXTRA=--hf-jobs"
cd /d external\microduck_rl
uv sync
if errorlevel 1 (
  echo [x] Environment install failed on this machine. Use Ubuntu/WSL2, or mode 2.
  pause
  exit /b 1
)
echo Training %TASK% with %ENVS% envs %EXTRA% ...
uv run train %TASK% --env.scene.num-envs %ENVS% %EXTRA%
pause
