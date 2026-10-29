@echo off
chcp 65001 >nul
setlocal
title Microduck - plate DXF
call "%~dp0_env.bat" || (pause & exit /b 1)
echo ================================================
echo  Export aluminium plate outlines to DXF
echo ================================================
uv run python cad\tools\plates_to_dxf.py
if errorlevel 1 (pause & exit /b 1)
start "" "cad\plates\dynamixel"
pause
