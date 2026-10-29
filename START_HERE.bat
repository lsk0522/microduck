@echo off
chcp 65001 >nul
title Microduck
cd /d "%~dp0"
:menu
cls
echo ==========================================================
echo                 MICRODUCK  -  main menu
echo ==========================================================
echo   0   Setup (first time)          - install uv + Python env
echo.
echo   1   View 3D model               - MuJoCo viewer
echo   2   Check mass / torque         - pick servo, voltage, pose
echo   3   Rebuild BOM and open Excel
echo   4   Export plate DXF            - aluminium parts
echo   5   Extract joint frames        - Fusion skeleton dimensions
echo   6   Render model images
echo.
echo   7   Update from GitHub
echo   8   Download reference repos    - microduck_rl, runtime, Open Duck Mini
echo   9   Drive policy in sim         - experimental on Windows
echo   10  Train walking policy        - Linux/WSL2 or HF Jobs
echo.
echo   D   Open docs (README)          G   Open GitHub page
echo   F   Open this folder            Q   Quit
echo ==========================================================
set "SEL="
set /p SEL=Select: 
if /i "%SEL%"=="Q" exit /b 0
if "%SEL%"=="0" call "bat\00_setup.bat"
if "%SEL%"=="1" call "bat\01_view_model.bat"
if "%SEL%"=="2" call "bat\02_check_torque.bat"
if "%SEL%"=="3" call "bat\03_build_bom.bat"
if "%SEL%"=="4" call "bat\04_plates_dxf.bat"
if "%SEL%"=="5" call "bat\05_joint_frames.bat"
if "%SEL%"=="6" call "bat\06_render_images.bat"
if "%SEL%"=="7" call "bat\07_update.bat"
if "%SEL%"=="8" call "bat\08_get_reference_repos.bat"
if "%SEL%"=="9" call "bat\09_policy_sim.bat"
if "%SEL%"=="10" call "bat\10_train_walk.bat"
if /i "%SEL%"=="D" start "" "https://github.com/lsk0522/microduck#readme"
if /i "%SEL%"=="G" start "" "https://github.com/lsk0522/microduck"
if /i "%SEL%"=="F" start "" "%~dp0"
cd /d "%~dp0"
goto menu
