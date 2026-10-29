@echo off
chcp 65001 >nul
setlocal
title Microduck - build BOM
call "%~dp0_env.bat" || (pause & exit /b 1)
echo ================================================
echo  Rebuild BOM (bom\build_bom.py -> BOM.xlsx, BOM.csv)
echo ================================================
echo Close BOM.xlsx in Excel first, otherwise the file cannot be overwritten.
pause
uv run python bom\build_bom.py
if errorlevel 1 (
  echo [x] Failed. Is BOM.xlsx still open in Excel?
  pause
  exit /b 1
)
echo Opening BOM.xlsx (Excel recalculates the totals on open) ...
start "" "bom\BOM.xlsx"
pause
