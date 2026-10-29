@echo off
chcp 65001 >nul
setlocal
title Microduck - render images
call "%~dp0_env.bat" || (pause & exit /b 1)
echo ================================================
echo  Render model images (iso / front / side)
echo ================================================
set "XML=cad\reference\microduck\scene_allcollisions.xml"
set /p X=Scene XML [Enter = original model]: 
if not "%X%"=="" set "XML=%X%"
if not exist renders mkdir renders
uv run python sim\render.py "%XML%" renders\model
if errorlevel 1 (pause & exit /b 1)
start "" "renders"
pause
