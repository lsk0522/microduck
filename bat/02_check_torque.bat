@echo off
chcp 65001 >nul
setlocal
title Microduck - mass and torque check
call "%~dp0_env.bat" || (pause & exit /b 1)
echo ================================================
echo  Mass / joint range / holding torque check
echo ================================================
echo  Servo:  1 XL330-M288 (Dynamixel)   2 MG996R   3 MG90S   4 SG90
set "SERVO=xl330"
set "VIN=7.4"
set /p S=Select servo [1-4, default 1]: 
if "%S%"=="2" (set "SERVO=mg996r" & set "VIN=6.0")
if "%S%"=="3" (set "SERVO=mg90s" & set "VIN=6.0")
if "%S%"=="4" (set "SERVO=sg90" & set "VIN=5.0")
set /p V=Supply voltage [default %VIN%]: 
if not "%V%"=="" set "VIN=%V%"
echo  Pose:  1 STAND   2 SIT   3 FOLD
set "KEY=STAND"
set /p K=Select pose [1-3, default 1]: 
if "%K%"=="2" set "KEY=SIT"
if "%K%"=="3" set "KEY=FOLD"
set "XML=cad\reference\microduck\scene_allcollisions.xml"
set /p X=Model XML [Enter = original model]: 
if not "%X%"=="" set "XML=%X%"
if not exist logs mkdir logs
set "LOG=logs\check_%SERVO%_%KEY%.txt"
uv run python sim\check_model.py "%XML%" --servo %SERVO% --vin %VIN% --key %KEY% > "%LOG%" 2>&1
type "%LOG%"
echo.
echo Saved to %LOG%
pause
