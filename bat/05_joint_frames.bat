@echo off
chcp 65001 >nul
setlocal
title Microduck - joint frames
call "%~dp0_env.bat" || (pause & exit /b 1)
echo ================================================
echo  Extract joint positions / axes / link lengths
echo  (base dimensions for the Fusion skeleton)
echo ================================================
echo [1/3] Original size (Dynamixel track) ...
uv run python cad\tools\extract_joint_frames.py
if errorlevel 1 (pause & exit /b 1)
echo [2/3] 1.5x size (hobby servo track) ...
uv run python cad\tools\extract_joint_frames.py --scale 1.5 --out cad\hobby_servo\reference_1.5x
if errorlevel 1 (pause & exit /b 1)
echo [3/3] Copying Fusion parameter files ...
if not exist cad\fusion\params mkdir cad\fusion\params
copy /y cad\reference\fusion_params.csv cad\fusion\params\fusion_params_1x.csv >nul
copy /y cad\hobby_servo\reference_1.5x\fusion_params.csv cad\fusion\params\fusion_params_1.5x.csv >nul
uv run python cad\tools\parts_table.py
start "" "cad\fusion\params"
pause
