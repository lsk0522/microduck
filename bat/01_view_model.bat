@echo off
chcp 65001 >nul
setlocal
title Microduck - 3D model viewer
call "%~dp0_env.bat" || (pause & exit /b 1)
set "XML="
echo ================================================
echo  MuJoCo 3D viewer
echo ================================================
echo  1  Original Microduck (standing scene)
echo  2  All-collisions model (every part)
echo  3  Roller skates model
echo  4  Walk model (training model)
echo  5  XL330 servo test bench
echo  6  Other scene XML (type a path)
echo.
set /p SEL=Select [1-6]: 
if "%SEL%"=="1" set "XML=cad\reference\microduck\scene.xml"
if "%SEL%"=="2" set "XML=cad\reference\microduck\scene_allcollisions.xml"
if "%SEL%"=="3" set "XML=cad\reference\microduck\scene_rollers.xml"
if "%SEL%"=="4" set "XML=cad\reference\microduck\scene_walk.xml"
if "%SEL%"=="5" set "XML=cad\reference\xl330_test_bench\scene.xml"
if "%SEL%"=="6" set /p XML=Path to scene XML: 
if not defined XML (
  echo Invalid selection.
  pause
  exit /b 1
)
echo Opening %XML% ...  (close the viewer window to return)
echo Tips: double-click a part to select, Ctrl+right-drag to push it, space = pause.
uv run python -m mujoco.viewer --mjcf="%XML%"
pause
