@echo off
chcp 65001 >nul
setlocal
title Microduck - setup
cd /d "%~dp0.."
echo ================================================
echo  Microduck setup  (Python env + tools)
echo ================================================
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

where uv >nul 2>nul
if errorlevel 1 goto install_uv
goto have_uv

:install_uv
echo [1/3] Installing uv (Python package manager) ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo [x] uv install failed. See https://docs.astral.sh/uv/getting-started/installation/
  pause
  exit /b 1
)

:have_uv
echo [1/3] uv found.
echo [2/3] Creating Python environment (.venv). First run downloads Python + packages, a few minutes ...
uv sync
if errorlevel 1 (
  echo [x] uv sync failed. Check your internet connection and try again.
  pause
  exit /b 1
)
echo [3/3] Checking packages ...
uv run python -c "import mujoco, trimesh, ezdxf, openpyxl, shapely; print('mujoco', mujoco.__version__, '- all OK')"
if errorlevel 1 (
  echo [x] Package check failed.
  pause
  exit /b 1
)
echo.
echo Setup complete. Use START_HERE.bat for everything else.
pause
